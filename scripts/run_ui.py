"""Script to run the Streamlit UI."""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Set environment variables
os.environ["PYTHONPATH"] = str(project_root)

if __name__ == "__main__":
    import streamlit.web.cli as stcli
    
    # Run Streamlit app using module mode
    sys.argv = [
        "streamlit",
        "run",
        "-m",
        "palantir.ui",
        "--server.port=8501",
        "--server.address=0.0.0.0"
    ]
    
    sys.exit(stcli.main()) 