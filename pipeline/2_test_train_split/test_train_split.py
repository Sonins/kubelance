import argparse
import random
from pathlib import Path
from typing import Dict, Iterable, Tuple, Union

IDEAL_RATIO = 0.8
ITERATE_TIL_IDEAL = 10

# (label_dir, image_dir, target_dir)
DEV_DIRS = (r"./test/labels", r"./test/images", r"./test")
PROD_DIRS = (r"/data/labels", r"/data/images", r"/data")


def _vector_sum(vec: Iterable[Union[float, int]]) -> Iterable[Union[float, int]]:
    return [sum(x) for x in zip(*vec)]


def _split_test_train(
    label_list: Iterable[str],
    class_count_over_files: Dict,
) -> Tuple[Iterable[str], float]:
    train_labels = random.sample(label_list, round(IDEAL_RATIO * len(label_list)))

    train_classes_sum = _vector_sum([class_count_over_files[x] for x in train_labels])
    total_classes_sum = _vector_sum(class_count_over_files.values())

    ratio = 0
    count = 0

    for train, total in zip(train_classes_sum, total_classes_sum):
        if total == 0:
            continue
        count += 1
        ratio += train / total

    if count != 0:
        ratio /= count
    else:
        ratio = 0

    return train_labels, ratio


if __name__ == "__main__":

    # Parse argument
    argument_parser = argparse.ArgumentParser()

    argument_parser.add_argument("--classes", type=str, help="List of dataset classes")

    argument_parser.add_argument(
        "--development",
        help="Indicates if runtime is development",
        action="store_true",
        default=False,
    )

    args = argument_parser.parse_args()

    if args.development:
        LABEL_DIR, IMAGE_DIR, TARGET_DIR = DEV_DIRS
    else:
        LABEL_DIR, IMAGE_DIR, TARGET_DIR = PROD_DIRS

    classes = args.classes.split()
    num_classes = len(classes)

    # Write .data and .names file for yolo train
    # TODO: It may need to be in seperate file. (2_write_obj_file)
    with open(f"{TARGET_DIR}/obj.data", "w") as f:
        f.write(f"classes = {num_classes}\n")
        f.write(f"train = {TARGET_DIR}/train.txt\n")
        f.write(f"test = {TARGET_DIR}/test.txt\n")
        f.write(f"names = {TARGET_DIR}/obj.names\n")
        f.write(f"backup = {TARGET_DIR}/output")

    with open(f"{TARGET_DIR}/obj.names", "w") as f:
        f.writelines("\n".join([cl for cl in classes]))

    # Load label files and count number of each classes
    Path(f"{TARGET_DIR}/output").mkdir(exist_ok=True)
    Path(f"{TARGET_DIR}/train.txt").touch()
    Path(f"{TARGET_DIR}/test.txt").touch()

    class_count_over_files = {}
    label_exists = []

    with open(f"{TARGET_DIR}/train.txt", "r") as f:
        label_exists.extend([Path(line.strip()).stem for line in f.readlines()])

    with open(f"{TARGET_DIR}/test.txt", "r") as f:
        label_exists.extend([Path(line.strip()).stem for line in f.readlines()])

    label_files = Path(LABEL_DIR).rglob("*.txt")
    for file in label_files:
        if file.stem in label_exists:
            continue

        count = [0] * num_classes

        with file.open() as f:
            labels = f.readlines()

        for label in labels:
            label = label.strip()
            count[int(label.split(" ")[0])] += 1

        file.rename(f"{IMAGE_DIR}/{file.stem}{file.suffix}")
        class_count_over_files[file.stem] = count

    # Split test/train and save train which is ratio closest to ideal.
    label_list = class_count_over_files.keys()
    ratio_difference = 1
    result_train = []
    result_ratio = 0

    for i in range(ITERATE_TIL_IDEAL):
        train, ratio = _split_test_train(
            label_list=label_list, class_count_over_files=class_count_over_files
        )

        if ratio_difference > abs(IDEAL_RATIO - ratio):
            result_train = train
            result_ratio = ratio
            ratio_difference = abs(IDEAL_RATIO - ratio)

    # Write train.txt and test.txt accordingly.
    train = result_train
    test = [x for x in label_list if x not in train]

    extensions = ("png", "jpg", "jpeg")
    path_list = [Path(IMAGE_DIR).rglob(f"*.{ext}") for ext in extensions]

    files = []
    for p in path_list:
        files.extend(p)

    train_file_list = [
        f"{IMAGE_DIR}/{f.stem}{f.suffix}" for f in files if f.stem in train
    ]
    test_file_list = [
        f"{IMAGE_DIR}/{f.stem}{f.suffix}" for f in files if f.stem in test
    ]

    if train_file_list:
        with open(f"{TARGET_DIR}/train.txt", "a+") as f:
            f.writelines("\n".join(train_file_list))
            f.write("\n")

    if test_file_list:
        with open(f"{TARGET_DIR}/test.txt", "a") as f:
            f.writelines("\n".join(test_file_list))
            f.write("\n")

    print("New dataset: ")
    print(f"total dataset: {list(class_count_over_files.keys())}")
    print(f"training dataset: {train}")
    print(f"test dataset: {test}")
    print(f"train / total ratio: {result_ratio}")
