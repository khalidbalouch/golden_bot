from __future__ import annotations
import ctypes
from multiprocessing import RawArray, Value
import numpy as np

class LockFreeRingBuffer:
    """Single-producer single-consumer (SPSC) lock-free queue."""
    def __init__(self, capacity: int = 100000):
        self.capacity = capacity
        self.data = RawArray(ctypes.c_double, capacity * 4) # Assuming 4 fields
        self.head = Value(ctypes.c_uint64, 0)
        self.tail = Value(ctypes.c_uint64, 0)

    def push(self, val: float) -> bool:
        h = self.head.value
        t = self.tail.value
        next_h = (h + 1) % self.capacity
        if next_h == t: return False # Full
        self.data[h] = val
        self.head.value = next_h
        return True

    def pop(self) -> float:
        h = self.head.value
        t = self.tail.value
        if h == t: return 0.0 # Empty
        val = self.data[t]
        self.tail.value = (t + 1) % self.capacity
        return val
