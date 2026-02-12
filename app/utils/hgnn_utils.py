import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import json
import pickle
from datetime import datetime, timezone
from typing import List, Dict, Tuple, Optional
from pathlib import Path

UTC = timezone.utc


# ----------------------------
# Utilities: build incidence and degree matrices
# ----------------------------
def build_incidence_matrix(num_nodes, hyperedges, device='cpu', dtype=torch.float32):
    """
    hyperedges: list of lists of node indices (each hyperedge is list of node ids)
    Returns:
      H: (N, M) incidence matrix
      Dv_inv_sqrt: (N,N) diagonal matrix of Dv^{-1/2}
      De_inv: (M,M) diagonal matrix of De^{-1}
    All returned as torch tensors on device.
    """
    M = len(hyperedges)
    N = num_nodes
    if M == 0:
        H = torch.zeros((N,0), dtype=dtype, device=device)
        Dv_inv_sqrt = torch.eye(N, dtype=dtype, device=device)
        De_inv = torch.zeros((0,0), dtype=dtype, device=device)
        return H, Dv_inv_sqrt, De_inv

    # Build dense H as float
    H = torch.zeros((N, M), dtype=dtype, device=device)
    for j, hedge in enumerate(hyperedges):
        for node in hedge:
            if 0 <= node < N:
                H[node, j] = 1.0

    # Degrees
    dv = H.sum(dim=1)  # (N,)
    de = H.sum(dim=0)  # (M,)

    # guard against zeros
    dv = torch.where(dv == 0, torch.ones_like(dv), dv)
    de = torch.where(de == 0, torch.ones_like(de), de)

    Dv_inv_sqrt = torch.diag(torch.pow(dv, -0.5))
    De_inv = torch.diag(torch.pow(de, -1.0))

    return H, Dv_inv_sqrt, De_inv