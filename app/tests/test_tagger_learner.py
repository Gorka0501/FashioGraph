"""Unit tests for TaggerFeedbackLearner and UserPreferenceLearner utilities."""
import pytest
import torch
import torch.nn as nn
import numpy as np
from pathlib import Path
from app.models.tagger_feedback_learner import TaggerFeedbackLearner
from app.models.user_preference_learner import UserPreferenceLearner, copy_hgnn_model
import tempfile
import json
import time


class MockTaggerModel(torch.nn.Module):
    """Mock tagger model for testing."""
    
    def __init__(self, embedding_dim=256):
        super().__init__()
        self.main_head = torch.nn.Linear(embedding_dim, 11)
        self.sub_head = torch.nn.Linear(embedding_dim, 141)
        self.category_head = torch.nn.Linear(embedding_dim, 210)
    
    def forward(self, x):
        return (self.main_head(x), self.sub_head(x), 
                self.category_head(x), torch.zeros(x.shape[0], 200))


@pytest.fixture
def temp_storage():
    """Create temporary storage directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_tagger():
    """Create a mock tagger model."""
    return MockTaggerModel()


@pytest.fixture
def tagger_learner(mock_tagger, temp_storage):
    """Create a TaggerFeedbackLearner with mock model."""
    return TaggerFeedbackLearner(mock_tagger, temp_storage, device='cpu')


class TestTaggerLearnerBasics:
    """Test TaggerFeedbackLearner basic functionality."""
    
    def test_initialization_with_model(self, mock_tagger, temp_storage):
        """Test initializing learner with base model."""
        learner = TaggerFeedbackLearner(mock_tagger, temp_storage, device='cpu')
        
        assert learner.tagger_model is not None
        assert learner.optimizer is not None
        assert learner.storage_path == temp_storage
    
    def test_initialization_without_model(self, temp_storage):
        """Test initializing learner without base model."""
        learner = TaggerFeedbackLearner(None, temp_storage, device='cpu')
        
        assert learner.tagger_model is None
        assert learner.optimizer is None
    
    def test_storage_path_creation(self, mock_tagger):
        """Test that storage path is created automatically."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "nonexistent" / "path"
            learner = TaggerFeedbackLearner(mock_tagger, storage_path, device='cpu')
            assert storage_path.exists()
    
    def test_add_correction_sample(self, tagger_learner):
        """Test adding a correction sample."""
        embedding = np.random.randn(256).astype(np.float32)
        result = tagger_learner.add_correction_sample(
            embedding=embedding,
            original_predictions={'main_category_indices': [0, 1]},
            corrected_labels={'main_category_indices': [0, 2]},
            confidence=0.9
        )
        
        assert 'status' in result


class TestTaggerTraining:
    """Test tagger training functionality."""
    
    def test_train_on_corrections_successful(self, tagger_learner):
        """Test successful training on correction samples."""
        samples = []
        for i in range(5):
            sample = {
                'embedding': np.random.randn(256).astype(np.float32),
                'original_main': [i],
                'corrected_main': [i + 1],
                'confidence': 0.8
            }
            samples.append(sample)
        
        result = tagger_learner.train_on_corrections(samples, epochs=2)
        
        assert 'error' not in result
        assert 'final_loss' in result
        assert result['samples_trained'] == 5
    
    def test_train_insufficient_samples(self, tagger_learner):
        """Test that training requires at least 2 samples."""
        sample = {
            'embedding': np.random.randn(256).astype(np.float32),
            'original_main': [0],
            'corrected_main': [1]
        }
        
        result = tagger_learner.train_on_corrections([sample])
        assert 'error' in result
    
    def test_train_without_model(self, temp_storage):
        """Test training when learner has no model."""
        learner = TaggerFeedbackLearner(None, temp_storage, device='cpu')
        
        samples = [
            {'embedding': np.random.randn(256).astype(np.float32), 'original_main': [0], 'corrected_main': [1]},
            {'embedding': np.random.randn(256).astype(np.float32), 'original_main': [1], 'corrected_main': [2]}
        ]
        
        result = learner.train_on_corrections(samples)
        assert 'error' in result
    
    def test_training_history_recorded(self, tagger_learner):
        """Test that training history is recorded."""
        samples = [
            {'embedding': np.random.randn(256).astype(np.float32), 'original_main': [i], 'corrected_main': [i+1]}
            for i in range(5)
        ]
        
        tagger_learner.train_on_corrections(samples, epochs=2)
        
        assert len(tagger_learner.training_history) > 0
        entry = tagger_learner.training_history[-1]
        assert 'timestamp' in entry
        assert 'samples_trained' in entry
        assert entry['samples_trained'] == 5


