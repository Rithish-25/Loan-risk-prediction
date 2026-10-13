from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
import database
import pdf_generator

router = APIRouter()

@router.get("/api/history")
async def get_assessment_history():
    try:
        return database.fetch_assessments()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/history/{tx_id}/pdf")
async def download_history_assessment_pdf(tx_id: str):
    try:
        record = database.fetch_assessment_by_id(tx_id)
        if not record:
            raise HTTPException(status_code=404, detail="Assessment record not found.")

        income = float(record.get("income", 0))
        loan = float(record.get("loan", 0))
        savings = float(record.get("savings", 0))
        credit_score = int(record.get("credit_score", 650))
        defaults = record.get("defaults", "No")

        cap_factor = 0.35
        if defaults == "Yes":
            cap_factor = 0.10
        elif credit_score < 560:
            cap_factor = 0.15
        elif credit_score < 650:
            cap_factor = 0.25
        if savings >= loan:
            cap_factor = min(0.50, cap_factor + 0.10)

        record["recommended_cap"] = int(round(income * cap_factor))
        record["affordable_emi"] = int(round((income / 12.0) * 0.30))

        pdf_bytes = pdf_generator.generate_assessment_pdf(record)
        applicant_name = record.get("applicant_name") or record.get("name") or "Applicant"
        clean_name = "".join(c for c in applicant_name if c.isalnum() or c in (" ", "-", "_")).strip() or "Applicant"
        filename = f"{clean_name} Loan Risk.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate historical report PDF: {str(e)}")
