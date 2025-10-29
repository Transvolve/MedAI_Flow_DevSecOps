from fastapi import APIRouter, Depends
from .security import verify_token
from .utils import latency_timer

router = APIRouter()

@router.get("/infer", dependencies=[Depends(verify_token)])
@latency_timer
async def infer():
    return {"message": "Model inference endpoint ready."}
