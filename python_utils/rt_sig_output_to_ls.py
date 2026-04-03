from collections import defaultdict
from typing import Any
from frozendict import frozendict
from more_itertools import map_reduce, one
from enum import Enum
from itertools import chain
from collections.abc import Iterable, Mapping, Collection
import argparse
import json
import os
from functools import cache, partial
import polars as pl
import logging

logger = logging.getLogger(__name__)

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s -   %(message)s",
    datefmt="%m/%d/%Y %H:%M:%S",
    level=logging.INFO,
)
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


def build_id(tag: str, file_index: int, row_index: int, annotation_index: int) -> str:
    return f"{file_index}_{tag}_{row_index}_{annotation_index}"


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
        rt_frame_to_ls_annotations(
            rt_frame=rt_frame, file_index=file_index, file_text=file_text
        )
        if rt_frame is not None
        else []
    )  # (
    #     chain.from_iterable(
    #         rt_dict_to_ls_annotations(
    #             row_dict=row_dict,
    #             file_index=file_index,
    #             row_index=row_index,
    #             file_text=file_text,
    #         )
    #         for row_index, row_dict in enumerate(rt_frame.to_dicts())
    #     )
    #     if rt_frame is not None
    #     else []
    # )

    ae_annotations = (
        chain.from_iterable(
            ae_dict_to_ls_annotations(
                row_dict=row_dict,
                file_index=file_index,
                row_index=row_index,
                file_text=file_text,
            )
            for row_index, row_dict in enumerate(ae_frame.to_dicts())
        )
        if ae_frame is not None
        else []
    )
    return {
        "id": file_index,
        "data": {"text": file_text},
        annotation_state.value: [
            {
                "id": file_index + total_files,
                "result": list(chain(ae_annotations, rt_annotations)),
            }
        ],
    }


