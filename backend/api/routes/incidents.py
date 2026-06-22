from fastapi import APIRouter, Depends

from backend.config.settings import get_settings
from backend.memory.long_term import SQLiteLongTermMemory
from backend.models.incidents import Incident

router = APIRouter(tags=["incidents"])


def get_memory() -> SQLiteLongTermMemory:
    settings = get_settings()
    db_path = settings.database_url.replace("sqlite+aiosqlite:///", "")
    return SQLiteLongTermMemory(db_path=db_path)


@router.get("/incidents", response_model=list[Incident])
async def list_incidents(
    limit: int = 50,
    memory: SQLiteLongTermMemory = Depends(get_memory),
) -> list[Incident]:
    return await memory.list_incidents(limit=limit)
