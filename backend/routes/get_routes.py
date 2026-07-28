from fastapi import APIRouter, HTTPException
import database

router = APIRouter()

@router.get("/api/history")
async def get_assessment_history():
    try:
        return database.fetch_assessments()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
