from fastapi import APIRouter, HTTPException
import database

router = APIRouter()

@router.delete("/api/history")
async def clear_assessment_history():
    try:
        database.delete_all_assessments()
        return {"status": "success", "message": "All historical logs deleted."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
