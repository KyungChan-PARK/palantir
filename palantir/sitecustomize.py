import sys
import types

if 'PIL' not in sys.modules:
    stub = types.ModuleType('PIL')
    stub.Image = types.SimpleNamespace(open=lambda *a, **k: None)
    sys.modules['PIL'] = stub
