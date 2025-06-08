import sys
import importlib
import types

try:
    importlib.import_module("PIL")
except ModuleNotFoundError:
    stub = types.ModuleType("PIL")
    stub.Image = types.SimpleNamespace(open=lambda *a, **k: None)
    sys.modules["PIL"] = stub
