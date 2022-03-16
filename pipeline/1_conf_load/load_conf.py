import argparse
import os

from boto3 import Session

if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser()

    argument_parser.add_argument("--S3_endpoint", type=str, help="S3 endpoint")
    argument_parser.add_argument("--bucket", type=str, help="S3 bucket name")
    argument_parser.add_argument("--S3_prefix", type=str, help="S3 prefix")

    S3_access_key = os.environ["S3_ACCESS_KEY"]
    S3_secret_key = os.environ["S3_SECRET_KEY"]

    args = argument_parser.parse_args()

    session = Session()

    client = session.client(
        "s3",
        endpoint_url=args.S3_endpoint,
        aws_access_key_id=S3_access_key,
        aws_secret_access_key=S3_secret_key,
    )

    print("Downloading configuration..")
    objs = client.list_objects(Bucket=args.bucket, Prefix=args.S3_prefix)["Contents"]

    for obj in objs:
        target = os.path.join("/conf", obj["Key"].split("/")[-1])
        print(f"Downloading {obj['Key']}")
        client.download_file(args.bucket, obj["Key"], target)
