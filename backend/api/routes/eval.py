from fastapi import APIRouter, Depends

from backend.evaluations.runner import EvalRunner

router = APIRouter(prefix="/eval", tags=["evaluation"])


@router.post("/run")
async def run_evaluation() -> dict:
    runner = EvalRunner()
    return await runner.run_all()