def build_file_id_to_file_preannotation(
    rt_tables_dir: str, ae_tables_dir: str, file_id_to_file_text: Mapping[int, str]
) -> Mapping[int, Mapping[Any, Any]]:
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
    all_ids = file_id_to_rt_table.keys() | file_id_to_ae_table.keys()
    total_files = len(all_ids)

    def file_id_to_ls_annotation(file_id: int, index: int) -> Mapping[Any, Any]:
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
            file_index=index,
            total_files=total_files,
            file_text=file_id_to_file_text.get(file_id, "MISSING_FILE_TEXT"),
            annotation_state=AnnotationStage.predictions,
        )

    return {
        file_id: file_id_to_ls_annotation(file_id=file_id, index=index)
        for index, file_id in enumerate(sorted(all_ids), start=1)
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


def cui_cell_to_ls_entity(
    start: int,
    end: int,
    cui_labels: list[str],
    ls_id: str,
    origin: str,
) -> frozendict:
    return frozendict(
        {
            "value": frozendict(
                {"start": start, "end": end, "text": tuple(sorted(cui_labels))}
            ),
            "id": ls_id,
            "from_name": "CUI",
            "to_name": "text",
            "type": "textarea",
            "origin": origin,
        }
    )


def ae_cell_to_ls_entity(
    start: int, end: int, text: str | None, ls_id: str, origin: str
) -> dict:
    return cell_to_ls_entity(
        start=start,
        end=end,
        text=text,
        entity_type="labels",
        entity_labels=["Adverse Event"],
        ls_id=ls_id,
        from_name="Event",
        to_name="text",
        origin=origin,
    )


def rt_cell_to_ls_entity(
    start: int,
    end: int,
    text: str | None,
    rt_column_name: str,
    ls_id: str,
    from_name: str,
    origin: str,
) -> dict:
    return cell_to_ls_entity(
        start=start,
        end=end,
        text=text,
        entity_type="labels",
        entity_labels=[RT_COLUMN_SIGNATURE_TO_LS_SIGNATURE[rt_column_name]],
        ls_id=ls_id,
        from_name=from_name,
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
) -> frozendict:
    return frozendict(
        {
            "value": frozendict(
                {
                    "start": start,
                    "end": end,
                    "text": text,
                    entity_type: tuple(sorted(entity_labels)),
                }
            ),
            "id": ls_id,
            "from_name": from_name,
            "to_name": to_name,
            "type": entity_type,
            "origin": origin,
        }
    )


def ae_dict_to_ls_annotations(
    row_dict: Mapping[str, str],
    file_index: int,
    row_index: int,
    file_text: str,
) -> Iterable[dict]:
    ae_tag = "ae"
    current = 0
    local_build_id = partial(
        build_id, file_index=file_index, row_index=row_index, tag=ae_tag
    )
    core_event = row_dict.get("adverse_event")
    if core_event is None:
        raise ValueError("Missing core AE entity")
    offsets = parse_offset_str(core_event)
    if offsets is None:
        raise ValueError(f"Malformed offsets {offsets}")
    start, end = offsets
    text = file_text[start:end]
    yield ae_cell_to_ls_entity(
        start=start,
        end=end,
        text=text,
        ls_id=local_build_id(annotation_index=current),
        origin="prediction",
    )
    dtr = row_dict.get("dtr")
    if not isinstance(dtr, str) or dtr == "None":
        raise ValueError(f"Malformed DTR: {dtr}")
    yield dtr_cell_to_ls_entity(
        start=start,
        end=end,
        text=text,
        dtr_labels=[dtr],
        ls_id=local_build_id(annotation_index=current),
        origin="prediction",
    )
    cui = row_dict.get("cuis")
    if not isinstance(cui, str) or cui == "None":
        raise ValueError(f"Malformed CUIs: {cui}")
    yield cui_cell_to_ls_entity(
        start=start,
        end=end,
        cui_labels=cui.split("_"),
        ls_id=local_build_id(annotation_index=current),
        origin="prediction",
    )


def rt_frame_to_ls_annotations(
    rt_frame: pl.DataFrame, file_index: int, file_text: str
) -> Iterable[dict]:
    center_dose_to_signatures = {}
    non_dose_attr_columns = set(rt_frame.columns) - {"dtr", "cuis"}
    for (offset_str,), sub_table in rt_frame.group_by("central_dose"):
        result = {}
        dtrs = set(sub_table["dtr"].to_list())
        try:
            result["dtr"] = [one(dtrs)]
        except Exception:
            ValueError(f"Inconsistent dtr values {dtrs}")
        cuis = set(sub_table["cuis"].to_list())
        try:
            raw = one(cuis)
            result["cuis"] = (
                ["C1522449"] if raw is None or raw != "None" else raw.split("_")
            )
        except Exception:
            ValueError(f"Inconsistent cuis values {cuis}")
        center_dose_offsets = parse_offset_str(offset_str)
        if center_dose_offsets is None:
            raise ValueError(f"Malformed center dose offsets: {offset_str}")
        for column in non_dose_attr_columns:
            vals = {
                parse_offset_str(val)
                for val in set(sub_table[column].to_list())
                if val != "None" and val is not None
            }
            try:
                offsets = one(
                    vals,
                    too_long=ValueError,
                    too_short=IndexError,
                )
            except ValueError:
                logger.error(
                    "Bad values for column %s: %s - Selecting element closest to center dose",
                    column,
                    ", ".join(map(str, sorted(vals))),
                )
                offsets = min(vals, key=lambda s: abs(s[0] - center_dose_offsets[0]))
            except IndexError:
                offsets = None
            if offsets is not None:
                result[column] = offsets
        center_dose_to_signatures[center_dose_offsets] = result
    for signatures in center_dose_to_signatures.values():
        secondary_dose = signatures.get("secondary_dose")
        if (
            secondary_dose is not None
            and secondary_dose not in center_dose_to_signatures.keys()
        ):
            raise ValueError(
                f"Secondary dose offsets {secondary_dose} not found among center dose offsets {sorted(center_dose_to_signatures.keys())}"
            )

    dose_offsets_to_annotations = defaultdict(set)
    offsets_and_type_to_index = {
        offsets_and_type: idx
        for idx, offsets_and_type in enumerate(
            sorted(
                set(
                    chain(
                        {(k, "central_dose") for k in center_dose_to_signatures.keys()},
                        (
                            (v, k)
                            for _val in center_dose_to_signatures.values()
                            for k, v in _val.items()
                            if k not in {"dtr", "cuis", "secondary_dose"}
                        ),
                    )
                )
            )
        )
    }
    for offsets in center_dose_to_signatures.keys():
        start, end = offsets
        dose_offsets_to_annotations[offsets].add(
            rt_cell_to_ls_entity(
                start=start,
                end=end,
                text=file_text[start:end],
                rt_column_name="central_dose",
                ls_id=f"{file_index}_rt_{offsets_and_type_to_index.get((offsets, 'central_dose'), 'ERROR')}",
                from_name="Event",
                origin="prediction",
            )
        )
    signature_pairs = set()
    dose_dose_pairs = set()
    signature_offsets_to_annotation = defaultdict(set)
    for center_dose_offsets, value_dict in center_dose_to_signatures.items():
        center_dose_id = f"{file_index}_rt_{offsets_and_type_to_index.get((center_dose_offsets, 'central_dose'), 'ERROR')}"
        center_dose_start, center_dose_end = center_dose_offsets
        secondary_dose = value_dict.get("secondary_dose")
        if secondary_dose is not None:
            if secondary_dose not in dose_offsets_to_annotations.keys():
                raise ValueError(
                    f"Secondary dose offsets {value_dict['secondary_dose']} not found among center dose offsets {sorted(dose_offsets_to_annotations.keys())}"
                )
            secondary_dose_id = f"{file_index}_rt_{offsets_and_type_to_index.get((secondary_dose, 'central_dose'), 'ERROR')}"
            dose_dose_pairs.add(
                (
                    center_dose_id,
                    secondary_dose_id,
                )
            )
        if value_dict.get("dtr") is None:
            raise ValueError(f"{center_dose_offsets} missing DTR")
        dose_offsets_to_annotations[center_dose_offsets].add(
            dtr_cell_to_ls_entity(
                start=center_dose_start,
                end=center_dose_end,
                text=file_text[center_dose_start:center_dose_end],
                dtr_labels=value_dict["dtr"],
                ls_id=center_dose_id,
                origin="prediction",
            )
        )

        if value_dict.get("cuis") is None:
            raise ValueError(f"{center_dose_offsets} missing CUIs")
        dose_offsets_to_annotations[center_dose_offsets].add(
            cui_cell_to_ls_entity(
                start=center_dose_start,
                end=center_dose_end,
                cui_labels=value_dict["cuis"],
                ls_id=center_dose_id,
                origin="prediction",
            )
        )
        for signature_name in value_dict.keys() - {
            "dtr",
            "cuis",
            "secondary_dose",
            "central_dose",
        }:
            signature_offsets = value_dict.get(signature_name)
            if signature_offsets is not None:
                signature_start, signature_end = signature_offsets
                ls_id = f"{file_index}_rt_{offsets_and_type_to_index.get((signature_offsets, signature_name), 'ERROR')}"
                ls_entity = rt_cell_to_ls_entity(
                    start=signature_start,
                    end=signature_end,
                    text=file_text[signature_start:signature_end],
                    rt_column_name=signature_name,
                    ls_id=ls_id,
                    from_name="RadiotherapySignature",
                    origin="prediction",
                )
                signature_offsets_to_annotation[signature_offsets].add(ls_entity)
                signature_pairs.add(
                    (
                        center_dose_id,
                        ls_id,
                    )
                )
    for v in dose_offsets_to_annotations.values():
        assert len(v) == 3, v
        for elem in v:
            yield elem
    for v in signature_offsets_to_annotation.values():
        # assert len(v) == 1, v
        for elem in v:
            yield elem

    def id_key(ls_id: str) -> int:
        last = ls_id.split("_")[-1]
        if not last.isnumeric():
            raise ValueError(f"Bad LS ID: {ls_id}")
        return int(last)

    for signature_pair in signature_pairs:
        anchor, signature = signature_pair
        yield entities_to_relation(
            from_id=anchor,
            to_id=signature,
            direction="right" if id_key(anchor) <= id_key(signature) else "left",
        )

    for dose_dose_pair in dose_dose_pairs:
        anchor, signature = dose_dose_pair
        yield entities_to_relation(
            from_id=anchor,
            to_id=signature,
            labels=["SecondaryDose"],
            direction="right" if id_key(anchor) <= id_key(signature) else "left",
        )


def rt_dict_to_ls_annotations(
    row_dict: Mapping[str, str],
    file_index: int,
    row_index: int,
    file_text: str,
    anchor_column: str = "central_dose",
) -> Iterable[dict]:
    current = 0
    rt_tag = "rt"
    fixed_row_dict = {}
    local_build_id = partial(
        build_id, file_index=file_index, row_index=row_index, tag=rt_tag
    )
    for raw_column, raw_cell in row_dict.items():
        column = raw_column.strip()
        if raw_cell != "None":
            match column:
                case "dtr":
                    fixed_row_dict[column] = [raw_cell]
                case "cuis":
                    fixed_row_dict[column] = (
                        ["C1522449"] if raw_cell is None else raw_cell.split("_")
                    )
                case _:
                    offsets = parse_offset_str(raw_cell)
                    fixed_row_dict[column] = offsets
    # if file_index == 3:
    #     raise ValueError(fixed_row_dict)

    def build_ls_entity(
        column_name: str,
        ls_id: str,
        from_name: str = "Event",
        origin: str = "prediction",
    ) -> dict:
        match column_name:
            case "dtr":
                start = fixed_row_dict[anchor_column][0]
                end = fixed_row_dict[anchor_column][1]
                text = file_text[start:end]
                return dtr_cell_to_ls_entity(
                    start=start,
                    end=end,
                    text=text,
                    dtr_labels=fixed_row_dict[column_name],
                    ls_id=ls_id,
                    origin=origin,
                )
            case "cuis":
                start = fixed_row_dict[anchor_column][0]
                end = fixed_row_dict[anchor_column][1]
                return cui_cell_to_ls_entity(
                    start=start,
                    end=end,
                    cui_labels=fixed_row_dict[column_name],
                    ls_id=ls_id,
                    origin=origin,
                )
            case _:
                start = fixed_row_dict[column_name][0]
                end = fixed_row_dict[column_name][1]
                text = file_text[start:end]
                return rt_cell_to_ls_entity(
                    start=start,
                    end=end,
                    text=text,
                    rt_column_name=column_name,
                    ls_id=ls_id,
                    from_name=from_name,
                    origin=origin,
                )

    anchor_id = local_build_id(annotation_index=current)
    dtr_column = "dtr"
    cui_column = "cuis"
    anchor_entity = build_ls_entity(anchor_column, anchor_id, from_name="Event")
    dtr_entity = build_ls_entity(dtr_column, anchor_id)
    cuis_entity = build_ls_entity(cui_column, anchor_id)
    current += 1
    id_to_signature = {}
    for signature_column in fixed_row_dict.keys() - {
        anchor_column,
        dtr_column,
        cui_column,
    }:
        signature_id = local_build_id(annotation_index=current)
        id_to_signature[signature_id] = build_ls_entity(
            signature_column, signature_id, from_name="RadiotherapySignature"
        )
        current += 1
    relations = (
        entities_to_relation(
            from_id=anchor_id,
            to_id=signature_id,
            direction="right"
            if anchor_entity["value"]["start"]
            <= id_to_signature[signature_id]["value"]["start"]
            else "left",
        )
        for signature_id in id_to_signature.keys()
    )
    return chain(
        (anchor_entity, dtr_entity, cuis_entity), id_to_signature.values(), relations
    )


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
