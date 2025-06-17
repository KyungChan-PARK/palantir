import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REQ = ROOT / "requirements.txt"
DEPS = ROOT / "deps"

if not REQ.exists():
    print("requirements.txt not found", file=sys.stderr)
    sys.exit(1)

cmd = [sys.executable, "-m", "pip", "install", "-r", str(REQ)]
if DEPS.exists():
    cmd += ["--find-links", str(DEPS)]

print("Running:", " ".join(cmd))
subprocess.check_call(cmd)
