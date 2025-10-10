import json
import os
import argparse
from collections.abc import Iterable

parser = argparse.ArgumentParser(description="")

parser.add_argument(
    "--json_dir",
    type=str,
    help="Where the cTAKES output is",
)

parser.add_argument(
    "--output_dir",
    type=str,
    help="Where to write the full aggregated JSON",
)


def get_json_dicts(json_dir: str) -> Iterable[dict]:
    for fn in os.listdir(json_dir):
        if fn.endswith("json"):
            with open(os.path.join(json_dir, fn), mode="r") as f:
                yield json.loads(f.read())


def aggregate_and_align(json_dir: str, output_dir: str, debug_n: int = 3) -> None:
    json_dicts = list(get_json_dicts(json_dir))
    nu_start = 0
    for idx, json_dict in enumerate(json_dicts, 1):
        json_dict["id"] = idx
        nu_start = idx
    for idx, json_dict in enumerate(json_dicts, nu_start + 1):
        # print(json_dict)
        json_dict["predictions"][0]["id"] = idx

    with open(os.path.join(output_dir, "full.json"), mode="w") as f:
        f.write(json.dumps(json_dicts))

    with open(os.path.join(output_dir, "full.json"), mode="w") as f:
        f.write(json.dumps(json_dicts))

    first_n = json_dicts[:debug_n]
    for idx, json_dict in enumerate(first_n, 1):
        json_dict["id"] = idx
        nu_start = idx
    for idx, json_dict in enumerate(first_n, nu_start + 1):
        # print(json_dict)
        json_dict["predictions"][0]["id"] = idx

    with open(os.path.join(output_dir, f"first_{debug_n}.json"), mode="w") as f:
        f.write(json.dumps(first_n))


def main() -> None:
    args = parser.parse_args()
    aggregate_and_align(args.json_dir, args.output_dir)


if __name__ == "__main__":
    main()
