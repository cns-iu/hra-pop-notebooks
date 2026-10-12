import gzip
import json
from pathlib import Path
from pprint import pprint

from tqdm import tqdm


def iterate_through_json_lines(filename: str, print_line: bool = False):
    """Iterate through a JSON Lines (JSONL) file and yield each JSON object.

    Transparently handles gzipped (.jsonl.gz) files. Skips an upfront line-count
    pass (no fixed total/ETA on the progress bar) since some inputs are tens of GB
    gzipped, making a full pre-count pass (decompressing the whole file just to
    count lines, before decompressing it again to process) too expensive.
    """
    filename = Path(filename)
    opener = gzip.open if filename.suffix == ".gz" else open

    print(
        f"Now processing {filename}, printing {'enabled' if print_line else 'not enabled'}."
    )

    with opener(filename, "rt", encoding="utf-8") as f:
        for line in tqdm(f, desc="Processing JSONL lines", unit="line"):
            line = line.strip()
            if not line:
                continue
            line_json = json.loads(line)
            if print_line:
                pprint(line_json)
            yield line_json
