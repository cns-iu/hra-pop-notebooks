import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REQUIREMENTS = HERE / "requirements.txt"
RAW_DATA = HERE / "raw-data"


def install_requirements():
    """Install packages listed in requirements.txt into the current interpreter."""
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS)]
    )


sys.path.append(str(HERE.parent))
try:
    from shared_common import *  # noqa: E402,F403
except ImportError:
    # shared_common needs tqdm; install requirements on first run, then retry
    install_requirements()
    from shared_common import *  # noqa: E402,F403


def process_jsonlines():
    for line in iterate_through_json_lines(
        RAW_DATA / "sc-transcriptomics-cell-summaries.top10k.jsonl.gz", False
    ):
        print(line["cell_source"])


def main():
    install_requirements()
    process_jsonlines()

    import pandas as pd
    import requests

    # TODO: de-duplicate HRApop datasets


if __name__ == "__main__":
    main()
