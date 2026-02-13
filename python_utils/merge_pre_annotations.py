from operator import itemgetter
from dataclasses import dataclass, field
import argparse
from collections.abc import Iterable, Mapping, Sequence, Collection
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
    "--annotation_schema_path",
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

Offsets = tuple[int, int]


@dataclass
class SignatureCluster:
    central_dose: dict
    signatures: Collection[dict] = field(default=set())
    relations: Collection[dict] = field(default=set())

    def __post_init__(self):
        if len(self.relations) != len(self.signatures):
            raise ValueError(
                f"Have {len(self.relations)} relations and {len(self.signatures)} signatures - should be equal"
            )
        if set(map(itemgetter("to_id"), self.relations)) == set(
            map(itemgetter("id"), self.signatures)
        ):
            raise ValueError(
                "Relation target entity IDs don't match signature entity IDs"
            )


def overlap_match(offsets_1: Offsets, offsets_2: Offsets) -> bool:
    return offsets_1[0] < offsets_2[1] and offsets_1[1] > offsets_2[0]


# TODO - contrive an actual implementation
def check_compatibility(annotation_schema_path: str, loaded_corpus: list[dict]) -> bool:
    logger.error(
        "Compatibility check not enforced - calling it for developer awareness"
    )
    return True


def recoordinate_signature_cluster(
    new_rt_entity: dict, signature_cluster: SignatureCluster
) -> SignatureCluster:
    def update_relation(relation: dict) -> dict:
        relation["from_id"] = new_rt_entity["id"]
        return relation

    return SignatureCluster(
        central_dose=new_rt_entity,
        signatures=signature_cluster.signatures,
        relations=set(map(update_relation, signature_cluster.relations)),
    )


def build_entity_id_to_entity_map(entities: list[dict]) -> Mapping[str, dict]:
    return {entity["id"]: entity for entity in entities}


def single_offset_coordination(
    first: Collection[Offsets], second: Collection[Offsets]
) -> Mapping[Offsets, Collection[Offsets]]:
    return {}


def double_offset_coordination(
    first: Collection[Offsets], second: Collection[Offsets]
) -> Mapping[Offsets, Offsets]:
    return {}


def align_results(
    results_with_updates: Collection[dict],
    results_to_updates: Collection[dict],
) -> Sequence[dict]:
    offsets_to_radiation_therapy = get_offsets_to_radiation_therapy_mapping(
        dictionary_pre_annotations=results_to_updates
    )
    offsets_to_adverse_event = get_offsets_to_adverse_event_mapping(
        dictionary_pre_annotations=results_to_updates
    )
    offsets_to_signature_cluster = get_offsets_to_signature_cluster_mapping(
        signature_pre_annotations=results_with_updates
    )
    for signature_offsets, signature_cluster in offsets_to_signature_cluster.items():
        overlaps = [
            rt_entity
            for rt_offsets, rt_entity in offsets_to_radiation_therapy.items()
            if overlap_match(signature_offsets, rt_offsets)
        ]
    return []


def get_offsets_to_signature_cluster_mapping(
    signature_pre_annotations: Iterable[dict],
) -> Mapping[Offsets, SignatureCluster]:
    return {}


def get_offsets_to_radiation_therapy_mapping(
    dictionary_pre_annotations: Iterable[dict],
) -> Mapping[Offsets, dict]:
    return {}


def get_offsets_to_adverse_event_mapping(
    dictionary_pre_annotations: Iterable[dict],
) -> Mapping[Offsets, dict]:
    return {}


def align_annotated_files(
    file_annotation_with_update: dict,
    file_annotation_to_update: dict,
    merge_body: str = "predictions",  # eventually want to do "annotations"/manual annotations as well
) -> dict:
    results_with_updates = file_annotation_with_update.get(merge_body)
    results_to_updates = file_annotation_to_update.get(merge_body)
    if results_with_updates is None or results_to_updates is None:
        raise ValueError(
            f"At least one of the files in question is missing annotations/pre-annotations field: {merge_body}"
        )
    assert (
        file_annotation_with_update["id"] == file_annotation_to_update["id"]
        and file_annotation_with_update["data"] == file_annotation_to_update["data"]
    )
    return {
        "id": file_annotation_with_update["id"],
        "data": file_annotation_with_update["data"],
        merge_body: align_results(results_with_updates, results_to_updates),
    }


def id_based_aggregate_and_align(
    corpus_with_update: Mapping[int, dict],
    corpus_to_update: Mapping[int, dict],
) -> Iterable[dict]:
    for file_id in corpus_with_update.keys() | corpus_to_update.keys():
        match file_id in corpus_with_update, file_id in corpus_to_update:
            case True, False:
                logger.warning("%d in updated corpus but not original", file_id)
                yield corpus_with_update[file_id]
            case False, True:
                logger.warning("%d in original corpus but not in updated", file_id)
                yield corpus_to_update[file_id]
            case True, True:
                logger.warning(
                    "%d in both original and updated corpora - updating and resolving conflicts",
                    file_id,
                )
                yield align_annotated_files(
                    corpus_with_update[file_id], corpus_to_update[file_id]
                )
            case _:
                raise ValueError(f"{file_id} missing from both original and updated")


def id_to_file_annotations(corpus: Iterable[dict]) -> Mapping[int, dict]:
    return {file_annotation["id"]: file_annotation for file_annotation in corpus}


def aggregate_and_align(
    corpus_with_update: Sequence[dict],
    corpus_to_update: Sequence[dict],
) -> Sequence[dict]:
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
    annotation_schema_path: str,
    json_corpus_with_update: str,
    json_corpus_to_update: str,
    output_dir: str,
) -> None:
    corpus_with_update = load_json_corpus(json_corpus_with_update)
    corpus_to_update = load_json_corpus(json_corpus_to_update)
    if not (
        check_compatibility(annotation_schema_path, corpus_with_update)
        and check_compatibility(annotation_schema_path, corpus_to_update)
    ):
        raise ValueError("Schema compatibility issue")
    updated_corpus = aggregate_and_align(
        corpus_with_update,
        corpus_to_update,
    )
    with open(os.path.join(output_dir, "updated_corpus.json"), mode="w") as f:
        json.dump(updated_corpus, f)


def main() -> None:
    args = parser.parse_args()
    process_and_write(
        args.annotation_schema_path,
        args.json_corpus_with_update,
        args.json_corpus_to_update,
        args.output_dir,
    )


if __name__ == "__main__":
    main()