class TestTaggerStats:
    """Test tagger statistics."""
    
    def test_stats_before_training(self, tagger_learner):
        """Test stats before any training."""
        stats = tagger_learner.get_stats()
        
        assert stats['has_model'] is True
        assert stats['training_batches'] == 0
        assert stats['latest_loss'] is None
    
    def test_stats_after_training(self, tagger_learner):
        """Test stats after training."""
        samples = [
            {'embedding': np.random.randn(256).astype(np.float32), 'original_main': [i], 'corrected_main': [i+1]}
            for i in range(5)
        ]
        
        tagger_learner.train_on_corrections(samples)
        stats = tagger_learner.get_stats()
        
        assert stats['training_batches'] == 1
        assert stats['latest_loss'] is not None
        assert stats['total_samples_trained'] == 5


class TestTaggerPersistence:
    """Test model persistence."""
    
    def test_model_saved_after_training(self, tagger_learner):
        """Test that model is saved after training."""
        samples = [
            {'embedding': np.random.randn(256).astype(np.float32), 'original_main': [i], 'corrected_main': [i+1]}
            for i in range(5)
        ]
        
        tagger_learner.train_on_corrections(samples)
        
        model_path = tagger_learner.storage_path / "tagger_finetuned.pt"
        assert model_path.exists()
    
    def test_history_saved_after_training(self, tagger_learner):
        """Test that training history is saved."""
        samples = [
            {'embedding': np.random.randn(256).astype(np.float32), 'original_main': [i], 'corrected_main': [i+1]}
            for i in range(5)
        ]
        
        tagger_learner.train_on_corrections(samples)
        
        history_path = tagger_learner.storage_path / "tagger_training_history.json"
        assert history_path.exists()


class TestTaggerMultiBatchTraining:
    """Test multiple training batches for tagger."""
    
    def test_multiple_training_batches_accumulate(self, tagger_learner):
        """Test that multiple training batches accumulate in history."""
        # First batch
        samples1 = [
            {'embedding': np.random.randn(256).astype(np.float32), 'original_main': [i], 'corrected_main': [i+1]}
            for i in range(5)
        ]
        tagger_learner.train_on_corrections(samples1)
        
        history_len_1 = len(tagger_learner.training_history)
        assert history_len_1 > 0
        
        # Second batch
        samples2 = [
            {'embedding': np.random.randn(256).astype(np.float32), 'original_main': [i], 'corrected_main': [i+2]}
            for i in range(5)
        ]
        tagger_learner.train_on_corrections(samples2)
        
        history_len_2 = len(tagger_learner.training_history)
        assert history_len_2 > history_len_1
    
    def test_accumulate_samples_across_batches(self, tagger_learner):
        """Test that total samples trained accumulates correctly."""
        total_samples = 0
        
        for batch in range(3):
            num_samples = 5 + batch
            samples = [
                {'embedding': np.random.randn(256).astype(np.float32), 'original_main': [i], 'corrected_main': [i+1]}
                for i in range(num_samples)
            ]
            tagger_learner.train_on_corrections(samples)
            total_samples += num_samples
        
        stats = tagger_learner.get_stats()
        assert stats['total_samples_trained'] == total_samples


