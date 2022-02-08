from datetime import datetime

from airflow.decorators import task
from airflow.providers.http.hooks.http import HttpHook
from airflow.providers.http.operators.http import SimpleHttpOperator
from pendulum.tz import timezone

from airflow import DAG

args = {
    "owner": "admin",
    "email": ["gmlrhks95@gmail.com"],
    "email_on_failure": True,
}


@task()
def get_storages(
    projects,
    http_conn_id: str,
):
    import json

    from requests.auth import HTTPBasicAuth

    projects = json.loads(projects)
    http = HttpHook("GET", http_conn_id=http_conn_id, auth_type=HTTPBasicAuth)

    storages = []

    for project in projects["results"]:

        # get import storages
        response = http.run(
            endpoint="/api/storages/s3", data={"project": project["id"]}
        )

        if response.ok:
            storages.extend(
                [dict(item, direction="import") for item in response.json()]
            )  # add {'direction': 'import'} for each storage json.

        # get export storages
        response = http.run(
            endpoint="/api/storages/export/s3", data={"project": project["id"]}
        )

        if response.ok:
            storages.extend(
                [dict(item, direction="export") for item in response.json()]
            )  # add {'direction': 'export'} for each storage json.

    return storages


@task()
def sync_storages(
    storages,
    http_conn_id: str,
):
    from requests.auth import HTTPBasicAuth

    http = HttpHook("POST", http_conn_id=http_conn_id, auth_type=HTTPBasicAuth)

    for storage in storages:
        endpoint = (
            f"/api/storages/s3/{storage['id']}/sync"
            if storage["direction"] == "import"
            else f"/api/storages/export/s3/{storage['id']}/sync"
        )
        http.run(endpoint)


dag = DAG(
    dag_id="sync_storage",
    default_args=args,
    schedule_interval="0 0 * * *",
    start_date=datetime.now().replace(
        hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone("Asia/Seoul")
    ),
    tags=["labelstudio", "mlops"],
)

getProjects = SimpleHttpOperator(
    task_id="get_projects",
    endpoint="/api/projects",
    method="GET",
    http_conn_id="labelstudio_conn",
    do_xcom_push=True,
    dag=dag,
)

getStorages = get_storages(getProjects.output, "labelstudio_conn")
syncStorages = sync_storages(getStorages, "labelstudio_conn")

getProjects >> getStorages >> syncStorages
