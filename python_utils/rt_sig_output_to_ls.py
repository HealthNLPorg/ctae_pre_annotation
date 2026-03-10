from typing import Any
from more_itertools import map_reduce, one
from enum import Enum
from itertools import chain
from collections.abc import Iterable, Mapping, Collection
import argparse
import json
import os
from functools import cache
import polars as pl

parser = argparse.ArgumentParser(description="")

parser.add_argument(
    "--rt_tables_dir",
    type=str,
    help="Where the cTAKES RT output is",
)

parser.add_argument(
    "--ae_tables_dir",
    type=str,
    help="Where the cTAKES AE output is",
)
parser.add_argument(
    "--notes_dir",
    type=str,
    help="Where the original notes are",
)
parser.add_argument(
    "--output_dir",
    type=str,
    help="Where to write the full aggregated JSON",
)

RT_COLUMN_SIGNATURE_TO_LS_SIGNATURE = {
    "central_dose": "Radiotherapy Treatment",
    "boost": "Boost",
    "date": "Date",
    "secondary_dose": "Secondary Dose",
    "fraction_frequency": "Fraction Frequency",
    "fraction_number": "Fraction Number",
    "site": "Site",
}


class AnnotationStage(Enum):
    predictions = "predictions"
    annotations = "annotations"


def ctakes_csv_to_ls_file_annotation(
    rt_csv_path: str | None,
    ae_csv_path: str | None,
    file_index: int,
    total_files: int,
    file_text: str,
    annotation_state: Enum,
) -> Mapping[Any, Any]:
    # Remove straggler rows where all cells are null

    rt_frame = (
        pl.read_csv(rt_csv_path).filter(~pl.all_horizontal(pl.all().is_null()))
        if rt_csv_path is not None
        else None
    )
    ae_frame = (
        pl.read_csv(ae_csv_path).filter(~pl.all_horizontal(pl.all().is_null()))
        if ae_csv_path is not None
        else None
    )
    rt_annotations = (
        chain.from_iterable(
            rt_dict_to_ls_annotations(
                row_dict=row_dict, file_index=file_index, row_index=row_index
            )
            for row_index, row_dict in enumerate(rt_frame.to_dicts())
        )
        if rt_frame is not None
        else []
    )

    ae_annotations = (
        chain.from_iterable(
            ae_dict_to_ls_annotations(
                row_dict=row_dict, file_index=file_index, row_index=row_index
            )
            for row_index, row_dict in enumerate(ae_frame.to_dicts())
        )
        if ae_frame is not None
        else []
    )
    return {
        "id": file_index,
        "data": {"text": file_text},
        annotation_state.value: {
            "id": file_index + total_files,
            "result": list(chain(ae_annotations, rt_annotations)),
        },
    }


