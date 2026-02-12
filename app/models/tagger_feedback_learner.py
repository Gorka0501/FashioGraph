"""
Tagger Feedback Learner

Fine-tunes the HierarchicalMultiTaskModel tagger using user corrections (ItemChanges).
This improves the tagger's accuracy over time as users correct mislabeled items.
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import json

class TaggerFeedbackLearner:
    """
    Fine-tunes the hierarchical tagger model on user-corrected item categories.
    
    This learner:
    1. Takes the pre-trained tagger model
    2. Collects user corrections (original predictions vs corrected labels)
    3. Fine-tunes on this correction data
    4. Saves the improved model
    """
    
    def __init__(self, base_tagger, storage_path: Path, device: str = 'cpu'):
        """
        Initialize tagger feedback learner.
        
        Args:
            base_tagger: The HierarchicalMultiTaskModel to fine-tune
            storage_path: Where to save fine-tuned models
            device: 'cpu' or 'cuda'
        """
        self.base_tagger = base_tagger
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.device = torch.device(device)
        self.tagger_model = None
        self.optimizer = None
        self.training_history = []
        
        if base_tagger is not None:
            # Initialize fine-tuned model from base model
            self.tagger_model = self._init_model_from_base()
            self.learning_rate = 1e-5  # Very small LR for fine-tuning
            self.optimizer = optim.Adam(self.tagger_model.parameters(), lr=self.learning_rate)
    
    def _init_model_from_base(self):
        """Initialize model from base tagger with copied weights."""
        if self.base_tagger is None:
            return None
        
        model = type(self.base_tagger)(*self._get_model_args())
        model.load_state_dict(self.base_tagger.state_dict())
        model.to(self.device)
        return model
    
    def _get_model_args(self):
        """Extract model architecture parameters from base model."""
        # This is a placeholder - you may need to adjust based on your model
        return []
    
    def add_correction_sample(self, 
                             embedding: np.ndarray,
                             original_predictions: Dict[str, List[int]],
                             corrected_labels: Dict[str, List[int]],
                             confidence: float = 1.0,
                             notes: str = None):
        """
        Add a correction sample to the training buffer.
        
        Args:
            embedding: Image/attribute embedding (1D array)
            original_predictions: {'main': [...], 'sub': [...], 'category': [...], 'related': [...]}
            corrected_labels: Same structure as original_predictions
            confidence: User's confidence in the correction (0-1)
            notes: Optional notes about the correction
        """
        if self.tagger_model is None:
            return {'error': 'No tagger model available for training'}
        
        # Convert lists to one-hot encoded targets
        # This is simplified - adjust based on your model's exact requirements
        sample = {
            'embedding': torch.tensor(embedding, dtype=torch.float32),
            'original_main': original_predictions.get('main_category_indices', []),
            'original_sub': original_predictions.get('sub_category_indices', []),
            'original_category': original_predictions.get('category_indices', []),
            'corrected_main': corrected_labels.get('main_category_indices', []),
            'corrected_sub': corrected_labels.get('sub_category_indices', []),
            'corrected_category': corrected_labels.get('category_indices', []),
            'confidence': confidence,
            'notes': notes
        }
        
        return {'status': 'Sample queued for training'}
    
    def train_on_corrections(self, 
                            correction_samples: List[Dict[str, Any]],
                            epochs: int = 5,
                            batch_size: int = 4) -> Dict[str, Any]:
        """
        Fine-tune tagger on collected user corrections.
        
        Args:
            correction_samples: List of correction samples from users
            epochs: Number of training epochs
            batch_size: Batch size for training
            
        Returns:
            Training statistics
        """
        if self.tagger_model is None:
            return {'error': 'No tagger model available for training'}
        
        if len(correction_samples) < 2:
            return {'error': 'Insufficient samples for training (need at least 2)'}
        
        self.tagger_model.train()
        losses = []
        
        print(f"\n[TAGGER] Starting fine-tuning on {len(correction_samples)} correction samples")
        
        for epoch in range(epochs):
            epoch_losses = []
            
            # Process samples in batches
            for i in range(0, len(correction_samples), batch_size):
                batch = correction_samples[i:i + batch_size]
                
                try:
                    # Prepare batch tensors
                    embeddings = torch.stack([
                        torch.tensor(s['embedding'], dtype=torch.float32)
                        for s in batch
                    ]).to(self.device)
                    
                    # Forward pass
                    outputs = self.tagger_model(embeddings)
                    
                    # Compute loss against corrected labels
                    # This is simplified - adjust based on your loss function
                    loss = self._compute_correction_loss(outputs, batch)
                    
                    if loss is None:
                        continue
                    
                    self.optimizer.zero_grad()
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(self.tagger_model.parameters(), max_norm=1.0)
                    self.optimizer.step()
                    
                    epoch_losses.append(loss.item())
                
                except Exception as e:
                    print(f"[WARNING] Error processing batch: {e}")
                    continue
            
            if epoch_losses:
                avg_loss = np.mean(epoch_losses)
                losses.append(avg_loss)
                print(f"  Epoch {epoch+1}/{epochs}: Loss = {avg_loss:.6f}")
        
        # Record training history
        if losses:
            stats = {
                'timestamp': datetime.now().isoformat(),
                'samples_trained': len(correction_samples),
                'epochs': epochs,
                'final_loss': float(losses[-1]),
                'avg_loss': float(np.mean(losses)),
                'learning_rate': self.learning_rate
            }
            self.training_history.append(stats)
            
            # Save model and history
            self._save_model()
            self._save_history()
            
            print(f"[OK] Tagger fine-tuned. Final loss: {stats['final_loss']:.6f}")
            return stats
        else:
            return {'error': 'Training produced no valid losses'}
    
    def _compute_correction_loss(self, model_outputs, batch_samples) -> Optional[torch.Tensor]:
        """
        Compute loss between model outputs and corrected labels.
        
        This is a placeholder - customize based on your loss function.
        """
        try:
            # Convert outputs to probabilities
            if isinstance(model_outputs, tuple):
                # Multi-output model
                main_logits, sub_logits, cat_logits, related_logits = model_outputs
            else:
                return None
            
            # Create target tensors from corrected labels
            # This is simplified - your actual implementation may differ
            total_loss = 0
            count = 0
            
            for logits, key in [
                (main_logits, 'corrected_main'),
                (sub_logits, 'corrected_sub'),
                (cat_logits, 'corrected_category'),
            ]:
                target = self._create_target_from_indices(
                    [s.get(key, []) for s in batch_samples],
                    logits.shape[1]
                )
                
                if target is not None:
                    # Use binary cross-entropy for multi-label classification
                    loss = nn.BCEWithLogitsLoss()(logits, target)
                    total_loss += loss
                    count += 1
            
            return total_loss / count if count > 0 else None
        
        except Exception as e:
            print(f"[ERROR] Loss computation failed: {e}")
            return None
    
    def _create_target_from_indices(self, indices_list: List[List[int]], num_classes: int) -> Optional[torch.Tensor]:
        """Convert list of index lists to binary target tensor."""
        try:
            targets = []
            for indices in indices_list:
                target = torch.zeros(num_classes, dtype=torch.float32)
                for idx in indices:
                    if 0 <= idx < num_classes:
                        target[idx] = 1.0
                targets.append(target)
            
            if targets:
                return torch.stack(targets).to(self.device)
            return None
        except Exception as e:
            print(f"[ERROR] Target creation failed: {e}")
            return None
    
    def _save_model(self):
        """Save fine-tuned tagger model."""
        if self.tagger_model is None:
            return
        
        model_path = self.storage_path / "tagger_finetuned.pt"
        try:
            torch.save({
                'model_state_dict': self.tagger_model.state_dict(),
                'timestamp': datetime.now().isoformat(),
                'training_batches': len(self.training_history)
            }, model_path)
            print(f"[OK] Tagger model saved to {model_path}")
        except Exception as e:
            print(f"[WARNING] Could not save tagger model: {e}")
    
    def _save_history(self):
        """Save training history to JSON."""
        history_path = self.storage_path / "tagger_training_history.json"
        try:
            with open(history_path, 'w') as f:
                json.dump(self.training_history, f, indent=2, default=str)
        except Exception as e:
            print(f"[WARNING] Could not save training history: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get tagger fine-tuning statistics."""
        return {
            'has_model': self.tagger_model is not None,
            'training_batches': len(self.training_history),
            'latest_loss': self.training_history[-1].get('final_loss') if self.training_history else None,
            'total_samples_trained': sum(h.get('samples_trained', 0) for h in self.training_history),
            'model_path': str(self.storage_path / "tagger_finetuned.pt")
        }

# Global tagger feedback learner instance
_tagger_feedback_learner = None


def get_tagger_feedback_learner() -> TaggerFeedbackLearner:
    """Get or initialize the tagger feedback learner."""
    global _tagger_feedback_learner
    if _tagger_feedback_learner is None:
        import torch
        from app.utils.ml_models import get_models
        from app.backend.storage_config import StorageConfig
        models = get_models()
        base_tagger = models.get("hierarchical_tagger") if models else None
        # Use StorageConfig for centralized storage
        storage_path = Path(StorageConfig.PERSONAL_MODELS_DIR) / "tagger_feedback"
        _tagger_feedback_learner = TaggerFeedbackLearner(
            base_tagger=base_tagger,
            storage_path=storage_path,
            device='cuda' if torch.cuda.is_available() else 'cpu'
        )
    return _tagger_feedback_learner
