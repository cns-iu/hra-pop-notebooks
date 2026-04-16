from pathlib import Path
import gzip
import shutil
import os
import pandas


def gunzip_if_needed(gz_path: str) -> Path:
    """Decompress a .gz file and infer output filename."""
    gz_path = Path(gz_path)
    output_path = gz_path.with_suffix("")  # removes .gz

    if output_path.exists():
        print(f"⚙️ Already unzipped — skipping: {output_path}")
        return output_path

    print(f"📦 Decompressing {gz_path} ...")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with gzip.open(gz_path, "rb") as f_in:
        with open(output_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

    print(f"✅ File extracted to: {output_path}")
    return output_path


def load_qc_data():
    zip_path = "data/hra-pop-v1.1-qc-report.csv.gz"
    extract_dir = "data/unzipped"
    gunzip_if_needed(zip_path)


def main():
    load_qc_data()


if __name__ == "__main__":
    main()
