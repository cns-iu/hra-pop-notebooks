from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], cwd: Path) -> None:
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd, check=True)


def get_venv_python(venv_dir: Path) -> Path:
    if sys.platform.startswith("win"):
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def main() -> None:
    project_dir = Path(__file__).resolve().parent
    scripts_dir = project_dir / "scripts"
    requirements_file = project_dir / "requirements.txt"
    venv_dir = project_dir / ".venv"

    if not scripts_dir.exists():
        raise FileNotFoundError(f"Scripts directory not found: {scripts_dir}")
    if not requirements_file.exists():
        raise FileNotFoundError(f"requirements.txt not found: {requirements_file}")

    # Create the virtual environment if needed.
    if not venv_dir.exists():
        run_command([sys.executable, "-m", "venv", str(venv_dir)], cwd=project_dir)

    venv_python = get_venv_python(venv_dir)
    if not venv_python.exists():
        raise FileNotFoundError(f"Virtual environment Python not found: {venv_python}")

    # Install dependencies into the virtual environment.
    run_command([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"], cwd=project_dir)
    run_command([str(venv_python), "-m", "pip", "install", "-r", str(requirements_file)], cwd=project_dir)

    # Run all Python scripts in /scripts in sorted order.
    script_files = sorted(scripts_dir.glob("*.py"))
    if not script_files:
        print("No Python scripts found in scripts/. Nothing to run.")
        return

    for script_path in script_files:
        run_command([str(venv_python), str(script_path)], cwd=project_dir)

    print("All scripts completed successfully.")


if __name__ == "__main__":
    main()
