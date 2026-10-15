from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import document_verifier

router = APIRouter()

@router.post("/api/verify-documents")
async def verify_documents(
    income_certificate: Optional[UploadFile] = File(None),
    aadhaar_card: Optional[UploadFile] = File(None),
    pan_card: Optional[UploadFile] = File(None),
    applicant_name: str = Form(""),
    stated_income: float = Form(0.0),
    aadhaar_number: str = Form(""),
    pan_number: str = Form(""),
    gender: str = Form(""),
    age: int = Form(0)
):
    """
    Authenticate and verify 3 compulsory KYC proofs:
    1. Income Certificate (PDF or Image)
    2. Aadhaar Card (PDF or Image)
    3. PAN Card (PDF or Image)
    
    Extracts text, checks UIDAI Verhoeff checksums, PAN regex and entity categories,
    revenue department seals, and performs cross-document consistency checks.
    """
    try:
        # Read file bytes safely
        income_bytes = await income_certificate.read() if income_certificate else b""
        income_fname = income_certificate.filename if income_certificate else ""

        aadhaar_bytes = await aadhaar_card.read() if aadhaar_card else b""
        aadhaar_fname = aadhaar_card.filename if aadhaar_card else ""

        pan_bytes = await pan_card.read() if pan_card else b""
        pan_fname = pan_card.filename if pan_card else ""

        # Check if at least some data was provided
        if not income_bytes and not aadhaar_bytes and not pan_bytes and not pan_number and not aadhaar_number:
            raise HTTPException(
                status_code=400,
                detail="Please upload at least one document proof (PDF or Image) or provide verification details."
            )

        result = document_verifier.verify_all_three_documents(
            income_file_bytes=income_bytes,
            income_filename=income_fname,
            aadhaar_file_bytes=aadhaar_bytes,
            aadhaar_filename=aadhaar_fname,
            pan_file_bytes=pan_bytes,
            pan_filename=pan_fname,
            applicant_name=applicant_name.strip(),
            stated_income=float(stated_income),
            aadhaar_number=aadhaar_number.strip(),
            pan_number=pan_number.strip().upper(),
            gender=gender.strip(),
            age=int(age) if age else 0
        )
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"KYC Document verification processing failed: {str(e)}"
        )

@router.post("/api/verify-single-proof")
async def verify_single_proof(
    file: UploadFile = File(...),
    document_type: str = Form(...), # "pan", "aadhaar", "income"
    applicant_name: str = Form(""),
    expected_id: str = Form(""),
    expected_income: float = Form(0.0),
    gender: str = Form(""),
    age: int = Form(0)
):
    """Authenticate a single individual document proof (PAN, Aadhaar, or Income Certificate)."""
    try:
        file_bytes = await file.read()
        filename = file.filename
        
        extracted = document_verifier.extract_text_and_meta(file_bytes, filename)
        doc_type_lower = document_type.lower().strip()
        
        if "pan" in doc_type_lower:
            res = document_verifier.verify_pan_card(
                extracted["text"],
                applicant_name=applicant_name,
                user_pan=expected_id,
                forensics=extracted["forensics"]
            )
        elif "aadhaar" in doc_type_lower or "aadhar" in doc_type_lower:
            res = document_verifier.verify_aadhaar_card(
                extracted["text"],
                applicant_name=applicant_name,
                user_aadhaar=expected_id,
                user_gender=gender,
                user_age=int(age) if age else 0,
                forensics=extracted["forensics"]
            )
        elif "income" in doc_type_lower or "salary" in doc_type_lower:
            res = document_verifier.verify_income_certificate(
                extracted["text"],
                applicant_name=applicant_name,
                stated_income=float(expected_income),
                forensics=extracted["forensics"]
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid document_type. Expected: pan, aadhaar, or income")

        return {
            "document_type": document_type,
            "verification": res,
            "forensics": extracted["forensics"],
            "preview_text_snippet": extracted["text"][:250]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Single proof verification error: {str(e)}")

@router.get("/api/sample-kyc-data")
def get_sample_kyc_data():
    """Provides sample authentic details for rapid faculty/examiner demonstration."""
    valid_aadhaar_prefix = "54892341678"
    checksum = document_verifier.verhoeff_generate(valid_aadhaar_prefix)
    sample_aadhaar = valid_aadhaar_prefix + checksum
    
    return {
        "authentic_sample": {
            "applicant_name": "Rithish Kumar",
            "pan_number": "ABCPK8941F",
            "aadhaar_number": sample_aadhaar,
            "stated_income": 650000,
            "gender": "Male",
            "age": 28,
            "description": "Authentic individual PAN ('P' 4th letter, 'K' 5th letter) + valid UIDAI Verhoeff Aadhaar + matching Tahsildar Income Certificate."
        },
        "suspicious_sample": {
            "applicant_name": "Rithish Kumar",
            "pan_number": "ABCDX9999Z", # 'D' is invalid 4th letter for Individual, 'Z' doesn't match name
            "aadhaar_number": "123456789012", # Fails Verhoeff checksum
            "stated_income": 1200000, # Large discrepancy
            "gender": "Female",
            "age": 21,
            "description": "Tampered/Fabricated credentials (Invalid PAN entity code, mathematically forged Aadhaar checksum, demographic conflict)."
        }
    }
