"""Shared test fixtures / path setup.

The backend under `src/` imports its modules by bare name (`import db`,
`from bidplan import days_until`), so the tests must run with `src/` on the
import path. This adds it once for the whole suite.
"""
import os
import sys

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)
