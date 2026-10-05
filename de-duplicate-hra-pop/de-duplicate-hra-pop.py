import subprocess
import sys
from pathlib import Path

REQUIREMENTS = Path(__file__).parent / "requirements.txt"


def install_requirements():
    """Install packages listed in requirements.txt into the current interpreter."""
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS)]
    )


def main():
    install_requirements()

    import pandas as pd
    import requests

    # TODO: de-duplicate HRApop datasets


if __name__ == "__main__":
    main()