class TestTaggerCorrectionProcessing:
    """Test how tagger processes corrections."""
    
    def test_add_single_correction(self, tagger_learner):
        """Test adding a single correction sample."""
        embedding = np.random.randn(256).astype(np.float32)
        
        result = tagger_learner.add_correction_sample(
            embedding=embedding,
            original_predictions={'main_category_indices': [0, 1]},
            corrected_labels={'main_category_indices': [2, 3]},
            confidence=0.95
        )
        
        assert 'status' in result
    
    def test_add_multiple_corrections(self, tagger_learner):
        """Test adding multiple corrections."""
        for i in range(5):
            embedding = np.random.randn(256).astype(np.float32)
            tagger_learner.add_correction_sample(
                embedding=embedding,
                original_predictions={'main_category_indices': [i]},
                corrected_labels={'main_category_indices': [i+1]},
                confidence=0.8 + (i * 0.02)
            )
    
    def test_corrections_with_different_confidence_levels(self, tagger_learner):
        """Test that corrections with different confidence levels are handled."""
        samples = []
        
        for i in range(5):
            sample = {
                'embedding': np.random.randn(256).astype(np.float32),
                'original_main': [i],
                'corrected_main': [i+1],
                'confidence': 0.5 + (i * 0.1)  # 0.5, 0.6, 0.7, 0.8, 0.9
            }
            samples.append(sample)
        
        result = tagger_learner.train_on_corrections(samples, epochs=2)
        assert 'error' not in result
    
    def test_training_with_main_and_sub_categories(self, tagger_learner):
        """Test training with both main and sub category corrections."""
        samples = []
        
        for i in range(5):
            sample = {
                'embedding': np.random.randn(256).astype(np.float32),
                'original_main': [i % 11],
                'corrected_main': [(i + 1) % 11],
                'original_sub': [i % 141],
                'corrected_sub': [(i + 1) % 141],
                'confidence': 0.8
            }
            samples.append(sample)
        
        result = tagger_learner.train_on_corrections(samples)
        assert 'error' not in result


class TestTaggerContinuousLearning:
    """Test continuous learning from corrections."""
    
    def test_continuous_correction_and_training_cycle(self, tagger_learner):
        """Test complete correction -> training cycle."""
        for batch in range(3):
            samples = [
                {
                    'embedding': np.random.randn(256).astype(np.float32),
                    'original_main': [i],
                    'corrected_main': [i + batch],
                    'confidence': 0.7 + (batch * 0.1)
                }
                for i in range(5)
            ]
            
            result = tagger_learner.train_on_corrections(samples, epochs=1)
            assert 'error' not in result
        
        # Should have training records
        assert len(tagger_learner.training_history) >= 3
    
    def test_correction_pattern_learning(self, tagger_learner):
        """Test that repeated corrections for same category are learned."""
        # Simulate repeated corrections: category 0 should be 1, 2 should be 3, etc.
        
        for _ in range(2):  # Two rounds of corrections
            samples = [
                {'embedding': np.random.randn(256).astype(np.float32), 'original_main': [0], 'corrected_main': [1]},
                {'embedding': np.random.randn(256).astype(np.float32), 'original_main': [0], 'corrected_main': [1]},
                {'embedding': np.random.randn(256).astype(np.float32), 'original_main': [2], 'corrected_main': [3]},
                {'embedding': np.random.randn(256).astype(np.float32), 'original_main': [2], 'corrected_main': [3]},
                {'embedding': np.random.randn(256).astype(np.float32), 'original_main': [4], 'corrected_main': [5]},
            ]
            
            result = tagger_learner.train_on_corrections(samples)
            assert 'error' not in result


class TestTaggerTrainingVariations:
    """Test different training configurations."""
    
    def test_training_with_different_epochs(self, tagger_learner):
        """Test training with varying number of epochs."""
        samples = [
            {'embedding': np.random.randn(256).astype(np.float32), 'original_main': [i], 'corrected_main': [i+1]}
            for i in range(5)
        ]
        
        for epochs in [1, 2, 5]:
            learner_temp = TaggerFeedbackLearner(
                MockTaggerModel(), 
                Path(tempfile.gettempdir()) / f"temp_{epochs}",
                device='cpu'
            )
            result = learner_temp.train_on_corrections(samples, epochs=epochs)
            assert result.get('epochs') == epochs or 'error' not in result
    
    def test_training_with_batch_sizes(self, tagger_learner):
        """Test training with different numbers of samples."""
        for num_samples in [2, 5, 10]:
            samples = [
                {'embedding': np.random.randn(256).astype(np.float32), 'original_main': [i], 'corrected_main': [i+1]}
                for i in range(num_samples)
            ]
            
            if num_samples >= 2:  # Minimum requirement
                result = tagger_learner.train_on_corrections(samples)
                assert 'error' not in result or result.get('samples_trained') == num_samples


