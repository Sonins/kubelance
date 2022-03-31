# Calculating Anchors

Refer [pipeline.py](../pipeline.py).  
3_calc_anchors node is made using darknet image.

```python
calc_anchors_3 = (
    dsl.ContainerOp(
        name="Calculate anchors from data.",
        image="daisukekobayashi/darknet:cpu-noopt",
        arguments=[
            "sh",
            "-c",
            "darknet detector calc_anchors $DATA_PATH -num_of_clusters $CLUSTER_NUM -width $WIDTH -height $HEIGHT -dont_show && mv anchors.txt /data",
        ],
    )
    .set_display_name("Calculate anchors")
    .apply(onprem.mount_pvc("yolo-data-pvc", "yolo-data", "/data"))
).after(test_train_split_2)

calc_anchors_3.container.add_env_variable(
    V1EnvVar(name="DATA_PATH", value="/data/obj.data")
).add_env_variable(V1EnvVar(name="CLUSTER_NUM", value=9))\
.add_env_variable(V1EnvVar(name="WIDTH", value=416))\
.add_env_variable(V1EnvVar(name="HEIGHT", value=416))\
.add_env_variable(V1EnvVar(name="OUTPUT_PATH", value="/data/anchors.txt"))
```