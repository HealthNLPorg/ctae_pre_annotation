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


def check_compatibility(annotation_schema: str, loaded_corpus: dict) -> bool:
    logger.warning(
        "Compatibility check not enforced - calling it for developer awareness"
    )
    return True


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
