"""
conftest.py — ensures the service root is on sys.path so that imports like
``from domain.models import User`` resolve when running pytest from the
service root (or any subdirectory).
"""
import os
import sys

_SERVICE_ROOT = os.path.dirname(os.path.abspath(__file__))
if _SERVICE_ROOT not in sys.path:
    sys.path.insert(0, _SERVICE_ROOT)