def build_file_id_to_file_preannotation(
    rt_tables_dir: str, ae_tables_dir: str, file_id_to_file_text: Mapping[int, str]
) -> Mapping[int, dict]:
    def __file_id(fn: str) -> int:
        return int(fn.split("_")[0])

    def warned_first(files: Collection[str]) -> str:
        try:
            return one(files)
        except Exception:
            raise ValueError(
                f"More than one ({len(files)}) files for file id {__file_id(next(iter(files)))}"
            )

    rt_table_files = os.listdir(rt_tables_dir)
    ae_table_files = os.listdir(ae_tables_dir)
    file_id_to_rt_table = map_reduce(
        rt_table_files, keyfunc=__file_id, reducefunc=warned_first
    )
    if len(file_id_to_rt_table) != len(rt_table_files):
        raise ValueError(
            f"Of {len(rt_table_files)} rt files {len(file_id_to_rt_table)} are unique"
        )
    file_id_to_ae_table = map_reduce(
        ae_table_files, keyfunc=__file_id, reducefunc=warned_first
    )
    if len(file_id_to_ae_table) != len(ae_table_files):
        raise ValueError(
            f"Of {len(ae_table_files)} ae files {len(file_id_to_ae_table)} are unique"
        )

    def file_id_to_ls_annotation(file_id: int) -> Mapping[Any, Any]:
        rt_table_fn = file_id_to_rt_table.get(file_id)
        ae_table_fn = file_id_to_ae_table.get(file_id)
        if rt_table_fn is None and ae_table_fn is None:
            raise ValueError(f"Missing both tables for {file_id}")
        return ctakes_csv_to_ls_file_annotation(
            rt_csv_path=os.path.join(rt_tables_dir, rt_table_fn)
            if rt_table_fn is not None
            else None,
            ae_csv_path=os.path.join(ae_tables_dir, ae_table_fn)
            if ae_table_fn is not None
            else None,
            file_index=file_id,
            total_files=len(file_id_to_rt_table.keys() | file_id_to_ae_table.keys()),
            file_text=file_id_to_file_text.get(file_id, "MISSING_FILE_TEXT"),
            annotation_state=AnnotationStage.predictions,
        )

    return {
        __file_id(table_fn): ctakes_csv_to_ls_file_annotation(
            csv_path=os.path.join(tables_dir, table_fn),
            file_index=file_index,
            total_files=len(table_files),
            file_text=file_id_to_file_text.get(
                __file_id(table_fn), "MISSING_FILE_TEXT"
            ),
            annotation_state=AnnotationStage.predictions,
        )
        for file_index, table_fn in enumerate(table_files)
    }


def build_file_id_to_file_text(notes_dir: str) -> Mapping[int, str]:
    def __file_id(fn: str) -> int:
        return int(fn.split(".")[0])

    def __load(notes_dir: str, note_fn: str) -> str:
        with open(os.path.join(notes_dir, note_fn), mode="r") as f:
            return f.read()

    return {
        __file_id(note_fn): __load(notes_dir, note_fn)
        for note_fn in os.listdir(notes_dir)
    }


def build_label_studio_label(
    origin: str,
    annotation_id: str,
    start: int,
    end: int,
    label_space: str,
    labels: list[str],
) -> dict:
    return {
        "value": {"start": start, "end": end, "text": None, "labels": labels},
        "id": annotation_id,
        "from_name": label_space,
        "to_name": "text",
        "origin": origin,
    }


def build_label_studio_relation(
    source_id: str, target_id: str, labels: list[str]
) -> dict:
    return {
        "from_id": source_id,
        "to_id": target_id,
        "type": "relation",
        "direction": "right",
        "labels": labels,
    }


def entities_to_relation(
    from_id: str,
    to_id: str,
    direction: str = "right",
    labels: list[str] = ["Signature"],
) -> dict:
    return {
        "from_id": from_id,
        "to_id": to_id,
        "type": "relation",
        "direction": direction,
        "labels": labels,
    }


def dtr_cell_to_ls_entity(
    start: int,
    end: int,
    text: str | None,
    dtr_labels: list[str],
    ls_id: str,
    origin: str,
) -> dict:
    return cell_to_ls_entity(
        start=start,
        end=end,
        text=text,
        entity_type="choices",
        entity_labels=dtr_labels,
        ls_id=ls_id,
        from_name="DocTimeRel",
        to_name="text",
        origin=origin,
    )


def rt_cell_to_ls_entity(
    start: int, end: int, text: str | None, rt_column_name: str, ls_id: str, origin: str
) -> dict:
    return cell_to_ls_entity(
        start=start,
        end=end,
        text=text,
        entity_type="labels",
        entity_labels=[RT_COLUMN_SIGNATURE_TO_LS_SIGNATURE[rt_column_name]],
        ls_id=ls_id,
        from_name="RadiotherapySignature",
        to_name="text",
        origin=origin,
    )


def cell_to_ls_entity(
    start: int,
    end: int,
    text: str | None,
    entity_type: str,
    entity_labels: list[str],
    ls_id: str,
    from_name: str,
    to_name: str,
    origin: str,
) -> dict:
    return {
        "value": {
            "start": start,
            "end": end,
            "text": text,
            entity_type: entity_labels,
        },
        "id": ls_id,
        "from_name": from_name,
        "to_name": to_name,
        "type": entity_type,
        "origin": origin,
    }


