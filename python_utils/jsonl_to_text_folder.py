import logging
import json
import argparse
import pathlib
from functools import lru_cache
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
note_dict = dict[str, str | int]


def debug_restriction(_note_dict: note_dict) -> note_dict:
    @lru_cache
    def __norm_key(k: str) -> str:
        return k.strip().lower()

    def __is_index_key(k: str) -> bool:
        norm_k = __norm_key(k)
        return "mrn" in norm_k or "id" in norm_k

    return {k: v for k, v in _note_dict if __is_index_key(k)}


def __normalize(s: str) -> str:
    return " ".join(s.strip().lower().split())


def mkdir(dir_name: str) -> None:
    _dir_name = pathlib.Path(dir_name)
    _dir_name.mkdir(parents=True, exist_ok=True)


def get_ctakes_file_info(json_line: str) -> tuple[str, str]:
    _note_dict = json.loads(json_line)
    raw_ctakes_fn = _note_dict.get("id")
    if raw_ctakes_fn is None:
        ValueError(
            f"id not found for note (with other info):\n{debug_restriction(_note_dict)}"
        )
        ctakes_fn = "MISSING_ID"
    else:
        ctakes_fn = str(raw_ctakes_fn)

    raw_rpt_text = _note_dict.get("RPT_TEXT")
    raw_rpt_text_no_html = _note_dict.get("RPT_TEXT_NO_HTML")
    match raw_rpt_text, raw_rpt_text_no_html:
        case None, None:
            ValueError(
                f"No report text for either RPT_TEXT or RPT_TEXT_NO_HTML found in note {ctakes_fn} :\n{debug_restriction(_note_dict)}"
            )
            rpt_text = ""
        case None, str(raw_rpt_text_no_html):
            rpt_text = raw_rpt_text_no_html
        case str(raw_rpt_text), None:
            rpt_text = raw_rpt_text
        case str(raw_rpt_text), str(raw_rpt_text_no_html):
            # For now just in case
            rpt_text = raw_rpt_text_no_html
        case _:
            ValueError(
                f"Report text issues for both RPT_TEXT: {raw_rpt_text}\nand RPT_TEXT_NO_HTML: {raw_rpt_text_no_html}\n found in note {ctakes_fn} :\n{debug_restriction(_note_dict)}"
            )
            rpt_text = ""
    return ctakes_fn, rpt_text


def migrate_note(json_line: str, output_dir: str) -> None:
    ctakes_fn, file_content = get_ctakes_file_info(json_line)
    with open(os.path.join(output_dir, f"{ctakes_fn}.txt"), mode="w") as f:
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
