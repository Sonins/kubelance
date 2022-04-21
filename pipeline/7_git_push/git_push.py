import argparse
import shutil
from datetime import datetime

from git.repo import Repo
from pytz import timezone

PATH = r"/conf"


def generate_commitmsg() -> str:
    now = datetime.now(timezone("Asia/Seoul"))
    return f"New weight updated ({now.strftime('%y/%m/%d %H:%M')})"


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("--src_weight", type=str, help="Path of source weight")
    parser.add_argument("--dest_weight", type=str, help="Path of target weight")

    args = parser.parse_args()

    shutil.move(args.src_weight, args.dest_weight)

    with Repo(PATH) as repo:
        repo.git.add(update=True)
        repo.index.commit(generate_commitmsg())
        origin = repo.remotes.origin
        origin.push()
