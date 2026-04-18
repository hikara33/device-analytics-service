from celery.result import AsyncResult
from fastapi import APIRouter

from app.celery_app import celery_app
from app.schemas.schemas import TaskStatusOut

router = APIRouter()


@router.get("/{task_id}", response_model=TaskStatusOut)
def get_task_status(task_id: str) -> TaskStatusOut:
    ar: AsyncResult = AsyncResult(task_id, app=celery_app)
    state = ar.state
    err: str | None = None
    result: dict | None = None
    if state == "FAILURE":
        err = str(ar.result) if ar.result else "failure"
    elif state == "SUCCESS":
        result = ar.result if isinstance(ar.result, dict) else {"value": ar.result}

    return TaskStatusOut(task_id=task_id, state=state, result=result, error=err)
