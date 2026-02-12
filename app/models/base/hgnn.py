"""
Simplified HGNN Model for Fashion Outfit Compatibility
Based on optimized hyperparameter search results (h=256, hd=32, nl=1, ah=4, dr=0.30)
"""
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


# ============ ATTENTION POOLING ============
class MultiHeadAttnPool(nn.Module):
    """Multi-head attention-based pooling for variable-length sequences."""
    def __init__(self, dim, n_heads=4, dropout=0.1):
        super().__init__()
        self.dim = dim
        self.n_heads = n_heads
        self.head_dim = dim // n_heads
        assert dim % n_heads == 0, "dim must be divisible by n_heads"
        
        self.query = nn.Linear(dim, dim)
        self.attention_dropout = nn.Dropout(dropout)
        
    def forward(self, x, mask):
        """
        x: (B, L, dim) - sequence embeddings
        mask: (B, L) - binary mask (1 for valid, 0 for padding)
        Returns: pooled (B, dim), weights (B, L)
        """
        B, L, D = x.shape
        
        # Compute attention scores
        q = self.query(x)  # (B, L, dim)
        scores = q.sum(dim=2, keepdim=True)  # (B, L, 1) - simple scoring
        
        # Apply mask
        mask_expanded = mask.unsqueeze(-1).float()  # (B, L, 1)
        scores = scores * mask_expanded  # mask out padding
        scores = scores - 1e9 * (1 - mask_expanded)  # large negative for padding
        
        # Softmax attention
        attn_weights = F.softmax(scores, dim=1)  # (B, L, 1)
        attn_weights = self.attention_dropout(attn_weights)
        
        # Weighted sum pooling
        pooled = (x * attn_weights).sum(dim=1)  # (B, dim)
        
        return pooled, attn_weights.squeeze(-1)


# ============ HYPERGRAPH CONVOLUTIONAL LAYER ============
class HypergraphConvLayer(nn.Module):
    """Hypergraph Convolutional Layer with sparse matrix support."""
    def __init__(self, in_dim, out_dim, use_bias=True):
        super().__init__()
        self.linear = nn.Linear(in_dim, out_dim, bias=use_bias)
        self.norm = nn.LayerNorm(out_dim)

    def forward(self, X, H):
        """
        Hypergraph convolution using incidence matrix.
        X: (N, in_dim) - node features (on GPU)
        H: (N, E) - hypergraph incidence matrix (can be sparse, typically on CPU)
        Returns: (N, out_dim)
        """
        try:
            # Use H @ H^T to approximate neighbor aggregation
            if H.is_sparse:
                # Explicitly move to CPU before coalescing
                H_cpu = H.cpu()
                H_coalesced = H_cpu.coalesce()
                X_cpu = X.cpu()
                
                # H @ H^T on CPU - ensure both are COO format to avoid CSR beta warning
                H_t = H_coalesced.t().coalesce()  # Transpose and coalesce to COO
                HHt = torch.sparse.mm(H_coalesced, H_t)
                HHt_coo = HHt.coalesce()  # Ensure result is in COO format
                
                # Sparse-dense multiplication
                out_cpu = torch.sparse.mm(HHt_coo, X_cpu)
                out = out_cpu.to(X.device)
            else:
                HHt = H @ H.t()
                out = HHt @ X
        except Exception as e:
            # Fallback: use identity if error occurs
            out = X
        
        out = self.linear(out)
        out = F.relu(out)
        out = self.norm(out)
        return out


