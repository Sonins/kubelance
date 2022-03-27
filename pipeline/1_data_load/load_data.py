"""
Retrieve dataset to PersistentVolume that it uses ([/data] path.)
Retrieve annotation (label) from labelstudio.
Retrieve images from S3.
"""
import argparse
import os
import zipfile
from io import BytesIO

import requests
from boto3.session import Session
from boto3_type_annotations.s3 import Client
from requests import Response

if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser()

    argument_parser.add_argument(
        "--labelstudio_endpoint", type=str, help="labelstudio endpoint"
    )
    argument_parser.add_argument(
        "--labelstudio_token", type=str, help="labelstudio authorization token"
    )

    argument_parser.add_argument("--S3_endpoint", type=str, help="Input data S3 path")

    argument_parser.add_argument(
        "--input_bucket_name", type=str, help="Input data S3 bucket name"
    )

    argument_parser.add_argument(
        "--S3_prefix", type=str, help="Prefix of S3 object path"
    )

    args = argument_parser.parse_args()

    # Load annotations from labelstudio.

    labelstudio_endpoint = args.labelstudio_endpoint
    labelstudio_token = args.labelstudio_token

    print("Downloading Dataset..")

    res: Response = requests.get(
        url=labelstudio_endpoint,
        headers={"Authorization": f"Token {labelstudio_token}"},
        params={"exportType": "YOLO"},
    )

    res.raise_for_status()
    if res.ok:
        zipf = zipfile.ZipFile(BytesIO(res.content))
        zipf.extractall("/data")
        print(f"Downloaded: {os.listdir('/data')}")

    # Load images from S3 (Minio).

    s3_endpoint = args.S3_endpoint
    bucket_name = args.input_bucket_name
    s3_prefix = args.S3_prefix
    S3_ACCESS_KEY = os.environ["S3_ACCESS_KEY"]
    S3_SECRET_KEY = os.environ["S3_SECRET_KEY"]

    client: Client = Session().client(
        "s3",
        endpoint_url=s3_endpoint,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
    )

    image_list = client.list_objects(Bucket=bucket_name, prefix=s3_prefix)["Contents"]

    images_to_download = [
        obj["Key"]
        for obj in image_list
        if not os.path.isfile(os.path.join("/data/images", obj["Key"].split("/")[-1]))
    ]

    for obj in images_to_download:
        image_name = obj["Key"].split("/")[-1]
        target = os.path.join("/data/images", image_name)
        print(f"Downloading {obj}")
        client.download_file(bucket_name, obj, target)

    print("Download Done.")
