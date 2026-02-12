"""
User-Specific Reinforcement Learning for Outfit Preferences

Each user gets a personalized FULL HGNN model copy that learns from their outfit ratings.
The base model stays frozen, each user gets their own fine-tuned HGNN copy.
"""

import json
import threading
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import torch
import torch.nn as nn
from datetime import datetime
import copy
from app.backend.storage_config import StorageConfig


def copy_hgnn_model(base_model):
    """
    Create a deep copy of the base HGNN model.
    Used to initialize per-user models from the base model.
    
    Args:
        base_model: The base HGNN model to copy
        
    Returns:
        A new HGNN model with the same architecture and weights
    """
    if base_model is None:
        return None
    
    try:
        # Deep copy the model
        user_model = copy.deepcopy(base_model)
        return user_model
    except Exception as e:
        print(f"[WARNING] Could not copy HGNN model: {e}")
        return None


class UserPreferenceLearner:
    """
    Manages per-user HGNN model fine-tuning using reinforcement learning.
    
    Architecture:
    1. Base model: HGNN (shared across all users, FROZEN)
    2. User model: Full HGNN copy that gets fine-tuned on user ratings
       - Initialized with base model weights (transfer learning)
       - Fine-tuned on user's personal outfit ratings
       - Saved independently per-user
    3. Score: user_model(outfit) - direct personalized output
    
    Training:
    - When user rates an outfit (0-5 scale), collect rating
    - Loss: MSE between predicted score and actual user rating
    - Updates: Batch updates every N new ratings (default: 5)
    - Result: User gets personalized HGNN model from their data
    """
    
    def __init__(self, username: str, storage_path: Path = None, base_model=None):
        self.username = username
        # Use provided storage_path if available, otherwise use StorageConfig
        if storage_path:
            self.storage_path = Path(storage_path) / username
        else:
            # Fallback to StorageConfig for production use
            self.storage_path = Path(StorageConfig.get_user_personal_model_path(username))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # User's personalized HGNN model
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.user_model = None
        self.base_model_type = type(base_model).__name__ if base_model else None
        
        # Training configuration (set early, needed by _load_model)
        self.learning_rate = 0.0001  # Lower LR for fine-tuning
        self.loss_fn = nn.MSELoss()
        self.optimizer = None
        
        # Initialize user model from base model (transfer learning)
        if base_model is not None:
            self.user_model = copy_hgnn_model(base_model)
            if self.user_model:
                self.user_model = self.user_model.to(self.device)
                print(f"[OK] User {self.username}: Created personalized HGNN copy from base model")
            else:
                print(f"[WARNING] User {self.username}: Could not copy base model, will try to load from disk")
        else:
            print(f"[WARNING] User {self.username}: No base model provided")
        
        # Load existing model if available (will override if found)
        self._load_model()
        
        if self.user_model is None:
            print(f"[ERROR] User {self.username}: No model available (no base model and no saved model)")
        
        # Create optimizer after model is set
        if self.user_model:
            self.optimizer = torch.optim.Adam(self.user_model.parameters(), 
                                             lr=self.learning_rate)
        
        # Training data buffer
        self.ratings_buffer = []  # List of (outfit, user_score) tuples
        self.min_ratings_for_training = 10  # Min ratings before training (every 10 scores)
        
        # Statistics
        self.training_history = []
        self._load_history()
    
    def save_rating(self, outfit: torch.Tensor, user_score: float) -> None:
        """
        Save user's rating for an outfit.
        
        Args:
            outfit: torch tensor - outfit feature vector
            user_score: float between 0 and 1 - user's rating (normalized)
        """
        import logging
        logger = logging.getLogger("fashion_wardrobe_app")
        
        if isinstance(outfit, np.ndarray):
            outfit = torch.tensor(outfit, dtype=torch.float32)
        
        self.ratings_buffer.append((outfit.clone().detach(), float(user_score)))
        
        logger.debug(f"📊 User {self.username}: Rating saved. Buffer size: {len(self.ratings_buffer)}/{self.min_ratings_for_training}")
        
        # Auto-train if buffer is large enough (in background, non-blocking)
        if len(self.ratings_buffer) >= self.min_ratings_for_training:
            logger.info(f"🎯 User {self.username}: Buffer full ({len(self.ratings_buffer)} ratings), triggering auto-training")
            self._train_on_buffer_background()
    
    def _train_on_buffer_background(self) -> None:
        """
        Start background training on buffer (non-blocking).
        Launches training in a separate thread so API requests don't wait.
        """
        import logging
        logger = logging.getLogger("fashion_wardrobe_app")
        
        try:
            logger.info(f"🚀 Background training triggered for user {self.username} with {len(self.ratings_buffer)} ratings")
            
            # Create thread for background training
            train_thread = threading.Thread(
                target=self._background_train_wrapper,
                daemon=True,
                name=f"user_{self.username}_training"
            )
            train_thread.start()
            # Thread will continue in background without blocking
        except Exception as e:
            logger.error(f"❌ Failed to start background training for {self.username}: {e}", exc_info=True)
    
    def _background_train_wrapper(self) -> None:
        """Wrapper for background training that catches exceptions."""
        import logging
        logger = logging.getLogger("fashion_wardrobe_app")
        
        try:
            result = self.train_on_buffer()
            if 'error' in result:
                logger.warning(f"⚠️  Training error for {self.username}: {result['error']}")
            else:
                num_samples = result.get('num_samples', 0)
                avg_loss = result.get('avg_loss', 'N/A')
                logger.info(f"✅ Background training completed for {self.username}: {num_samples} samples, loss: {avg_loss}")
                logger.info(f"💾 Model and history saved to disk for user {self.username} (path: {self.storage_path / 'hgnn_model.pt'})")
        except Exception as e:
            logger.error(f"❌ Background training failed for {self.username}: {e}", exc_info=True)
    
    def train_on_buffer(self, epochs: int = 10) -> Dict[str, float]:
        """
        Fine-tune the user's HGNN model on collected ratings.
        
        Can be called directly or from background thread.
        
        Args:
            epochs: Number of training epochs
            
        Returns:
            Dictionary with training stats (loss, samples trained on, etc.)
        """
        if self.user_model is None:
            return {'error': 'No user model available'}
        
        if len(self.ratings_buffer) < 2:
            return {'error': 'Not enough ratings to train'}
        
        # Copy buffer before clearing (to avoid race conditions)
        buffer_copy = self.ratings_buffer.copy()
        
        # Prepare batch with padding to fixed size
        outfits = []
        scores = []
        total_features = 768  # clip (512) + attr (256)
        
        for outfit, score in buffer_copy:
            # Ensure outfit is 1D tensor
            if outfit.dim() > 1:
                outfit = outfit.squeeze()
            
            # Ensure outfit has the right size
            if outfit.shape[-1] < total_features:
                # Pad with zeros
                pad_size = total_features - outfit.shape[-1]
                outfit = torch.cat([outfit, torch.zeros(pad_size, device=outfit.device, dtype=outfit.dtype)])
            elif outfit.shape[-1] > total_features:
                # Truncate
                outfit = outfit[:total_features]
            
            outfits.append(outfit)
            scores.append(score)
        
        # Stack all outfits into a batch (shape: [batch_size, features])
        outfits = torch.stack(outfits, dim=0).to(self.device)
        scores = torch.tensor(scores, dtype=torch.float32).unsqueeze(1).to(self.device)
        
        # Extract batch size (number of outfits in training batch)
        batch_size = outfits.shape[0]
        
        # Build hypergraph structure for training
        # Each outfit is a single "super-node" connected via one hyperedge
        # So we have batch_size nodes, all connected to 1 hyperedge
        n_items = batch_size
        H_np = np.ones((n_items, 1), dtype=np.float32)  # All outfits in one hyperedge
        
        # Compute degree matrices
        Dv_np = np.sum(H_np, axis=1)  # (n_items,)
        Dv_np = np.maximum(Dv_np, 1e-8)
        Dv_inv_sqrt_np = np.diag(1.0 / np.sqrt(Dv_np))  # (n_items, n_items)
        
        De_np = np.sum(H_np, axis=0)  # (1,)
        De_np = np.maximum(De_np, 1e-8)
        De_inv_np = np.diag(1.0 / De_np)  # (1, 1)
        
        H = torch.from_numpy(H_np).to(self.device)
        Dv_inv_sqrt = torch.from_numpy(Dv_inv_sqrt_np).to(self.device)
        De_inv = torch.from_numpy(De_inv_np).to(self.device)
        
        # Outfit nodes and mask - one node per outfit in batch
        outfit_nodes = torch.arange(batch_size, dtype=torch.long, device=self.device)
        outfit_mask = torch.ones(batch_size, batch_size, dtype=torch.float32, device=self.device)
        
        # Training loop
        losses = []
        self.user_model.train()
        
        for epoch in range(epochs):
            self.optimizer.zero_grad()
            
            # Forward pass through user's HGNN model
            # The outfit tensor contains: clip (512 features) + attr (256 features)
            clip_dim = 512
            clip_feats_batch = outfits[:, :clip_dim]
            attr_feats_batch = outfits[:, clip_dim:clip_dim+256]
            
            # Call model with hypergraph parameters
            predictions = self.user_model(
                clip_feats_batch, 
                attr_feats_batch,
                H=H,
                Dv_inv_sqrt=Dv_inv_sqrt,
                De_inv=De_inv,
                outfit_nodes=outfit_nodes,
                outfit_mask=outfit_mask
            )
            
            # Handle different output formats
            if isinstance(predictions, tuple):
                # If model outputs multiple things, take first output
                predictions = predictions[0]
            
            # Ensure shape compatibility
            if predictions.shape != scores.shape:
                # If output doesn't match, try to extract score
                if len(predictions.shape) > 2:
                    predictions = predictions.mean(dim=1, keepdim=True)
                elif len(predictions.shape) == 1:
                    predictions = predictions.unsqueeze(1)
            
            loss = self.loss_fn(predictions, scores)
            
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.user_model.parameters(), max_norm=1.0)
            self.optimizer.step()
            
            losses.append(float(loss.item()))
        
        avg_loss = np.mean(losses)
        
        num_samples = len(buffer_copy)
        
        # Record training history
        stats = {
            'timestamp': datetime.now().isoformat(),
            'num_samples': num_samples,
            'avg_loss': avg_loss,
            'epochs': epochs,
            'learning_rate': self.learning_rate
        }
        self.training_history.append(stats)
        
        # Clear buffer after training
        self.ratings_buffer = []
        
        # Save the trained model and history to disk
        self._save_model()
        self._save_history()
        
        print(f"[OK] User {self.username}: Trained on {stats['num_samples']} ratings, loss: {avg_loss:.4f}")
        
        return stats
    
    def predict_user_score(self, outfit: torch.Tensor) -> float:
        """
        Predict user's preference score for an outfit using their fine-tuned model.
        
        Args:
            outfit: torch tensor - outfit feature vector
            
        Returns:
            Predicted user preference score (0-1)
        """
        if self.user_model is None:
            return 0.5  # Default score if no model
        
        if isinstance(outfit, np.ndarray):
            outfit = torch.tensor(outfit, dtype=torch.float32)
        
        self.user_model.eval()
        with torch.no_grad():
            outfit = outfit.unsqueeze(0).to(self.device)
            prediction = self.user_model(outfit)
            
            # Handle different output formats
            if isinstance(prediction, tuple):
                prediction = prediction[0]
            
            if len(prediction.shape) > 1:
                prediction = prediction.mean()
            
            score = float(prediction.item())
            # Clamp to 0-1 range
            score = max(0.0, min(1.0, score))
        
        return score
    
    def _save_model(self) -> None:
        """Save user's HGNN model to disk."""
        if self.user_model is None:
            return
        
        model_path = self.storage_path / "hgnn_model.pt"
        try:
            torch.save({
                'model_state_dict': self.user_model.state_dict(),
                'architecture': self.base_model_type,
                'username': self.username,
                'timestamp': datetime.now().isoformat(),
                'training_batches': len(self.training_history)
            }, model_path)
            print(f"[OK] User {self.username}: Model saved to {model_path}")
        except Exception as e:
            print(f"[WARNING] Could not save model for user {self.username}: {e}")
    
    def _load_model(self) -> None:
        """Load user's HGNN model from disk if available."""
        model_path = self.storage_path / "hgnn_model.pt"
        if model_path.exists():
            try:
                checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)
                
                # Load state dict into the model
                if self.user_model:
                    self.user_model.load_state_dict(checkpoint['model_state_dict'])
                    self.user_model = self.user_model.to(self.device)
                    print(f"[OK] User {self.username}: Loaded saved model from disk")
            except Exception as e:
                print(f"[WARNING] Could not load model for user {self.username}: {e}")
    
    def _save_history(self) -> None:
        """Save training history to JSON."""
        history_path = self.storage_path / "training_history.json"
        try:
            with open(history_path, 'w') as f:
                json.dump(self.training_history, f, indent=2)
        except Exception as e:
            print(f"[WARNING] Could not save history for user {self.username}: {e}")
    
    def _load_history(self) -> None:
        """Load training history from JSON."""
        history_path = self.storage_path / "training_history.json"
        if history_path.exists():
            try:
                with open(history_path, 'r') as f:
                    self.training_history = json.load(f)
            except Exception as e:
                print(f"[WARNING] Could not load history for user {self.username}: {e}")
    
    def delete_model(self) -> bool:
        """Delete user's personalized model and revert to base model."""
        try:
            # Delete model file
            model_path = self.storage_path / "hgnn_model.pt"
            if model_path.exists():
                model_path.unlink()
            
            # Delete history file
            history_path = self.storage_path / "training_history.json"
            if history_path.exists():
                history_path.unlink()
            
            # Reset in-memory state
            self.user_model = None
            self.ratings_buffer = []
            self.training_history = []
            
            print(f"[OK] User {self.username}: Personal model deleted, reverting to base model")
            return True
        except Exception as e:
            print(f"[ERROR] Could not delete model for user {self.username}: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """Get user's learning statistics."""
        return {
            'username': self.username,
            'has_model': self.user_model is not None,
            'num_ratings_in_buffer': len(self.ratings_buffer),
            'num_trained_batches': len(self.training_history),
            'total_ratings_trained_on': sum(h.get('num_samples', 0) 
                                           for h in self.training_history),
            'latest_avg_loss': self.training_history[-1].get('avg_loss', None) 
                              if self.training_history else None,
            'model_path': str(self.storage_path / "hgnn_model.pt"),
            'base_model_type': self.base_model_type
        }


class PreferenceLearnerManager:
    """
    Manages all user HGNN models.
    Each user gets their own fine-tuned copy of the base HGNN.
    Trains the base model collectively every 100 ratings.
    """
    
    def __init__(self, storage_path: Path, base_model=None):
        self.storage_path = Path(storage_path)
        self.learners = {}  # username -> UserPreferenceLearner
        self.base_model = base_model  # Shared base model for initialization
        self.global_rating_count = 0  # Track total ratings across all users
        self.base_model_ratings_buffer = []  # Collect ratings for base model training
        self.base_model_training_history = []  # Track base model training
        self._load_base_model_training_state()
    
    def _load_base_model_training_state(self) -> None:
        """Load base model training state from disk."""
        history_path = self.storage_path / "base_model_training_history.json"
        if history_path.exists():
            try:
                with open(history_path, 'r') as f:
                    data = json.load(f)
                    self.global_rating_count = data.get('global_rating_count', 0)
                    self.base_model_training_history = data.get('training_history', [])
                    print(f"[OK] Loaded base model training state: {self.global_rating_count} total ratings")
            except Exception as e:
                print(f"[WARNING] Could not load base model training state: {e}")
    
    def _save_base_model_training_state(self) -> None:
        """Save base model training state to disk."""
        state_path = self.storage_path / "base_model_training_history.json"
        try:
            with open(state_path, 'w') as f:
                json.dump({
                    'global_rating_count': self.global_rating_count,
                    'training_history': self.base_model_training_history,
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            print(f"[WARNING] Could not save base model training state: {e}")
    
    def get_learner(self, username: str) -> UserPreferenceLearner:
        """Get or create a learner (HGNN copy) for a user."""
        if username not in self.learners:
            self.learners[username] = UserPreferenceLearner(
                username, 
                self.storage_path,
                base_model=self.base_model
            )
        return self.learners[username]
    
    def save_outfit_rating(self, username: str, outfit: torch.Tensor, 
                          user_score: float) -> None:
        """Save user's rating for an outfit."""
        learner = self.get_learner(username)
        learner.save_rating(outfit, user_score)
        
        # Track for base model training
        self.global_rating_count += 1
        self.base_model_ratings_buffer.append({
            'username': username,
            'outfit': outfit.cpu().detach().clone(),
            'score': user_score
        })
        
        # Train base model every 100 ratings
        if self.global_rating_count % 100 == 0:
            self._train_base_model()
    
    def _train_base_model(self) -> None:
        """Train the base HGNN model on collected ratings from all users."""
        if self.base_model is None or len(self.base_model_ratings_buffer) == 0:
            print("[WARNING] Cannot train base model: model or buffer is empty")
            return
        
        import logging
        logger = logging.getLogger("app.models.preference_learner")
        
        logger.info(f"🎯 Base Model Training: Starting training on {len(self.base_model_ratings_buffer)} ratings from all users")
        
        try:
            device = next(self.base_model.parameters()).device
            optimizer = torch.optim.AdamW(self.base_model.parameters(), lr=1e-5, weight_decay=1e-5)
            criterion = torch.nn.MSELoss()
            
            # Training loop
            num_epochs = 3
            total_loss = 0
            sample_count = 0
            
            for epoch in range(num_epochs):
                epoch_loss = 0
                for rating_data in self.base_model_ratings_buffer:
                    outfit = rating_data['outfit'].to(device)
                    target_score = torch.tensor([rating_data['score']], dtype=torch.float32, device=device)
                    
                    # Forward pass
                    prediction = self.base_model(outfit.unsqueeze(0))
                    
                    # Handle different prediction shapes
                    if isinstance(prediction, tuple):
                        prediction = prediction[0]
                    if len(prediction.shape) > 1:
                        prediction = prediction.mean()
                    
                    # Compute loss
                    loss = criterion(prediction.unsqueeze(0), target_score)
                    
                    # Backward pass
                    optimizer.zero_grad()
                    loss.backward()
                    optimizer.step()
                    
                    epoch_loss += loss.item()
                    sample_count += 1
                
                avg_epoch_loss = epoch_loss / len(self.base_model_ratings_buffer)
                total_loss += avg_epoch_loss
                logger.debug(f"  Epoch {epoch+1}/{num_epochs}: avg_loss = {avg_epoch_loss:.4f}")
            
            avg_loss = total_loss / num_epochs
            
            # Record training
            self.base_model_training_history.append({
                'global_ratings': self.global_rating_count,
                'num_samples': len(self.base_model_ratings_buffer),
                'avg_loss': avg_loss,
                'timestamp': datetime.now().isoformat()
            })
            
            # Save base model state
            base_model_path = self.storage_path / "base_model_finetuned.pt"
            torch.save({
                'model_state_dict': self.base_model.state_dict(),
                'global_ratings': self.global_rating_count,
                'timestamp': datetime.now().isoformat()
            }, base_model_path)
            
            # Clear buffer and save state
            self.base_model_ratings_buffer.clear()
            self._save_base_model_training_state()
            
            logger.info(f"✨ Base Model Training Complete: Loss = {avg_loss:.4f}, Saved to {base_model_path}")
        
        except Exception as e:
            logger.error(f"[ERROR] Base model training failed: {e}", exc_info=True)
    
    def predict_user_preference(self, username: str, outfit: torch.Tensor) -> float:
        """Predict user's preference for an outfit using their personalized model."""
        learner = self.get_learner(username)
        return learner.predict_user_score(outfit)
    
    def get_user_model_score(self, user_id: int, outfit: torch.Tensor) -> float:
        """
        Get outfit score from user's personalized HGNN model.
        This is the direct output of the user's fine-tuned model.
        """
        return self.predict_user_preference(user_id, outfit)
    
    def get_learner_stats(self, username: str) -> Dict:
        """Get statistics for a user's model."""
        learner = self.get_learner(username)
        return learner.get_stats()
    
    def delete_user_model(self, username: str) -> bool:
        """Delete a user's personalized model, reverting them to the base model."""
        if username not in self.learners:
            print(f"[WARNING] User {username} has no learner to delete")
            return False
        
        learner = self.learners[username]
        success = learner.delete_model()
        
        if success:
            # Recreate learner for future use (will use base model)
            self.learners[username] = UserPreferenceLearner(
                username,
                self.storage_path,
                base_model=self.base_model
            )
        
        return success
    
    def reset_personal_model(self, username: str) -> Tuple[bool, str]:
        """
        Reset user's personal model back to base model (clear all learned preferences).
        Removes saved model and training history from disk.
        """
        import logging
        logger = logging.getLogger("app.models.preference_learner")
        
        if self.base_model is None:
            return False, "Base model is not available"
        
        try:
            # Remove saved model and history from disk
            user_model_dir = self.storage_path / username
            if user_model_dir.exists():
                import shutil
                shutil.rmtree(user_model_dir)
                logger.info(f"✓ Removed saved model and history for user {username}")
            
            # Create fresh personal model from base (overwrite in-memory)
            fresh_learner = UserPreferenceLearner(
                username,
                self.storage_path,
                base_model=self.base_model
            )
            
            # Replace learner with fresh one
            self.learners[username] = fresh_learner
            
            logger.info(f"✨ Personal model reset for user {username} back to base model")
            return True, "Personal model reset successfully to base model"
        
        except Exception as e:
            logger.error(f"[ERROR] Failed to reset personal model for {username}: {e}", exc_info=True)
            return False, f"Error during reset: {str(e)}"
    
    def retrain_personal_model_from_base(self, username: str) -> Tuple[bool, str]:
        """
        Retrain user's personal model from scratch using base model and all historical user ratings.
        Loads all user outfits with ratings and trains the fresh model on them.
        """
        import logging
        logger = logging.getLogger("app.models.preference_learner")
        
        if self.base_model is None:
            return False, "Base model is not available"
        
        try:
            from app.backend.database import SessionLocal, User, Outfit
            import shutil
            
            # Get database session
            db = SessionLocal()
            
            # Find user by username
            user = db.query(User).filter(User.username == username).first()
            if not user:
                db.close()
                return False, f"User {username} not found in database"
            
            # Delete existing saved model and history before retraining
            user_model_dir = Path(StorageConfig.get_user_personal_model_path(username))
            if user_model_dir.exists():
                shutil.rmtree(user_model_dir)
                logger.info(f"🗑️  Deleted existing model directory for user {username}")
            
            # Get all outfits with ratings for this user
            outfits_with_ratings = db.query(Outfit).filter(
                (Outfit.user_id == user.id) & 
                ((Outfit.user_rating.isnot(None)) | (Outfit.system_rating.isnot(None)))
            ).all()
            
            db.close()
            
            if not outfits_with_ratings:
                logger.info(f"⚠️  No rated outfits found for user {username}, creating fresh model from base")
                # Create fresh personal model from base
                fresh_learner = UserPreferenceLearner(
                    username,
                    self.storage_path,
                    base_model=self.base_model
                )
                self.learners[username] = fresh_learner
                fresh_learner._save_model()
                fresh_learner._save_history()
                return True, "Personal model retrained from base model (no historical ratings found)"
            
            # Create fresh personal model from base
            fresh_learner = UserPreferenceLearner(
                username,
                self.storage_path,
                base_model=self.base_model
            )
            
            # Clear training history for fresh retrain
            fresh_learner.training_history = []
            
            logger.info(f"🔄 Retraining personal model for user {username} with {len(outfits_with_ratings)} historical ratings")
            
            # Add all outfit ratings to the buffer for training
            # Directly add to buffer WITHOUT triggering auto-training
            for outfit in outfits_with_ratings:
                # Use user_rating if available, otherwise system_rating
                # Ratings are already stored as 0-1 in the database
                rating = outfit.user_rating if outfit.user_rating is not None else outfit.system_rating
                
                # Create outfit feature vector from items
                # For now, use a placeholder - in production, reconstruct from item embeddings
                outfit_features = torch.zeros(768, dtype=torch.float32)  # 512 clip + 256 attr
                
                # Add directly to buffer without triggering auto-training
                fresh_learner.ratings_buffer.append((outfit_features.clone().detach(), float(rating)))
            
            # Train the model once on ALL collected ratings
            if len(fresh_learner.ratings_buffer) > 0:
                train_stats = fresh_learner.train_on_buffer(epochs=5)
                num_samples = train_stats.get('num_samples', len(outfits_with_ratings))
            else:
                num_samples = 0
            
            # Replace learner with fresh trained one
            self.learners[username] = fresh_learner
            
            # Save the trained model to disk
            fresh_learner._save_model()
            fresh_learner._save_history()
            
            logger.info(f"✨ Personal model retrained for user {username} from base model with {num_samples} ratings (saved to disk)")
            return True, f"Personal model retrained successfully with {num_samples} historical ratings"
        
        except Exception as e:
            logger.error(f"[ERROR] Failed to retrain personal model for {username}: {e}", exc_info=True)
            return False, f"Error during retraining: {str(e)}"
    
    def get_base_model_stats(self) -> Dict:
        """Get statistics for the base model."""
        return {
            'global_rating_count': self.global_rating_count,
            'num_training_batches': len(self.base_model_training_history),
            'ratings_in_current_buffer': len(self.base_model_ratings_buffer),
            'latest_avg_loss': self.base_model_training_history[-1].get('avg_loss', None)
                              if self.base_model_training_history else None,
            'training_history': self.base_model_training_history
        }


# Global preference learner manager instance
_preference_learner_manager = None


def get_preference_learner_manager() -> PreferenceLearnerManager:
    """Get or initialize the preference learner manager."""
    global _preference_learner_manager
    if _preference_learner_manager is None:
        from app.utils.ml_models import get_models
        models = get_models()
        base_hgnn = models.get("fashion_hypergraph") if models else None
        # Use StorageConfig for centralized storage
        storage_path = Path(StorageConfig.PERSONAL_MODELS_DIR)
        _preference_learner_manager = PreferenceLearnerManager(
            storage_path=storage_path,
            base_model=base_hgnn
        )
    return _preference_learner_manager