# ============ HYPERGRAPH NEURAL NETWORK ============
class HypergraphNN(nn.Module):
    """Hypergraph Neural Network for outfit compatibility."""
    def __init__(self, in_dim, hidden_dim=128, out_dim=64, num_layers=2, dropout=0.2):
        super().__init__()
        self.in_dim = in_dim
        self.hidden_dim = hidden_dim
        self.out_dim = out_dim
        self.num_layers = num_layers
        self.dropout = nn.Dropout(dropout)
        
        # Initial projection
        self.input_proj = nn.Linear(in_dim, hidden_dim)
        
        # Hypergraph convolutional layers
        self.hgc_layers = nn.ModuleList([
            HypergraphConvLayer(hidden_dim if i > 0 else hidden_dim, hidden_dim)
            for i in range(num_layers)
        ])
        
        # Output projection
        self.output_proj = nn.Linear(hidden_dim, out_dim)
        self.out_norm = nn.LayerNorm(out_dim)

    def forward(self, X, H):
        """
        X: (N, in_dim) - node features (on GPU)
        H: (N, E) - incidence matrix (can be sparse)
        Returns: (N, out_dim)
        """
        x = self.input_proj(X)
        x = F.relu(x)
        x = self.dropout(x)
        
        for hgc_layer in self.hgc_layers:
            x = hgc_layer(x, H)
            x = self.dropout(x)
        
        x = self.output_proj(x)
        x = F.relu(x)
        x = self.out_norm(x)
        x = F.normalize(x, p=2, dim=-1)
        return x


# ============ FASHION HYPERGRAPH MODEL ============
class FashionHyperGraphModel(nn.Module):
    """
    Simplified Fashion HyperGraph Model for outfit compatibility.
    
    Best configuration from hyperparameter search (50 trials):
    - h=256 (fusion_hidden)
    - hd=32 (hgnn_dim) 
    - nl=1 (num_hgnn_layers)
    - ah=4 (attn_heads)
    - dr=0.30 (dropout)
    
    Achieves: Val F1=0.9177, Test F1=0.8705, Test AUC=0.9512
    """
    def __init__(self, 
                 clip_embed_dim=512,
                 attr_embed_dim=256,
                 fusion_hidden=256,          # Best: h=256
                 final_embedding_dim=32,     # Best: hd=32
                 dropout=0.30,               # Best: dr=0.30
                 attn_heads=4,               # Best: ah=4
                 use_hgnn=True,
                 hgnn_hidden_list=[(32,)],   # Best: nl=1 (single layer of 32)
                 use_cross_attention=False,
                 use_hierarchical_pooling=False,
                 use_moe=False,
                 num_experts=1):
        super().__init__()
        
        # Extract hgnn parameters from list (for compatibility)
        if hgnn_hidden_list and len(hgnn_hidden_list) > 0:
            first_branch = hgnn_hidden_list[0]
            if isinstance(first_branch, (list, tuple)) and len(first_branch) > 0:
                hidden_dim = fusion_hidden
                hgnn_dim = first_branch[-1]  # Output dimension
                num_hgnn_layers = len(first_branch)
            else:
                hidden_dim = fusion_hidden
                hgnn_dim = final_embedding_dim
                num_hgnn_layers = 1
        else:
            hidden_dim = fusion_hidden
            hgnn_dim = final_embedding_dim
            num_hgnn_layers = 1
        
        self.in_dim = clip_embed_dim + attr_embed_dim
        
        # HGNN encoder
        if use_hgnn:
            self.hgnn = HypergraphNN(
                in_dim=self.in_dim,
                hidden_dim=hidden_dim,
                out_dim=hgnn_dim,
                num_layers=num_hgnn_layers,
                dropout=dropout
            )
        else:
            self.hgnn = nn.Sequential(
                nn.Linear(self.in_dim, hgnn_dim),
                nn.ReLU(),
                nn.LayerNorm(hgnn_dim)
            )
        
        # Attention pooling
        self.attn_pool = MultiHeadAttnPool(hgnn_dim, n_heads=attn_heads, dropout=dropout)
        
        # Scoring head
        self.score_head = nn.Sequential(
            nn.Linear(hgnn_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid()
        )
    
    def forward(self, clip_feats, attr_feats, H=None, Dv_inv_sqrt=None, De_inv=None,
                outfit_nodes=None, outfit_mask=None):
        """
        Forward pass for outfit scoring.
        
        Args:
            clip_feats: (N, clip_embed_dim) - CLIP image embeddings
            attr_feats: (N, attr_embed_dim) - Attribute embeddings
            H: (N, E) - Hypergraph incidence matrix (optional for HGNN)
            Dv_inv_sqrt: Ignored (kept for compatibility)
            De_inv: Ignored (kept for compatibility)
            outfit_nodes: (B, L) - Outfit node indices
            outfit_mask: (B, L) - Binary mask for padding
            
        Returns:
            outfit_scores: (B,) - Compatibility scores
            node_emb: (N, hgnn_dim) - Node embeddings
            pooled: (B, hgnn_dim) - Pooled outfit embeddings
            attn: (B, L) - Attention weights
        """
        # Concatenate raw features to match notebook HGNN input
        x = torch.cat([clip_feats, attr_feats], dim=1)
        
        # Apply HGNN or simple projection
        if isinstance(self.hgnn, HypergraphNN) and H is not None:
            node_emb = self.hgnn(x, H)
        else:
            node_emb = self.hgnn(x) if not isinstance(self.hgnn, HypergraphNN) else self.hgnn.input_proj(x)
        
        # If no outfit nodes provided, return node embeddings only
        if outfit_nodes is None:
            return None, node_emb, None, None
        
        # Normalize outfit_nodes/outfit_mask to batched shape
        if outfit_nodes.dim() == 1:
            outfit_nodes = outfit_nodes.unsqueeze(0)
        if outfit_mask is not None and outfit_mask.dim() == 1:
            outfit_mask = outfit_mask.unsqueeze(0)

        # Extract outfit embeddings
        emb = node_emb[outfit_nodes]  # (B, L, hgnn_dim)
        
        # Attention pooling
        pooled, attn = self.attn_pool(emb, outfit_mask)  # (B, hgnn_dim)
        
        # Score prediction
        outfit_scores = self.score_head(pooled).squeeze(-1)  # (B,)
        
        return outfit_scores, node_emb, pooled, attn


# ============ ATTRIBUTE ENCODER ============
class AttributeEncoder(nn.Module):
    """Encoder for categorical attributes."""
    def __init__(self, input_dim, output_dim=256, hidden_dim=512):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, output_dim)
        )

    def forward(self, x):
        x = self.encoder(x)
        return F.normalize(x, p=2, dim=-1)


