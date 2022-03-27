import json

import kfp
from kfp import dsl, onprem
from kubernetes.client.models import V1EnvVar

with open("pipeline/config.json", "r") as f:
    f_json = json.load(f)

    s3_config = f_json["S3"]
    s3_access_key = s3_config["access_key"]
    s3_secret_key = s3_config["secret_key"]
    s3_endpoint = f"http://{s3_config['endpoint']}:{s3_config['port']}"
    input_bucket_name = s3_config["buckets"]["input"]["name"]

    labelstudio_config = f_json["labelstudio"]
    labelstudio_export_endpoint = (
        f"http://{labelstudio_config['base_url']}:{labelstudio_config['port']}"
        f"/api/projects/{labelstudio_config['project_id']}/export"
    )


@dsl.pipeline(name="YOLO Test arcface", description="test pipeline")
def yolo_pipeline():

    load_data_1 = (
        dsl.ContainerOp(
            name="load dataset from labelstudio",
            image="gmlrhks95/mlpipeline-1-load-data",
            arguments=[
                "--labelstudio_endpoint",
                labelstudio_export_endpoint,
                "--labelstudio_token",
                labelstudio_config["token"],
                "--S3_endpoint",
                s3_endpoint,
                "--bucket",
                input_bucket_name,
                "--S3_prefix",
                "mldataset",
            ],
            file_outputs={"classes": "/data/classes.txt"},
        )
        .set_display_name("Load labelstudio dataset")
        .apply(onprem.mount_pvc("yolo-data-pvc", "yolo-data", "/data"))
        .container.add_env_variable(V1EnvVar(name="S3_ACCESS_KEY", value=s3_access_key))
        .add_env_variable(V1EnvVar(name="S3_SECRET_KEY", value=s3_secret_key))
    )

    load_conf_1 = (
        dsl.ContainerOp(
            name="load configuration from minio",
            image="gmlrhks95/mlpipeline-1-load-conf",
            arguments=[
                "--S3_endpoint",
                s3_endpoint,
                "--bucket",
                input_bucket_name,
                "--S3_prefix",
                "/model/conf",
            ],
        )
        .set_display_name("Load model configuration")
        .apply(onprem.mount_pvc("yolo-conf-pvc", "yolo-conf", "/conf"))
        .container.add_env_variable(V1EnvVar(name="S3_ACCESS_KEY", value=s3_access_key))
        .add_env_variable(V1EnvVar(name="S3_SECRET_KEY", value=s3_secret_key))
    )

    test_train_split_2 = (
        dsl.ContainerOp(
            name="Split dataset into test/train",
            image="gmlrhks95/mlpipeline-2-test-train-split",
            arguments=[
                "--classes",
                load_data_1.outputs["classes"],
            ],
        )
        .set_display_name("Split test/train dataset")
        .apply(onprem.mount_pvc("yolo-data-pvc", "yolo-data", "/data"))
    ).after(load_data_1)


if __name__ == "__main__":

    with open("pipeline/config.json", "r") as f:
        kf_config = json.load(f)["Kubeflow"]
        kf_endpoint = kf_config["endpoint"]

    client = kfp.Client(host=f"http://{kf_endpoint}")

    pipeline_name = "YOLO"
    pipeline_package_path = "YOLO_pipeline.zip"
    version = "0.141"

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
