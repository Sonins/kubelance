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

    s3_input_bucket = s3_config["buckets"]["input"]
    input_bucket_name = s3_input_bucket["name"]
    dataset_prefix = s3_input_bucket["prefix"]["dataset"]

    s3_conf_bucket = s3_config["buckets"]["conf"]
    conf_bucket_name = s3_conf_bucket["name"]
    conf_prefix = s3_conf_bucket["prefix"]

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
                dataset_prefix,
            ],
            file_outputs={"classes": "/data/classes.txt"},
        )
        .set_display_name("Load labelstudio dataset")
        .apply(onprem.mount_pvc("yolo-data-pvc", "yolo-data", "/data"))
    )

    load_data_1.container\
        .add_env_variable(V1EnvVar(name="S3_ACCESS_KEY", value=s3_access_key))\
        .add_env_variable(V1EnvVar(name="S3_SECRET_KEY", value=s3_secret_key))

    load_conf_1 = (
        dsl.ContainerOp(
            name="load configuration from minio",
            image="gmlrhks95/mlpipeline-1-load-conf",
            arguments=[
                "--repo_url",
                conf_git_url,
            ],
            file_outputs={
                "conf_file_name": "/tmp/output/cfg",
                "weight_file_name": "/tmp/output/weight",
                "output_weight_file_name": "/tmp/output/output_weight"
            },
        )
        .set_display_name("Load model configuration")
        .apply(onprem.mount_pvc("yolo-conf-pvc", "yolo-conf", "/conf"))        
    )

    load_conf_1.container.add_env_variable(
        V1EnvVar(name="S3_ACCESS_KEY", value=s3_access_key)
    ).add_env_variable(V1EnvVar(name="S3_SECRET_KEY", value=s3_secret_key))

    model = load_conf_1.outputs['conf_file_name']
    weight = load_conf_1.outputs['weight_file_name']
    output_weight = load_conf_1.outputs['output_weight_file_name']

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

    calc_anchors_3 = (
        dsl.ContainerOp(
            name="Calculate anchors from data.",
            image="daisukekobayashi/darknet:cpu-noopt",
            arguments=[
                "sh",
                "-c",
                "darknet detector calc_anchors $DATA_PATH -num_of_clusters $CLUSTER_NUM -width $WIDTH -height $HEIGHT -dont_show && mv anchors.txt /data",
            ],
            file_outputs={"anchors": "/data/anchors.txt"}
        )
        .set_display_name("Calculate anchors")
        .apply(onprem.mount_pvc("yolo-data-pvc", "yolo-data", "/data"))
    ).after(test_train_split_2)

    calc_anchors_3.container.add_env_variable(
        V1EnvVar(name="DATA_PATH", value="/data/obj.data")
    ).add_env_variable(V1EnvVar(name="CLUSTER_NUM", value=9)).add_env_variable(
        V1EnvVar(name="WIDTH", value=416)
    ).add_env_variable(
        V1EnvVar(name="HEIGHT", value=416)
    ).add_env_variable(
        V1EnvVar(name="OUTPUT_PATH", value="/data/anchors.txt")
    )

    conf_tune_4 = (
        dsl.ContainerOp(
            name="Modify and tune configuration accordingly.",
            image="gmlrhks95/mlpipeline-4-conf-tune",
            arguments=[
                "--classes",
                load_data_1.outputs["classes"],
                "--batches",
                "16",
                "--subdivision",
                "4",
                "--img_size",
                "416",
                "--config_filename",
                model,
                "--anchors",
                calc_anchors_3.outputs["anchors"]
            ],
        )
        .set_display_name("Tuning configuration")
        .apply(onprem.mount_pvc("yolo-data-pvc", "yolo-data", "/data"))
        .apply(onprem.mount_pvc("yolo-conf-pvc", "yolo-conf", "/conf"))
    ).after(calc_anchors_3, load_conf_1)

    train_5 = (
        dsl.ContainerOp(
            name="Train",
            image="daisukekobayashi/darknet:cpu-noopt",
            arguments=[
                "sh",
                "-c",
                (
                "darknet detector train /data/obj.data "
                f"/conf/{model} "
                f"/conf/{weight} -map -dont_show "
                ),
                f"&& cp /data/output/{output_weight} /conf/{weight}",
            ],
        )
        .set_display_name("Train yolo")
        .apply(onprem.mount_pvc("yolo-data-pvc", "yolo-data", "/data"))
        .apply(onprem.mount_pvc("yolo-conf-pvc", "yolo-conf", "/conf"))
    ).after(conf_tune_4)

    validation_6 = (
        dsl.ContainerOp(
            name="Validation",
            image="daisukekobayashi/darknet:cpu",
            command=[
                "sh",
                "-c",
                (
                "darknet detector test /data/obj.data"
                f" /conf/{model}"
                f" /conf/{weight}"
                ),
            ]
        )
        .set_display_name("Validate")
        .apply(onprem.mount_pvc("yolo-data-pvc", "yolo-data", "/data"))
        .apply(onprem.mount_pvc("yolo-conf-pvc", "yolo-conf", "/conf"))
    ).after(train_5)

    deploy_6 = (
        dsl.ContainerOp(
            name="Deploy new weight",
            image="gmlrhks95/mlpipeline-7-git-push",
            command=['python', 'git_push.py'],
            arguments=[
                "--src_weight",
                f"/data/output/{output_weight}",
                "--dest_weight",
                f"/conf/{weight}"
            ],
        )
        .set_display_name("Deploy to git")
        .apply(onprem.mount_pvc("yolo-data-pvc", "yolo-data", "/data"))
        .apply(onprem.mount_pvc("yolo-conf-pvc", "yolo-conf", "/conf"))
    ).after(train_5)

if __name__ == "__main__":

    with open("pipeline/config.json", "r") as f:
        kf_config = json.load(f)["Kubeflow"]
        kf_endpoint = kf_config["endpoint"]

    client = kfp.Client(host=f"http://{kf_endpoint}")

    pipeline_name = "YOLO"
    pipeline_package_path = "YOLO_pipeline.zip"
    version = "0.15"

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
