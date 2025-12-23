import argparse
from functools import partial, lru_cache
import polars as pl

parser = argparse.ArgumentParser(description="")

parser.add_argument(
    "--sig_offsets_dir",
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


def ctakes_csv_to_ls_file_annotation(csv_path: str) -> dict:
    return {}


def get_offset_map_from_string(offset_map_string: str) -> dict[int, int]:
    NotImplementedError("Just a second")
    return {}


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
            final[signature] = offsets
    return final


def get_report_id_to_offset_map(
    character_offset_map_table: str, report_id_col_key: str, offset_map_col_key: str
) -> dict[int, dict[int, int]]:
    df = pl.read_csv(character_offset_map_table, separator="\t")
    return {
        int(report_id): get_offset_map_from_string(offset_map_string)
        for report_id, offset_map_string in zip(
            df[report_id_col_key], df[offset_map_col_key]
        )
    }


def aggregate_and_align(
    sig_offsets_dir: str, character_offset_map_table: str, output_dir: str
) -> None:
    pass


def main() -> None:
    args = parser.parse_args()
    aggregate_and_align(
        args.sig_offsets_dir, args.character_offset_map_table, args.output_dir
    )


if __name__ == "__main__":
    main()
