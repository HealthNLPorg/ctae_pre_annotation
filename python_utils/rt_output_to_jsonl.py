import argparse
import json
import os
import polars as pl
from typing import Mapping

parser = argparse.ArgumentParser(description="")

parser.add_argument(
    "--tables_dir",
    type=str,
    help="Directory containing offset tables for extracted RT signature mentions",
)

parser.add_argument(
    "--notes_dir",
    type=str,
    help="Directory containing the original notes",
)
parser.add_argument(
    "--output_dir",
    type=str,
    help="Where to store the JSONL for the corpus",
)


def table_file_to_file_preannotation(table_file: str) -> dict:
    # Remove straggler rows where all cells are null
    rt_frame = pl.read_csv(table_file).filter(~pl.all_horizontal(pl.all().is_null()))
    NotImplementedError("Parse table")
    return {}


def build_file_id_to_file_preannotation(tables_dir: str) -> Mapping[int, dict]:
    def __file_id(fn: str) -> int:
        return int(fn.split("_")[0])

    return {
        __file_id(table_fn): table_file_to_file_preannotation(
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

    return [
        __assemble(file_id)
        for file_id in sorted(
            file_id_to_file_text.keys() | file_id_to_file_preannotation.keys()
        )
        if __assemble(file_id) is not None
    ]


def build_and_write_jsonl(tables_dir: str, notes_dir: str, output_dir: str) -> None:
    file_id_to_file_text = build_file_id_to_file_text(notes_dir)
    file_id_to_file_preannotation = build_file_id_to_file_preannotation(tables_dir)
    with open(os.path.join(output_dir, "label_studio_corpus.json"), mode="w") as f:
        f.write(
            json.dumps(build_jsonl(file_id_to_file_text, file_id_to_file_preannotation))
        )


def main() -> None:
    args = parser.parse_args()
    build_and_write_jsonl(args.tables_dir, args.notes_dir, args.output_dir)


if __name__ == "__main__":
    main()