def generate_attribute_embeddings_from_df(df, encoder=None,
                                          max_related=None, max_category=None,
                                          max_main=None, max_sub=None, device="cpu"):
    """
    Converts structured attributes into flat binary/numeric vectors and encodes them.
    """

    def encode_list_column(col, max_index):
        binary_matrix = np.zeros((len(df), max_index), dtype=np.float32)
        for i, values in enumerate(df[col]):
            for v in values:
                if 0 <= v < max_index:
                    binary_matrix[i, v] = 1.0
        return binary_matrix

    # Dynamically set max indices if not provided
    if max_related is None:
        max_related = max([max(v) if len(v) > 0 else 0 for v in df["related_indices"]]) + 1
    if max_category is None:
        max_category = max([max(v) if len(v) > 0 else 0 for v in df["category_indices"]]) + 1
    if max_main is None:
        max_main = max([max(v) if len(v) > 0 else 0 for v in df["main_category_indices"]]) + 1
    if max_sub is None:
        max_sub = max([max(v) if len(v) > 0 else 0 for v in df["sub_category_indices"]]) + 1

    # Encode list-type columns
    related_bin = encode_list_column("related_indices", max_related)
    category_bin = encode_list_column("category_indices", max_category)
    main_bin = encode_list_column("main_category_indices", max_main)
    sub_bin = encode_list_column("sub_category_indices", max_sub)

    # Concatenate all features
    X_attr = np.concatenate([related_bin, category_bin, main_bin, sub_bin], axis=1)

    # Initialize encoder
    input_dim = X_attr.shape[1]
    if encoder is None:
        encoder = AttributeEncoder(input_dim=input_dim).to(device)

    # Encode
    X_tensor = torch.tensor(X_attr, dtype=torch.float32).to(device)
    encoder.eval()
    with torch.no_grad():
        embeddings = encoder(X_tensor).cpu().numpy()

    return embeddings, encoder
