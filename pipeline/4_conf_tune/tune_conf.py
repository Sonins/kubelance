import argparse
import json
from io import FileIO
from typing import Dict, Iterable


def read_config(filepath: str) -> Iterable[Dict]:
    with open(filepath, "r") as f:
        lines = [
            line.strip()
            for line in f.readlines()
            if line.strip() and not line.startswith("#")
        ]
    config = []
    for line in lines:
        if line.startswith("["):  # If line defines type of the block
            config.append({})
            block = config[-1]
            block["type"] = line[1:-1].rstrip()
            continue

        key, value = line.split("=")
        value = value.strip()
        if all(
            i.isdigit() or i == "." for i in value
        ):  # Store numeric value in numeric type.
            if any(i == "." for i in value):
                value = float(value)
            else:
                value = int(value)
        block[key.strip()] = value

    return config


def read_anchors(filepath: str) -> str:
    with open(filepath) as f:
        anchors = f.readline()
    return anchors.strip()


def build_parameters(
    num_classes: int,
    batches: int,
    subdivisions: int,
    img_size: int,
    anchors: str,
    other_args: Dict,
):
    param = {}
    param["num_classes"] = num_classes
    param["batches"] = batches
    param["subdivisions"] = subdivisions
    param["img_size"] = img_size
    param["anchors"] = anchors
    param.update(other_args)
    return param


def modify_config(config: Iterable[Dict], parameters: Dict) -> Iterable[Dict]:

    num_classes = parameters["num_classes"]
    batches = parameters["batches"]
    subdivisions = parameters["subdivisions"]
    img_size = parameters["img_size"]
    anchors = parameters["anchors"]

    prev_block = config[0]

    for block in config:
        if block["type"] == "net":
            net_block = block
            continue

        if block["type"] == "yolo":
            prev_block["filters"] = (num_classes + 5) * 3
            block["anchors"] = anchors
            block["classes"] = num_classes

        prev_block = block

    net_block["batch"] = batches
    net_block["subdivisions"] = subdivisions
    net_block["width"] = img_size
    net_block["height"] = img_size
    net_block["max_batches"] = num_classes * 2000
    net_block[
        "steps"
    ] = f"{int(net_block['max_batches'] * 0.8)}, {int(net_block['max_batches'] * 0.9)}"


def save_config(
    config: Iterable[Dict],
    filepath: str,
):
    with open(filepath, "w") as f:
        for block in config:
            __write_config_block_in_file(f, block)
            f.write("\n")


def __write_config_block_in_file(file: FileIO, block: Dict):
    file.write(f"[{block['type']}]\n")
    for k, v in block.items():
        if k == "type":
            continue
        file.write(f"{k}={v}\n")


if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser()

    argument_parser.add_argument("--classes", type=str, help="Classes of object")
    argument_parser.add_argument(
        "--batches", type=int, help="Count of batch train", default=1
    )
    argument_parser.add_argument(
        "--subdivisions", type=int, help="Subdivision in yolo conf", default=1
    )
    argument_parser.add_argument(
        "--img_size", type=int, help="width or height of image (square)", default=416
    )
    argument_parser.add_argument(
        "--json_args",
        type=json.loads,
        help="Other argument in json format",
        default="{}",
    )

    argument_parser.add_argument(
        "--config_filename", type=str, help="Yolo configuration file"
    )

    args = argument_parser.parse_args()
    config_filepath = f"/conf/{args.config_filename}"
    anchor_filepath = "/data/anchors.txt"
    num_classes = len(args.classes.split())

    config = read_config(filepath=config_filepath)
    anchors = read_anchors(anchor_filepath)

    parameters = build_parameters(
        num_classes,
        args.batches,
        args.subdivisions,
        args.img_size,
        anchors,
        other_args=args.json_args,
    )

    modify_config(config, parameters)
    save_config(config, config_filepath)
