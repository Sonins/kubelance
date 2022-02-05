import json
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow import DAG
from datetime import datetime

args = {
    "owner": "admin",
    "email": ["gmlrhks95@gmail.com"],
    "email_on_failure": True,
}

dag = DAG(
    dag_id="sync_storage",
    default_args=args,
    schedule_interval="0 0 * * *",
    start_date=datetime.now().replace(
        hour=0, minute=0, second=0, microsecond=0
    ),
    tags=["labelstudio", "mlops"]
)

getExportStorages = SimpleHttpOperator(
    task_id="get_export_storages",
    endpoint="/api/storages/export/s3",
    method="GET",
    http_conn_id="labelstudio_conn",
    do_xcom_push=True,
    dag=dag,
)

for num, stor in enumerate(getExportStorages.output):
    syncExportStorage = SimpleHttpOperator(
        task_id=f"sync_export_storage_{num}",
        endpoint=f"/api/storages/export/s3/{stor['id']}/sync",
        method="POST",
        data={
            "project": stor['project'],
            "bucket": stor['bucket'],
            "aws_access_key_id": stor['aws_access_key_id'],
            "aws_secret_access_key": stor['aws_secret_access_key'],
        },
        http_conn_id="labelstudio_conn",
        dag=dag,
    )
    getExportStorages >> syncExportStorage
    