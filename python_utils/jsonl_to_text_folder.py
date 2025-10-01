import logging
import argparse
import pathlib
import os

parser = argparse.ArgumentParser(description="")

parser.add_argument(
    "--jsonl_dir",
    type=str,
    help="The original type should be retained via the debug_source field",
)

parser.add_argument(
    "--output_dir",
    type=str,
    help="Where to write files for cTAKES",
)
logger = logging.getLogger(__name__)

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s -   %(message)s",
    datefmt="%m/%d/%Y %H:%M:%S",
    level=logging.INFO,
)


def __normalize(s: str) -> str:
    return " ".join(s.strip().lower().split())


def mkdir(dir_name: str) -> None:
    _dir_name = pathlib.Path(dir_name)
    _dir_name.mkdir(parents=True, exist_ok=True)

def get_ctakes_file_info(json_line: str) -> tuple[str, str]:
    note_dict = json.loads(json_line)
    return "", ""

def migrate_note(json_line: str, output_dir: str) -> None:
    ctakes_fn, file_content = get_ctakes_file_info(json_line)
    with open(os.path.join(output_dir, ctakes_fn), mode="w") as f:
        f.write(file_content)


def migrate_notes(jsonl_path: str, output_dir: str) -> None:
    with open(jsonl_path, mode="r") as jsonl_f:
        for json_line in jsonl_f:
            migrate_note(json_line, output_dir)


def migrate(jsonl_dir: str, output_dir: str) -> None:
    for fn in os.listdir(jsonl_dir):
        if fn.rstrip().lower().endswith("jsonl"):
            migrate_notes(os.path.join(jsonl_dir, fn), output_dir)


def main() -> None:
    args = parser.parse_args()
    migrate(args.jsonl_dir, args.output_dir)


if __name__ == "__main__":
    main()
