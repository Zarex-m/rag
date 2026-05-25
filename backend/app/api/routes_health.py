"""Write the health-check route here."""
from fastapi import APIRouter

router=APIRouter()



@router.post("/health")
async def health_check()->dict[str,str]:
    return {"status":"OK"}
