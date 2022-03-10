import json

import kfp
from kfp import dsl, onprem
from kubernetes.client.models import V1EnvVar

with open("pipeline/config.json", "r") as f:
    config = json.load(f)["S3"]
    access_key = config["access_key"]
    secret_key = config["secret_key"]
    endpoint = f"http://{config['endpoint']}:{config['port']}"
    input_bucket_name = config["buckets"]["input"]["name"]


@dsl.pipeline(name="YOLO Test arcface", description="test pipeline")
def yolo_pipeline():

    load_data_1 = (
        dsl.ContainerOp(
            name="load image dataset from S3",
            image="gmlrhks95/mlpipeline-1-load-data",
            arguments=[
                "--S3_endpoint",
                endpoint,
                "--input_bucket_name",
                input_bucket_name,
            ],
        )
        .set_display_name("load data")
        .apply(onprem.mount_pvc("yolo-data-pvc", "yolo-data", "/data"))
        .container.add_env_variable(V1EnvVar(name="S3_ACCESS_KEY", value=access_key))
        .add_env_variable(V1EnvVar(name="S3_SECRET_KEY", value=secret_key))
    )


if __name__ == "__main__":
    client = kfp.Client(host="http://localhost:3000")

    pipeline_name = "YOLO"
    pipeline_package_path = "YOLO_pipeline.zip"
    version = "0.12"

    kfp.compiler.Compiler().compile(yolo_pipeline, pipeline_package_path)

    # If exist, then update. If not, create.
    pipeline_id = client.get_pipeline_id(pipeline_name)

    if pipeline_id:
        client.upload_pipeline_version(
            pipeline_package_path=pipeline_package_path,
            pipeline_version_name=version,
            pipeline_name=pipeline_name,
        )
    else:
        client.upload_pipeline(
            pipeline_package_path=pipeline_package_path, pipeline_name=pipeline_name
        )
