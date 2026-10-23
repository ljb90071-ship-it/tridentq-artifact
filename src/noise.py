"""Deterministic, mean-one duration perturbations; allocation bounds are untouched."""
import hashlib
import math
import random

def factor(trace_id, kernel_id, device_id, sigma):
    if sigma < 0:
        raise ValueError('sigma must be nonnegative')
    key=f'20261023:prediction:{trace_id}:{kernel_id}:{device_id}'
    seed=int.from_bytes(hashlib.sha256(key.encode('utf-8')).digest()[:8], 'big')
    z=random.Random(seed).normalvariate(0,1)
    return math.exp(-sigma*sigma/2 + sigma*z)
