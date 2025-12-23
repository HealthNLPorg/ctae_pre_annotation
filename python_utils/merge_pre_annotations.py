import argparse
from functools import partial, lru_cache
import json

import logging

logger = logging.getLogger(__name__)

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s -   %(message)s",
    datefmt="%m/%d/%Y %H:%M:%S",
    level=logging.INFO,
)
parser = argparse.ArgumentParser(description="")

parser.add_argument(
    "--annotation_schema",
    type=str,
    help="XML Label Studio schema (unused for now but ideally want to enforce compatibility at some point)",
)

parser.add_argument(
    "--corpus_with_update",
    type=str,
    help="Label Studio corpus JSON with pre-annotations containing updates",
)
parser.add_argument(
    "--corpus_to_update",
    type=str,
    help="Label Studio corpus JSON where pre-annotations require updates",
)
parser.add_argument(
    "--output_dir",
    type=str,
    help="Where to write the full aggregated JSON",
)


@lru_cache
def parse_offset_str(offset_str: str) -> tuple[int, int] | None:
    elements = offset_str.split("_")
    if len(elements) != 2 or not all(map(str.isnumeric, elements)):
        ValueError(f"Problematic offset string {offset_str}")
        return None
    begin, end = elements
    return int(begin), int(end)


def check_compatibility(annotation_schema: str, loaded_corpus: dict) -> bool:
    logger.warning(
        "Compatibility check not enforced - calling it for developer awareness"
    )
    return True


def adjust_indices(
    report_id: int,
    character_offset_map: dict[int, int],
    signature_row_dict: dict[str, str],
) -> dict[str, tuple[int, int]]:
    def parse_and_adjust(offset_str: str) -> tuple[int, int] | None:
        result = parse_offset_str(offset_str)
        if result is None:
            ValueError(
                f"Report ID: {report_id} - could not parse offset string {offset_str}"
            )
            return None
        ascii_begin, ascii_end = result
        original_begin = character_offset_map.get(ascii_begin)
        original_end = character_offset_map.get(ascii_end)
        if original_begin is None or original_end is None:
            ValueError(
                f"Report ID: {report_id} - ASCII begin {ascii_begin} obtained {original_begin}, ASCII end {ascii_end} obtained {original_end}"
            )
            return None
        return original_begin, original_end

    final = {}
    for signature, offset_str in signature_row_dict.items():
        offsets = parse_and_adjust(offset_str)
        if offsets is not None:
            final[signature] = offsets
    return final


def aggregate_and_align(
    annotation_schema: str,
    corpus_with_update: str,
    corpus_to_update: str,
    output_dir: str,
) -> None:
    pass


def main() -> None:
    args = parser.parse_args()


if __name__ == "__main__":
    main()