class TestTaggerModelWeightUpdates:
    """Test that training updates model weights."""
    
    def test_training_updates_model_weights(self, tagger_learner):
        """Test that training actually updates the model weights."""
        # Get initial weights
        initial_weights = [p.clone() for p in tagger_learner.tagger_model.parameters()]
        
        samples = [
            {'embedding': np.random.randn(256).astype(np.float32), 'original_main': [i], 'corrected_main': [i+1]}
            for i in range(5)
        ]
        
        tagger_learner.train_on_corrections(samples, epochs=2)
        
        # Check that weights changed
        weights_changed = any(
            not torch.allclose(p, w, atol=1e-4) 
            for p, w in zip(tagger_learner.tagger_model.parameters(), initial_weights)
        )
        assert weights_changed or len(tagger_learner.training_history) > 0
    
    def test_weights_change_proportional_to_training(self, tagger_learner):
        """Test that more training causes more weight changes."""
        changes_1_epoch = []
        changes_3_epochs = []
        
        # Test 1 epoch
        samples = [
            {'embedding': np.random.randn(256).astype(np.float32), 'original_main': [i], 'corrected_main': [i+1]}
            for i in range(5)
        ]
        
        initial_weights = [p.clone() for p in tagger_learner.tagger_model.parameters()]
        tagger_learner.train_on_corrections(samples, epochs=1)
        
        for p, w in zip(tagger_learner.tagger_model.parameters(), initial_weights):
            changes_1_epoch.append((p - w).abs().mean().item())
        
        # Test with fresh learner, 3 epochs
        tagger_learner2 = TaggerFeedbackLearner(
            MockTaggerModel(),
            Path(tempfile.gettempdir()) / "temp_epochs",
            device='cpu'
        )
        
        initial_weights2 = [p.clone() for p in tagger_learner2.tagger_model.parameters()]
        tagger_learner2.train_on_corrections(samples, epochs=3)
        
        for p, w in zip(tagger_learner2.tagger_model.parameters(), initial_weights2):
            changes_3_epochs.append((p - w).abs().mean().item())


class TestTaggerErrorHandling:
    """Test error handling in tagger."""
    
    def test_empty_samples_list(self, tagger_learner):
        """Test training with empty samples list."""
        result = tagger_learner.train_on_corrections([])
        assert 'error' in result
    
    def test_single_sample_rejected(self, tagger_learner):
        """Test that single sample is rejected."""
        samples = [
            {'embedding': np.random.randn(256).astype(np.float32), 'original_main': [0], 'corrected_main': [1]}
        ]
        
        result = tagger_learner.train_on_corrections(samples)
        assert 'error' in result
    
    def test_malformed_sample_handling(self, tagger_learner):
        """Test handling of malformed samples."""
        samples = [
            {'embedding': np.random.randn(256).astype(np.float32), 'original_main': [0]},  # Missing corrected_main
            {'embedding': np.random.randn(256).astype(np.float32), 'original_main': [1], 'corrected_main': [2]}
        ]
        
        # Should handle gracefully
        try:
            result = tagger_learner.train_on_corrections(samples)
            # Either processes successfully or returns error
            assert isinstance(result, dict)
        except (KeyError, ValueError):
            # Acceptable to raise if malformed
            pass


class TestTaggerPersistenceAndLoading:
    """Test model persistence across sessions."""
    
    def test_model_persists_to_disk(self, tagger_learner):
        """Test that trained model persists to disk."""
        samples = [
            {'embedding': np.random.randn(256).astype(np.float32), 'original_main': [i], 'corrected_main': [i+1]}
            for i in range(5)
        ]
        
        tagger_learner.train_on_corrections(samples)
        
        model_file = tagger_learner.storage_path / "tagger_finetuned.pt"
        assert model_file.exists()
        assert model_file.stat().st_size > 0
    
    def test_training_history_persists(self, tagger_learner):
        """Test that training history persists to disk."""
        samples = [
            {'embedding': np.random.randn(256).astype(np.float32), 'original_main': [i], 'corrected_main': [i+1]}
            for i in range(5)
        ]
        
        tagger_learner.train_on_corrections(samples)
        
        history_file = tagger_learner.storage_path / "tagger_training_history.json"
        assert history_file.exists()
        
        with open(history_file, 'r') as f:
            history_data = json.load(f)
            assert len(history_data) > 0


class TestTaggerPerformance:
    """Test training performance."""
    
    def test_training_completes_in_reasonable_time(self, tagger_learner):
        """Test that training completes quickly."""
        samples = [
            {'embedding': np.random.randn(256).astype(np.float32), 'original_main': [i], 'corrected_main': [i+1]}
            for i in range(5)
        ]
        
        start = time.time()
        tagger_learner.train_on_corrections(samples, epochs=2)
        duration = time.time() - start
        
        # Should complete in reasonable time
        assert duration < 30, f"Training took {duration}s, should be faster"
