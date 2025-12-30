import argparse
from collections.abc import Iterable
import os
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
    "--json_corpus_with_update",
    type=str,
    help="Label Studio corpus JSON with pre-annotations containing updates",
)
parser.add_argument(
    "--json_corpus_to_update",
    type=str,
    help="Label Studio corpus JSON where pre-annotations require updates",
)
parser.add_argument(
    "--output_dir",
    type=str,
    help="Where to write the full aggregated JSON",
)


def check_compatibility(annotation_schema: str, loaded_corpus: list[dict]) -> bool:
    logger.warning(
        "Compatibility check not enforced - calling it for developer awareness"
    )
    return True


def align_annotated_files(
    file_annotations_with_update: dict,
    file_annotations_to_update: dict,
    merge_key: str = "annotations",  # eventually want to do "predictions"/pre-annotations as well
) -> dict:
    return {}


def id_based_aggregate_and_align(
    corpus_with_update: dict[int, dict],
    corpus_to_update: dict[int, dict],
) -> Iterable[dict]:
    for file_id in corpus_with_update.keys() | corpus_to_update.keys():
        match file_id in corpus_with_update, file_id in corpus_to_update:
            case True, False:
                logger.warning("%d in updated corpus but not original", file_id)
                yield corpus_with_update[file_id]
            case False, True:
                logger.warning("%d in original corpus but not in updated", file_id)
                yield corpus_with_update[file_id]
            case True, True:
                logger.warning(
                    "%d in both original and updated corpora - updating and resolving conflicts",
                    file_id,
                )
                yield align_annotated_files(
                    corpus_with_update[file_id], corpus_to_update[file_id]
                )
            case _:
                ValueError(
                    f"{file_id} missing from both original and updated, this shouldn't be possible"
                )


def id_to_file_annotations(corpus: list[dict]) -> dict[int, dict]:
    return {file_annotation["id"]: file_annotation for file_annotation in corpus}


def aggregate_and_align(
    corpus_with_update: list[dict],
    corpus_to_update: list[dict],
) -> list[dict]:
    return list(
        id_based_aggregate_and_align(
            id_to_file_annotations(corpus_with_update),
            id_to_file_annotations(corpus_to_update),
        )
    )


def load_json_corpus(json_corpus: str) -> list[dict]:
    with open(json_corpus, mode="r") as f:
        return json.load(f)


def process_and_write(
    annotation_schema: str,
    json_corpus_with_update: str,
    json_corpus_to_update: str,
    output_dir: str,
) -> None:
    corpus_with_update = load_json_corpus(json_corpus_with_update)
    corpus_to_update = load_json_corpus(json_corpus_to_update)
    if not (
        check_compatibility(annotation_schema, corpus_with_update)
        and check_compatibility(annotation_schema, corpus_to_update)
    ):
        ValueError("Schema compatibility issue")
    updated_corpus = aggregate_and_align(
        corpus_with_update,
        corpus_to_update,
    )
    with open(os.path.join(output_dir, "updated_corpus.json"), mode="w") as f:
        json.dump(updated_corpus, f)


def main() -> None:
    args = parser.parse_args()
    process_and_write(
        args.annotation_schema,
        args.json_corpus_with_update,
        args.json_corpus_to_update,
        args.output_dir,
    )


if __name__ == "__main__":
    main()
