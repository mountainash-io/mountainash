"""
Check which Ibis is being used.
"""
import ibis
print(f"Ibis version: {ibis.__version__}")
print(f"Ibis location: {ibis.__file__}")

import sys
print(f"\nPython: {sys.executable}")
print(f"Path: {sys.path[:5]}")
