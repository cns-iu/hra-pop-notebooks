import subprocess
import sys
from pathlib import Path

import pandas as pd


def create_venv_and_install_requirements() -> None:
    requirements_file = Path(__file__).with_name("requirements.txt")
    if not requirements_file.exists():
        raise FileNotFoundError(f"requirements.txt not found: {requirements_file}")

    requirements = pd.read_csv(
        requirements_file,
        header=None,
        comment="#",
        names=["requirement"],
        dtype=str,
    )["requirement"].dropna()
    requirements = requirements[requirements.str.strip() != ""]
    requirements_list = requirements.tolist()
    if not requirements_list:
        return

    venv_dir = Path(__file__).with_name(".venv")
    if not venv_dir.exists():
        subprocess.check_call([sys.executable, "-m", "venv", str(venv_dir)])

    venv_python = (
        venv_dir / "Scripts" / "python.exe"
        if sys.platform.startswith("win")
        else venv_dir / "bin" / "python"
    )

    subprocess.check_call(
        [str(venv_python), "-m", "pip", "install", *requirements_list]
    )


def get_data() -> pd.DataFrame:
    return pd.read_csv(
        "https://raw.githubusercontent.com/x-atlas-consortia/hra-pop/refs/heads/v1.1/output-data/v1.1/reports/atlas-ad-hoc/cell-types-in-anatomical-structurescts-per-as.csv"
    )


def get_cell_types(data_frame: pd.DataFrame) -> pd.DataFrame:
    result = data_frame[["organ", "tool", "cell_id", "cell_label"]]
    return result


if __name__ == "__main__":
    create_venv_and_install_requirements()
    get_cell_types(get_data()).to_csv("output/cell-types-hra-pop-v1.1.csv", index=False)
