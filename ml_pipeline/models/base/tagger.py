import torch
import torch.nn as nn
import torch.nn.functional as F

class AttentionFusion(nn.Module):
    """Generic attention fusion between hidden features and logits."""
    def __init__(self, hidden_dim, num_in, num_out, dropout=0.3):
        super().__init__()
        self.query = nn.Linear(hidden_dim, hidden_dim)
        self.key   = nn.Linear(num_in, hidden_dim)
        self.value = nn.Linear(num_in, hidden_dim)
        self.fc    = nn.Linear(hidden_dim, num_out)
        self.dropout = nn.Dropout(dropout / 2)

    def forward(self, h, logits):
        # h: (B, H), logits: (B, C_in)
        q = self.query(h)          # (B, H)
        k = self.key(logits)       # (B, H)
        v = self.value(logits)     # (B, H)

        # scaled dot-product attention across batch
        attn_scores  = torch.matmul(q, k.T) / (q.size(-1) ** 0.5)  # (B, B)
        attn_weights = torch.softmax(attn_scores, dim=-1)          # (B, B)

        fused = torch.matmul(attn_weights, v)  # (B, H)
        fused = self.dropout(fused + h)        # residual
        return self.fc(fused)                  # (B, num_out)

class HierarchicalMultiTaskModel(nn.Module):
    def __init__(self, embed_dim, num_related, num_categories, num_main, num_sub,
                 hidden_dim=512, dropout=0.3, use_attention=True):
        super().__init__()

        self.shared = nn.Sequential(
            nn.Linear(embed_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout)
        )

        self.main_head = nn.Linear(hidden_dim, num_main)

        # Attention heads unchanged
        self.use_attention = use_attention
        self.sub_head = AttentionFusion(hidden_dim, num_main, num_sub, dropout) if use_attention else nn.Sequential(
            nn.Linear(hidden_dim + num_main, hidden_dim // 2),
            nn.LayerNorm(hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout / 2),
            nn.Linear(hidden_dim // 2, num_sub)
        )
        self.category_head_attn = AttentionFusion(hidden_dim, num_main + num_sub, num_categories, dropout) if use_attention else nn.Sequential(
            nn.Linear(hidden_dim + num_main + num_sub, hidden_dim // 2),
            nn.LayerNorm(hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout / 2),
            nn.Linear(hidden_dim // 2, num_categories)
        )
        self.related_head_attn = AttentionFusion(hidden_dim, num_main + num_sub, num_related, dropout) if use_attention else nn.Sequential(
            nn.Linear(hidden_dim + num_main + num_sub, hidden_dim // 2),
            nn.LayerNorm(hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout / 2),
            nn.Linear(hidden_dim // 2, num_related)
        )

        # Post-attention refinement blocks (extra capacity, no simplification)
        refine_dim = hidden_dim // 2
        self.category_refine = nn.Sequential(
            nn.Linear(num_categories, refine_dim),
            nn.ReLU(),
            nn.Dropout(dropout / 2),
            nn.Linear(refine_dim, num_categories)
        )
        self.related_refine = nn.Sequential(
            nn.Linear(num_related, refine_dim),
            nn.ReLU(),
            nn.Dropout(dropout / 2),
            nn.Linear(refine_dim, num_related)
        )

    def forward(self, x):
        h = self.shared(x)
        main_logits = self.main_head(h)

        # sub via attention
        if self.use_attention:
            sub_logits = self.sub_head(h, main_logits)
        else:
            sub_logits = self.sub_head(torch.cat([h, main_logits], dim=1))

        ms_logits = torch.cat([main_logits, sub_logits], dim=1)

        # category via attention + refinement
        if self.use_attention:
            category_logits = self.category_head_attn(h, ms_logits)
        else:
            category_logits = self.category_head_attn(torch.cat([h, ms_logits], dim=1))
        category_logits = self.category_refine(category_logits)

        # related via attention + refinement
        if self.use_attention:
            related_logits = self.related_head_attn(h, ms_logits)
        else:
            related_logits = self.related_head_attn(torch.cat([h, ms_logits], dim=1))
        related_logits = self.related_refine(related_logits)

        return main_logits, sub_logits, category_logits, related_logits


# Note: FashionCLIP and image processing utilities are imported lazily
# to avoid import errors when they're not available
def precompute_embeddings_simple(
    df,                # pandas DataFrame with column 'item_id'
    images_path,  
    fclip=None,        # FashionCLIP instance with encode_images(list[PIL], batch_size=int)
    out_path="embeddings.npy",
    batch_size=256,
    force=False,
):
    """Precompute embeddings using FashionCLIP (lazy import)"""
    import os
    import math
    import numpy as np
    from PIL import Image
    from tqdm.auto import tqdm
    import torch   # only to detect GPU availability
    
    if fclip is None:
        try:
            from fashion_clip.fashion_clip import FashionCLIP
            fclip = FashionCLIP("fashion-clip")
        except ImportError as e:
            raise ImportError("FashionCLIP not available") from e
    
    def _load_img(p):
        with Image.open(p) as im:
            return im.convert("RGB")

    # If cached, load and return
    if os.path.exists(out_path) and not force:
        print(f"Loading cached embeddings from {out_path}")
        return np.load(out_path)

    # Device info (do not assume fclip.to exists)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")

    n = len(df)
    n_batches = math.ceil(n / batch_size)
    parts = []

    bar = tqdm(total=n_batches, desc="Embedding images", unit="batch", leave=True)

    for start in range(0, n, batch_size):
        end = min(start + batch_size, n)
        paths = [os.path.join(images_path, f"{df.iloc[i]['item_id']}.jpg") for i in range(start, end)]

        # Sequential image loading (one-by-one)
        imgs = []
        for p in paths:
            try:
                imgs.append(_load_img(p))
            except Exception as e:
                # log and skip missing/corrupt files
                print(f"Skipping {p}: {e}")

        if not imgs:
            bar.update(1)
            continue

        # Encode and collect
        # If the encoder supports a device arg, pass it via encode_images(...)
        try:
            embeds = fclip.encode_images(imgs, batch_size=len(imgs), device=device)
        except TypeError:
            embeds = fclip.encode_images(imgs, batch_size=len(imgs))

        parts.append(np.asarray(embeds, dtype=np.float32))

        bar.update(1)

    bar.close()

    if parts:
        all_embeds = np.vstack(parts)
    else:
        all_embeds = np.empty((0, 512), dtype=np.float32)  # adjust dim if needed

    # Trim to exactly n rows (safety)
    if all_embeds.shape[0] > n:
        all_embeds = all_embeds[:n]

    np.save(out_path, all_embeds)
    print(f"✅ Saved embeddings to {out_path} (shape: {all_embeds.shape})")
    return all_embeds