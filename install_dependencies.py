import subprocess
import sys

REQUIREMENTS = "requirements.txt"

if __name__ == "__main__":
    try:
        subprocess.check_call([
            sys.executable,
            "-m",
            "pip",
            "install",
            "--upgrade",
            "pip",
        ])
        subprocess.check_call([
            sys.executable,
            "-m",
            "pip",
            "install",
            "-r",
            REQUIREMENTS,
        ])
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'fastapi==0.115.12'])
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pydantic==2.10.6'])
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'reflex==0.7.12'])
        print("[OK] Dependencies installed.")
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1) 