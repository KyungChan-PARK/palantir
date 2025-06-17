import sys
import types

if "PIL" not in sys.modules:
    stub = types.ModuleType("PIL")
    stub.Image = types.SimpleNamespace(open=lambda *a, **k: None)
    sys.modules["PIL"] = stub
modules_to_stub = ["chromadb"]
for name in modules_to_stub:
    if name not in sys.modules:
        sys.modules[name] = types.ModuleType(name)
if "sqlalchemy" not in sys.modules:
    sa_stub = types.ModuleType("sqlalchemy")
    sa_stub.JSON = object
    sa_stub.Boolean = object
    sa_stub.Column = object
    sa_stub.Integer = object
    sa_stub.String = object
    sys.modules["sqlalchemy"] = sa_stub
modules_to_stub += ["psutil", "prefect", "networkx"]
for name in modules_to_stub:
    if name not in sys.modules:
        sys.modules[name] = types.ModuleType(name)
