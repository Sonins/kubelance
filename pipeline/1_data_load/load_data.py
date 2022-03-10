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

    session = Session()

    client = session.client(
        "s3",
        endpoint_url=args.S3_endpoint,
        aws_access_key_id=S3_ACCESS_KEY_ID,
        aws_secret_access_key=S3_SECRET_ACCESS_KEY,
    )

    os.makedirs("/data/images", exist_ok=True)

    for object in client.list_objects(
        Bucket=args.input_bucket_name, Prefix="mldataset"
    )["Contents"]:
        target = os.path.join("/data/images", object["Key"].split("/")[-1])
        if os.path.exists(target):
            print(f"{object['Key']} is already exists")
        else:
            print(f"Downloading {object['Key']}")
            client.download_file(args.input_bucket_name, object["Key"], target)
