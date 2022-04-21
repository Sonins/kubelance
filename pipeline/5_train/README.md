# Train

Refer [pipeline.py](../pipeline.py).  
5_train node is made using darknet image.

```python
    train_5 = (
        dsl.ContainerOp(
            name="Train",
            image="daisukekobayashi/darknet:gpu-cv-cc75",
            command=[
                "sh",
                "-c",
                (
                    "darknet detector train /data/obj.data "
                    f"/conf/{model} "
                    f"/conf/{weight} -map -dont_show "
                ),
                f"&& cp --verbose /data/output/{output_weight} /conf/{weight}",
            ],
        )
        .set_display_name("Train yolo")
        .apply(onprem.mount_pvc("yolo-data-pvc", "yolo-data", "/data"))
        .apply(onprem.mount_pvc("yolo-conf-pvc", "yolo-conf", "/conf"))
        .set_gpu_limit(1)
    ).after(conf_tune_4)
```
