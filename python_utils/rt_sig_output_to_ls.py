import argparse
import json
import os
from typing import Mapping
from functools import lru_cache
import polars as pl

parser = argparse.ArgumentParser(description="")

parser.add_argument(
    "--tables_dir",
    type=str,
    help="Where the cTAKES output is",
)

parser.add_argument(
    "--notes_dir",
    type=str,
    help="Where the cTAKES output is",
)
parser.add_argument(
    "--character_offset_map_table",
    type=str,
    help="Character offset mapping (ASCII only to original) in TSV table",
)
parser.add_argument(
    "--output_dir",
    type=str,
    help="Where to write the full aggregated JSON",
)

COLUMN_SIGNATURE_TO_LS_SIGNATURE = {
    "central_dose": "Radiotherapy Treatment",
    "boost": "Boost",
    "date": "Date",
    "secondary_dose": "Secondary Dose",
    "fraction_frequency": "Fraction Frequency",
    "fraction_number": "Fraction Number",
    "site": "Site",
}


def ctakes_csv_to_ls_file_annotation(csv_path: str) -> dict:
    # Remove straggler rows where all cells are null
    rt_frame = pl.read_csv(csv_path).filter(~pl.all_horizontal(pl.all().is_null()))
    NotImplementedError("Parse table")
    return {}


def build_file_id_to_file_preannotation(tables_dir: str) -> Mapping[int, dict]:
    def __file_id(fn: str) -> int:
        return int(fn.split("_")[0])

    return {
        __file_id(table_fn): ctakes_csv_to_ls_file_annotation(
            os.path.join(tables_dir, table_fn)
        )
        for table_fn in os.listdir(tables_dir)
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


def row_dict_to_ls_annotations(row_dict: dict[str, str]) -> list[dict]:
    fixed_row_dict = {
        column.strip(): parse_offset_str(cell)
        for column, cell in row_dict.items()
        if cell != "None" and parse_offset_str(cell) is not None
    }
    NotImplementedError("Finish")
    return []


# of the form
# <ascii begin>_<original begin>,...,<ascii begin>_<original begin>
def get_offset_map_from_string(offset_map_string: str) -> dict[int, int]:
    return {
        ascii_offset: original_offset
        for ascii_offset, original_offset in filter(
            None, map(parse_offset_str, offset_map_string.split(","))
        )
    }


@lru_cache
def parse_offset_str(offset_str: str) -> tuple[int, int] | None:
    elements = offset_str.split("_")
    if len(elements) != 2 or not all(map(str.isnumeric, elements)):
        ValueError(f"Problematic offset string {offset_str}")
        return None
    begin, end = elements
    return int(begin), int(end)


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
            final[signature.strip()] = offsets
    return final


def get_report_id_to_offset_map(
    character_offset_map_table: str,
    report_id_col_key: str = "FIXME",
    offset_map_col_key: str = "FIXME",
) -> dict[int, dict[int, int]]:
    df = pl.read_csv(character_offset_map_table, separator="\t")
    return {
        int(report_id): get_offset_map_from_string(offset_map_string)
        for report_id, offset_map_string in zip(
            df[report_id_col_key], df[offset_map_col_key]
        )
    }


def coordinate_to_label_studio_dict(file_preannotation: dict, file_text: str) -> dict:
    NotImplementedError("Turn into an actual Label Studio dictionary")
    return {}


def build_jsonl(
    file_id_to_file_text: Mapping[int, str],
    file_id_to_file_preannotation: Mapping[int, dict],
) -> list[dict]:
    def __assemble(file_id: int) -> dict | None:
        file_text = file_id_to_file_text.get(file_id)
        if file_text is None:
            ValueError(f"Missing file with ID: {file_id}")
            return None

        file_preannotation = file_id_to_file_preannotation.get(file_id)
        if file_preannotation is None:
            ValueError(f"Missing file table with ID: {file_id}")
            return None
        return coordinate_to_label_studio_dict(file_preannotation, file_text)

    # So ty doesn't complain
    return list(
        filter(
            None,
            map(
                __assemble,
                sorted(
                    file_id_to_file_text.keys() | file_id_to_file_preannotation.keys()
                ),
            ),
        )
    )


def build_and_write_jsonl(
    tables_dir: str, notes_dir: str, character_offset_map_table: str, output_dir: str
) -> None:
    file_id_to_file_text = build_file_id_to_file_text(notes_dir)
    file_id_to_file_preannotation = build_file_id_to_file_preannotation(tables_dir)
    with open(os.path.join(output_dir, "label_studio_corpus.json"), mode="w") as f:
        f.write(
            json.dumps(build_jsonl(file_id_to_file_text, file_id_to_file_preannotation))
        )


def main() -> None:
    args = parser.parse_args()
    build_and_write_jsonl(
        args.tables_dir,
        args.notes_dir,
        args.character_offset_map_table,
        args.output_dir,
    )


if __name__ == "__main__":
    main()
