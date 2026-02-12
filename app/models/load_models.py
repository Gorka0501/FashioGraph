import sys
import torch
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Use absolute path to models (they are in app/models/base/)
BASE = Path(__file__).resolve().parent / "base"

load_status = {}

# --- FashionCLIP ---
def load_fashion_clip():
    """Load FashionCLIP model (optional - skipped if torch/torchvision incompatible)"""
    try:
        from fashion_clip.fashion_clip import FashionCLIP
        # Initialize model with use_fast warning suppressed
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=UserWarning)
            model = FashionCLIP("fashion-clip")
        
        # Set use_fast=True on the image processor to avoid deprecation warning
        if hasattr(model, 'processor') and hasattr(model.processor, 'image_processor'):
            # Force use_fast to avoid slow processor deprecation warning
            try:
                model.processor.image_processor.use_fast = True
            except (AttributeError, TypeError):
                pass  # Some processor versions may not support this
        
        print("✅ FashionCLIP model loaded.")
        load_status['fashion_clip'] = 'loaded'
        return model
    except (ImportError, RuntimeError, ModuleNotFoundError) as e:
        # Common errors: torch/torchvision compatibility, missing transformers, etc.
        # FashionCLIP is optional - log and continue
        error_msg = str(e)
        if "torchvision::nms" in error_msg or "CLIPModel" in error_msg:
            print(f"⚠️  FashionCLIP skipped (torch/torchvision compatibility issue)")
            load_status['fashion_clip'] = 'skipped (torch/torchvision incompatible)'
        else:
            print(f"⚠️  FashionCLIP skipped: {error_msg[:60]}")
            load_status['fashion_clip'] = f'skipped: {error_msg[:60]}'
        return None
    except Exception as e:
        print(f"⚠️  FashionCLIP skipped: {str(e)[:60]}")
        load_status['fashion_clip'] = f'skipped: {str(e)[:60]}'
        return None

# --- AttributeEncoder ---
def load_attribute_encoder():
    try:
        from app.models.base.hgnn import AttributeEncoder
        print("Imported AttributeEncoder.")
    except Exception as e:
        print("AttributeEncoder not available:", e)
        load_status['attribute_encoder'] = f'fail: {e}'
        return None

    ATTR_PATH = BASE / "attribute_encoder.pt"
    state = None
    if ATTR_PATH.exists():
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=FutureWarning)
                raw = torch.load(ATTR_PATH, map_location=device, weights_only=False)
            state = raw.get("state_dict", raw) if isinstance(raw, dict) else raw
        except Exception as e:
            print("❌ Could not read attribute encoder checkpoint:", e)

    input_dim = 256
    if isinstance(state, dict):
        for v in state.values():
            if hasattr(v, "ndim") and v.ndim == 2:
                input_dim = int(v.shape[1])
                break

    try:
        model = AttributeEncoder(input_dim=input_dim).to(device)
        if isinstance(state, dict):
            model.load_state_dict(state, strict=False)
            model.eval()
            print(f"✅ AttributeEncoder loaded (input_dim={input_dim}).")
            load_status['attribute_encoder'] = f'loaded (input_dim={input_dim})'
        else:
            print(f"✅ AttributeEncoder instantiated (input_dim={input_dim}, no checkpoint).")
            load_status['attribute_encoder'] = f'instantiated (input_dim={input_dim})'
        return model
    except Exception as e:
        print("❌ Failed to create AttributeEncoder:", e)
        load_status['attribute_encoder'] = f'fail: {e}'
        return None

# --- FashionHyperGraphModel ---
def load_fashion_hypergraph():
    try:
        from app.models.base.hgnn import FashionHyperGraphModel
    except Exception as e:
        print("❌ Could not import FashionHyperGraphModel:", e)
        load_status['fashion_hypergraph'] = f'fail: {e}'
        return None

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=FutureWarning)
        state = torch.load(BASE / "model.pt", map_location=device, weights_only=False)
    state = state.get("state_dict", state) if isinstance(state, dict) else state

    try:
        # Best model architecture from hyperparameter search (50 trials)
        # Configuration: h=256, hd=32, nl=1, ah=4, dr=0.30
        # Best Val F1: 0.9177, Test F1: 0.8705, Test AUC: 0.9512
        model = FashionHyperGraphModel(
            clip_embed_dim=512,
            attr_embed_dim=256,
            fusion_hidden=256,          # h=256 (hidden_dim)
            hgnn_hidden_list=[(32,)],   # hd=32, nl=1 (single layer)
            final_embedding_dim=32,     # match hgnn output dim
            dropout=0.30,               # dr=0.30
            attn_heads=4,               # ah=4
            use_hierarchical_pooling=False
        )
        
        # Try to load weights - handle architecture mismatch gracefully
        try:
            missing, unexpected = model.load_state_dict(state, strict=False)
            if missing or unexpected:
                print(f"WARNING: Partial model load - missing: {len(missing)}, unexpected: {len(unexpected)}")
                print("    Some weights from checkpoint don't match new architecture")
                print("    Incompatible layers initialized with random weights")
        except Exception as load_err:
            print(f"WARNING: Could not load checkpoint weights: {load_err}")
            print("    Model initialized with random weights (needs retraining)")
        
        model.to(device).eval()
        print(f"FashionHyperGraphModel ready (simplified architecture: h=256, hd=32, nl=1, ah=4, dr=0.30)")
        load_status['fashion_hypergraph'] = 'loaded (simplified architecture, may need retraining)'
        return model
    except Exception as e:
        print("Could not create FashionHyperGraphModel:", e)
        load_status['fashion_hypergraph'] = f'fail: {e}'
        return None

