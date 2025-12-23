import argparse
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
