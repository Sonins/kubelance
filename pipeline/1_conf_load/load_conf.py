import argparse
import os
import shutil
from pathlib import Path

import git
from git.repo import Repo

PATH = r"/tmp/git"


def return_filenames(cfg: str, weight: str):
    os.makedirs("/tmp/output", exist_ok=True)
    with open("/tmp/output/cfg", "w") as f:
        f.write(cfg)

    with open("/tmp/output/output_weight", "w") as f:
        f.write(f"{cfg.split('.')[0]}_best.weights")

    # Returning weight file name.
    with open("/tmp/output/weight", "w") as f:
        f.write(weight)


if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser()

    argument_parser.add_argument("--repo_url", type=str, help="git repo url")

    args = argument_parser.parse_args()

    print("Downloading configuration..")

    os.makedirs(PATH, exist_ok=True)

    try:
        repo = Repo(PATH)
        repo.remotes.origin.pull()
        repo.git.reset("--hard", "origin/master")
    except git.exc.InvalidGitRepositoryError:
        print(f"{PATH} is not git repo, try cloning..")
        try:
            repo = Repo.clone_from(args.repo_url, PATH)
        except git.exc.InvalidGitRepositoryError:
            print("Cloning failed.")

    conf = list(Path(PATH).glob("*.cfg"))[0]
    weight = list(Path(PATH).glob("*.weights"))[0]

    conf = str(conf).split("/")[-1]
    weight = str(weight).split("/")[-1]

    return_filenames(conf, weight)

    for file in os.listdir(PATH):
        shutil.move(os.path.join(PATH, file), os.path.join(r"/conf", file))