def old_rt_cell_to_ls_entity(
    column_name: str,
    start: int,
    end: int,
    ls_id: str,
    text: str | None = None,
    from_name: str = "RadiotherapySignature",
    to_name: str = "text",
    entity_type: str = "labels",
    origin: str = "prediction",
    column_mapping: Mapping[str, str] = RT_COLUMN_SIGNATURE_TO_LS_SIGNATURE,
) -> dict:
    return {
        "value": {
            "start": start,
            "end": end,
            "text": text,
            entity_type: [column_mapping[column_name]],
        },
        "id": ls_id,
        "from_name": from_name,
        "to_name": to_name,
        "type": entity_type,
        "origin": origin,
    }


def ae_dict_to_ls_annotations(
    row_dict: Mapping[str, str],
    file_index: int,
    row_index: int,
) -> Iterable[dict]:
    return []


def rt_dict_to_ls_annotations(
    row_dict: Mapping[str, str],
    file_index: int,
    row_index: int,
    anchor_column: str = "central_dose",
) -> Iterable[dict]:
    current = 0
    fixed_row_dict = {}
    for raw_column, raw_cell in row_dict.items():
        column = raw_column.strip()
        if raw_cell != "None":
            if column == "dtr":
                fixed_row_dict[column] = [raw_cell]
            else:
                offsets = parse_offset_str(raw_cell)
                fixed_row_dict[column] = offsets

    def build_id(annotation_index) -> str:
        return f"{file_index}_{row_index}_{annotation_index}"

    def build_ls_entity(
        column_name: str, ls_id: str, origin: str = "prediction"
    ) -> dict:
        if column_name == "dtr":
            return dtr_cell_to_ls_entity(
                start=fixed_row_dict[anchor_column][0],
                end=fixed_row_dict[anchor_column][1],
                text=None,  # TODO - maybe file text
                dtr_labels=fixed_row_dict[column_name],
                ls_id=ls_id,
                origin=origin,
            )
        return rt_cell_to_ls_entity(
            start=fixed_row_dict[column_name][0],
            end=fixed_row_dict[column_name][0],
            text=None,
            rt_column_name=column_name,
            ls_id=ls_id,
            origin=origin,
        )

    anchor_id = build_id(current)
    anchor_entity = build_ls_entity(anchor_column, anchor_id)
    current += 1
    id_to_signature = {}
    for signature_column in fixed_row_dict.keys() - {anchor_column}:
        signature_id = build_id(current)
        id_to_signature[signature_id] = build_ls_entity(signature_column, signature_id)
        current += 1
    relations = (
        entities_to_relation(from_id=anchor_id, to_id=signature_id)
        for signature_id in id_to_signature.keys()
    )
    return chain((anchor_entity,), id_to_signature.values(), relations)


@cache
def parse_offset_str(offset_str: str) -> tuple[int, int] | None:
    elements = offset_str.split("_")
    if len(elements) != 2 or not all(map(str.isnumeric, elements)):
        raise ValueError(f"Problematic offset string {offset_str}")
    begin, end = elements
    return int(begin), int(end)


def build_and_write_jsonl(
    rt_tables_dir: str, ae_tables_dir: str, notes_dir: str, output_dir: str
) -> None:
    file_id_to_file_text = build_file_id_to_file_text(notes_dir)
    file_id_to_file_preannotation = build_file_id_to_file_preannotation(
        rt_tables_dir=rt_tables_dir,
        ae_tables_dir=ae_tables_dir,
        file_id_to_file_text=file_id_to_file_text,
    )
    with open(os.path.join(output_dir, "label_studio_corpus.json"), mode="w") as f:
        json.dump(list(file_id_to_file_preannotation.values()), f)


def main() -> None:
    args = parser.parse_args()
    build_and_write_jsonl(
        args.rt_tables_dir,
        args.ae_tables_dir,
        args.notes_dir,
        args.output_dir,
    )


if __name__ == "__main__":
    main()
