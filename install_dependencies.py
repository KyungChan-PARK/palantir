import subprocess
import sys
import platform
import os

REQUIREMENTS = "requirements.txt"
OFFLINE_PACKAGES_DIR = "offline_preparation/python_packages/unified"


def get_numpy_wheel():
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "windows":
        return f"{OFFLINE_PACKAGES_DIR}/numpy-2.2.6-cp313-cp313-win_amd64.whl"
    elif system == "linux":
        if "x86_64" in machine:
            return f"{OFFLINE_PACKAGES_DIR}/numpy-2.2.6-cp313-cp313t-manylinux_2_17_x86_64.manylinux2014_x86_64.whl"
    return None


def get_numpy_source():
    """Return the path to the NumPy source archive as a fallback."""
    tarball = "numpy-2.2.6.tar.gz"
    return tarball if os.path.exists(tarball) else None


if __name__ == "__main__":
    try:
        # Upgrade pip
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--upgrade",
                "pip",
            ]
        )

        # Install NumPy from wheel or source archive
        numpy_wheel = get_numpy_wheel()
        if numpy_wheel and os.path.exists(numpy_wheel):
            subprocess.check_call(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    numpy_wheel,
                ]
            )
            print("[OK] NumPy installed from local wheel.")
        else:
            numpy_src = get_numpy_source()
            if numpy_src:
                subprocess.check_call(
                    [
                        sys.executable,
                        "-m",
                        "pip",
                        "install",
                        numpy_src,
                    ]
                )
                print("[OK] NumPy installed from source archive.")
            else:
                print("[WARNING] No compatible NumPy package found.")

        # Install other dependencies
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-r",
                REQUIREMENTS,
            ]
        )

        # Install specific package versions
        subprocess.check_call([sys.executable, "-m", "pip", "install", "fastapi==0.115.12"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pydantic==2.10.6"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "reflex==0.7.12"])
        print("[OK] Dependencies installed.")
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)
