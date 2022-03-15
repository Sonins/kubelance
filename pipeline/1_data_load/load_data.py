"""
Retrieve dataset images from S3 to PersitentVolume that it uses. ([/data] path)
"""
import argparse
import os

from boto3.session import Session

if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser()

    argument_parser.add_argument("--S3_endpoint", type=str, help="Input data S3 path")

    argument_parser.add_argument(
        "--input_bucket_name", type=str, help="Input data S3 bucket name"
    )

    args = argument_parser.parse_args()

    S3_ACCESS_KEY_ID = os.environ["S3_ACCESS_KEY"]
    S3_SECRET_ACCESS_KEY = os.environ["S3_SECRET_KEY"]

    session = Session()  # boto3 session

    client = session.client(
        "s3",
        endpoint_url=args.S3_endpoint,
        aws_access_key_id=S3_ACCESS_KEY_ID,
        aws_secret_access_key=S3_SECRET_ACCESS_KEY,
    )

    print("Downloading Images..")
    os.makedirs("/data/images", exist_ok=True)

    S3_images_list = client.list_objects(
        Bucket=args.input_bucket_name, Prefix="mldataset"
    )["Contents"]

    images_to_download = [
        obj["Key"]
        for obj in S3_images_list
        if not os.path.isfile(os.path.join("/data/images", obj["Key"].split("/")[-1]))
    ]

    for obj in images_to_download:
        target = os.path.join("/data/images", obj.split("/")[-1])
        print(f"Downloading {obj}")
        client.download_file(args.input_bucket_name, obj, target)
