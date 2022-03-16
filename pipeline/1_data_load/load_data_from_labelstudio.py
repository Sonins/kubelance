"""
Retrieve dataset images from S3 to PersitentVolume that it uses. ([/data] path)
"""
import argparse
import os
import zipfile
from io import BytesIO

import requests
from requests import Response

if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser()

    argument_parser.add_argument(
        "--labelstudio_endpoint", type=str, help="labelstudio endpoint"
    )
    argument_parser.add_argument(
        "--labelstudio_token", type=str, help="labelstudio authorization token"
    )

    args = argument_parser.parse_args()

    endpoint = args.labelstudio_endpoint
    token = args.labelstudio_token

    print("Downloading Dataset..")

    res: Response = requests.get(
        url=endpoint,
        headers={"Authorization": f"Token {token}"},
        params={"exportType": "YOLO"},
    )

    res.raise_for_status()
    if res.ok:
        zipf = zipfile.ZipFile(BytesIO(res.content))
        zipf.extractall("/data")
        print("Download Done.")
        print(f"Downloaded: {os.listdir('/data')}")
