import importlib

for pkg in ("fastapi", "pydantic", "reflex"):
    mod = importlib.import_module(pkg)
    print(f"{pkg}: {mod.__version__}")
