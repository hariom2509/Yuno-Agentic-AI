import os

from celery import Celery


celery = Celery(
    "yuno_ai",
    broker=os.getenv("REDIS_URL"),
    backend=os.getenv("REDIS_URL")
)

celery.conf.update(

    task_serializer="json",

    accept_content=["json"],

    result_serializer="json",

    timezone="UTC",

    enable_utc=True,

    imports=[
        "app.tasks.workflow_tasks"
    ]
)