# --- HierarchicalMultiTaskModel ---
def load_hierarchical_tagger():
    """Load HierarchicalMultiTaskModel"""
    try:
        # Patch transformers before importing to avoid CLIPModel error
        import sys
        import transformers
        if not hasattr(transformers, 'CLIPModel'):
            from transformers import CLIPVisionModel
            transformers.CLIPModel = CLIPVisionModel
        
        # Try direct import first
        from app.models.base.tagger import HierarchicalMultiTaskModel
    except ImportError:
        try:
            # Fallback: use importlib for direct loading
            import importlib.util
            spec = importlib.util.spec_from_file_location("tagger", BASE / "tagger.py")
            if spec is None or spec.loader is None:
                raise ImportError("Could not load tagger.py")
            tagger_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(tagger_module)
            HierarchicalMultiTaskModel = tagger_module.HierarchicalMultiTaskModel
        except Exception as e:
            print(f"❌ Could not import HierarchicalMultiTaskModel: {e}")
            load_status['hierarchical_tagger'] = f'fail: {str(e)[:80]}'
            return None

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=FutureWarning)
            state = torch.load(BASE / "classification_model.pt", map_location=device, weights_only=False)
        state = state.get("state_dict", state) if isinstance(state, dict) else state

        # Helper to count CSV lines (excluding header)
        def count_csv_lines(filepath):
            """Count lines in CSV file (excluding header row)"""
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return sum(1 for _ in f) - 1
            except:
                return None
        
        # Get dimensions from CSV files
        current_dir = Path(__file__).resolve().parent
        num_main = count_csv_lines(current_dir / "idx2main.csv") or 11
        num_sub = count_csv_lines(current_dir / "idx2sub.csv") or 141
        num_categories = count_csv_lines(current_dir / "idx2category.csv") or 210
        num_related = count_csv_lines(current_dir / "idx2related.csv") or 312
        
        # Embedding dimension from state dict
        embed_dim = 512
        if 'shared.0.weight' in state:
            embed_dim = state['shared.0.weight'].shape[1]
        
        model = HierarchicalMultiTaskModel(embed_dim=embed_dim, num_related=num_related,
                                           num_categories=num_categories, num_main=num_main, num_sub=num_sub)
        model.load_state_dict(state, strict=False)
        model.to(device).eval()
        
        print(f"✅ HierarchicalMultiTaskModel loaded.")
        load_status['hierarchical_tagger'] = f'loaded (embed_dim={embed_dim})'
        return model
    except Exception as e:
        print(f"❌ Could not load HierarchicalMultiTaskModel: {e}")
        load_status['hierarchical_tagger'] = f'fail: {str(e)[:80]}'
        return None
    
# --- Load all models ---
def load_all_models():
    """Convenience function to load all models and return them in a dict."""
    models = {
        "fashion_clip": load_fashion_clip(),
        "attribute_encoder": load_attribute_encoder(),
        "fashion_hypergraph": load_fashion_hypergraph(),
        "hierarchical_tagger": load_hierarchical_tagger(),
    }
    print("\n--- Load Summary ---")
    for k, v in load_status.items():
        print(f"{k}: {v}")
    print("--------------------\n")
    return models

# --- Main runner ---
if __name__ == "__main__":
    print("Device:", device)
    print("Model files:", [p.name for p in BASE.glob("*.pt")])

    fashion_clip = load_fashion_clip()
    attribute_encoder = load_attribute_encoder()
    fashion_hypergraph = load_fashion_hypergraph()
    hierarchical_tagger = load_hierarchical_tagger()

    print("\n--- Load Summary ---")
    for k, v in load_status.items():
        print(f"{k}: {v}")
    print("--------------------\n")
