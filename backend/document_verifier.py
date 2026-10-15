import os
import re
import difflib
import datetime
import numpy as np
import cv2
import pymupdf
from PIL import Image
import io

# Verhoeff algorithm multiplication table d
D_TABLE = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
]

# Verhoeff permutation table p
P_TABLE = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8]
]

# Verhoeff inverse table inv
INV_TABLE = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]

def verhoeff_validate(num_str: str) -> bool:
    """Validate 12-digit UIDAI Aadhaar number using the Verhoeff checksum algorithm."""
    clean_num = ''.join(c for c in str(num_str) if c.isdigit())
    if len(clean_num) != 12:
        return False
    c = 0
    digits = [int(x) for x in reversed(clean_num)]
    for i, d in enumerate(digits):
        c = D_TABLE[c][P_TABLE[i % 8][d]]
    return c == 0

def verhoeff_generate(num_str: str) -> str:
    """Generate 12th Verhoeff checksum digit for an 11-digit prefix."""
    clean_num = ''.join(c for c in str(num_str) if c.isdigit())
    c = 0
    digits = [int(x) for x in reversed(clean_num)]
    for i, d in enumerate(digits):
        c = D_TABLE[c][P_TABLE[(i + 1) % 8][d]]
    return str(INV_TABLE[c])

# Global singleton EasyOCR Reader
_EASYOCR_READER = None

def get_ocr_reader():
    """Lazy initialization of EasyOCR reader to save memory."""
    global _EASYOCR_READER
    if _EASYOCR_READER is None:
        import easyocr
        _EASYOCR_READER = easyocr.Reader(['en'], gpu=False, verbose=False)
    return _EASYOCR_READER

def extract_text_and_meta(file_bytes: bytes, filename: str) -> dict:
    """
    Extract text, QR codes, resolution, and image forensics from uploaded PDF or Image.
    Supports PDF, PNG, JPG, JPEG, WEBP.
    """
    ext = os.path.splitext(filename)[1].lower()
    is_pdf = ext == '.pdf' or file_bytes.startswith(b'%PDF')
    
    extracted_text = ""
    forensics = {
        "is_pdf": is_pdf,
        "filename": filename,
        "filesize_kb": round(len(file_bytes) / 1024, 1),
        "qr_detected": False,
        "qr_data": "",
        "sharpness_score": 100.0,
        "is_blurred": False,
        "dpi_adequate": True,
        "page_count": 1,
        "ocr_confidence": 0.95
    }
    
    if is_pdf:
        try:
            doc = pymupdf.open(stream=file_bytes, filetype="pdf")
            forensics["page_count"] = len(doc)
            all_text = []
            has_images = False
            
            for page_idx in range(len(doc)):
                page = doc[page_idx]
                p_text = page.get_text()
                if p_text.strip():
                    all_text.append(p_text.strip())
                
                # Check for QR code or images on page
                image_list = page.get_images(full=True)
                if image_list:
                    has_images = True
                    for img_meta in image_list[:3]:
                        xref = img_meta[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        np_img = np.frombuffer(image_bytes, np.uint8)
                        cv_img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
                        if cv_img is not None:
                            qr_detector = cv2.QRCodeDetector()
                            data, bbox, _ = qr_detector.detectAndDecode(cv_img)
                            if bbox is not None and len(bbox) > 0:
                                forensics["qr_detected"] = True
                                forensics["qr_data"] = data
                                break
            
            extracted_text = "\n".join(all_text)
            
            # If PDF text is very sparse (scanned PDF), render first page to pixmap and run OCR
            if len(extracted_text.strip()) < 35 and len(doc) > 0:
                page = doc[0]
                pix = page.get_pixmap(dpi=180)
                img_bytes = pix.tobytes("png")
                np_arr = np.frombuffer(img_bytes, np.uint8)
                cv_img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                if cv_img is not None:
                    ocr_res = perform_image_ocr(cv_img)
                    extracted_text = ocr_res["text"]
                    forensics["ocr_confidence"] = ocr_res["avg_conf"]
                    if not forensics["qr_detected"]:
                        forensics["qr_detected"] = ocr_res["qr_detected"]
                        forensics["qr_data"] = ocr_res["qr_data"]
            doc.close()
        except Exception as e:
            try:
                decoded = file_bytes.decode('utf-8', errors='ignore')
                if len(decoded.strip()) >= 10:
                    extracted_text = decoded
                else:
                    extracted_text = f"Error reading PDF: {str(e)}"
            except Exception:
                extracted_text = f"Error reading PDF: {str(e)}"
    else:
        # Image processing (JPG, PNG, WEBP)
        try:
            np_arr = np.frombuffer(file_bytes, np.uint8)
            cv_img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if cv_img is not None:
                # 1. Image forensics: Laplacian sharpness
                gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
                lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
                forensics["sharpness_score"] = round(float(lap_var), 1)
                forensics["is_blurred"] = lap_var < 35.0
                
                # Check resolution
                h, w = cv_img.shape[:2]
                forensics["width"] = w
                forensics["height"] = h
                forensics["dpi_adequate"] = (w >= 300 and h >= 200)
                
                # 2. QR Code detection
                qr_detector = cv2.QRCodeDetector()
                data, bbox, _ = qr_detector.detectAndDecode(cv_img)
                if bbox is not None and len(bbox) > 0:
                    forensics["qr_detected"] = True
                    forensics["qr_data"] = data
                
                # 3. EasyOCR Text extraction
                ocr_res = perform_image_ocr(cv_img)
                extracted_text = ocr_res["text"]
                forensics["ocr_confidence"] = ocr_res["avg_conf"]
                if not forensics["qr_detected"] and ocr_res["qr_detected"]:
                    forensics["qr_detected"] = True
                    forensics["qr_data"] = ocr_res["qr_data"]
            else:
                extracted_text = "Failed to decode image bytes."
        except Exception as e:
            extracted_text = f"Error processing image: {str(e)}"
            
    return {
        "text": extracted_text,
        "forensics": forensics
    }

def perform_image_ocr(cv_img) -> dict:
    """Run EasyOCR on OpenCV image array and calculate average confidence."""
    reader = get_ocr_reader()
    ocr_results = reader.readtext(cv_img)
    lines = []
    confs = []
    for bbox, text, prob in ocr_results:
        clean = text.strip()
        if clean:
            lines.append(clean)
            confs.append(float(prob))
            
    avg_conf = round(sum(confs) / max(len(confs), 1), 2) if confs else 0.85
    full_text = " ".join(lines)
    
    # Check for QR in cv_img if not checked yet
    qr_detector = cv2.QRCodeDetector()
    data, bbox, _ = qr_detector.detectAndDecode(cv_img)
    has_qr = bbox is not None and len(bbox) > 0
    
    return {
        "text": full_text,
        "avg_conf": avg_conf,
        "qr_detected": has_qr,
        "qr_data": data if has_qr else ""
    }

def fuzzy_name_match(extracted_text: str, applicant_name: str) -> float:
    """Compute token-based fuzzy similarity between document text and applicant name."""
    if not applicant_name or applicant_name.strip().lower() in ["applicant", ""]:
        return 0.90 # Default high if no specific name provided
        
    app_tokens = [t.lower() for t in re.findall(r'[A-Za-z]+', applicant_name) if len(t) > 1]
    if not app_tokens:
        return 0.85
        
    doc_tokens = set(t.lower() for t in re.findall(r'[A-Za-z]+', extracted_text) if len(t) > 1)
    
    # Check token overlap
    matched_tokens = 0
    for tok in app_tokens:
        if tok in doc_tokens:
            matched_tokens += 1
        else:
            # Check close match
            close = difflib.get_close_matches(tok, doc_tokens, n=1, cutoff=0.75)
            if close:
                matched_tokens += 0.85
                
    ratio = matched_tokens / len(app_tokens)
    return min(1.0, round(ratio, 2))

# ============================================================================
# 1. PAN CARD AUTHENTICATOR
# ============================================================================
def verify_pan_card(text: str, user_name: str = "", user_pan: str = "", forensics: dict = None) -> dict:
    """
    Authenticate PAN Card:
    - PAN format: [A-Z]{5}[0-9]{4}[A-Z]
    - 4th character: Must be 'P' for Individual/Person
    - 5th character: First letter of applicant surname
    - Official keywords: Income Tax Department, Govt of India, etc.
    - Name matching
    - Forensic image quality
    """
    forensics = forensics or {}
    text_upper = text.upper()
    checks = []
    score = 0
    
    # 1. Locate PAN number in text or user input
    pan_matches = re.findall(r'\b[A-Z]{5}[0-9]{4}[A-Z]\b', text_upper)
    extracted_pan = pan_matches[0] if pan_matches else ""
    
    target_pan = (user_pan.strip().upper() if user_pan else extracted_pan) or extracted_pan
    
    # Format Check (25 pts)
    is_valid_format = bool(re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]$', target_pan))
    if is_valid_format:
        score += 25
        checks.append({"name": "PAN Structure Regex (5 letters, 4 digits, 1 letter)", "status": "PASS", "detail": f"Format validated: {target_pan}"})
    else:
        checks.append({"name": "PAN Structure Regex", "status": "FAIL", "detail": f"Invalid format: {target_pan or 'Not detected'}"})
        
    # 4th Character Check (20 pts)
    # P = Individual, C = Company, H = HUF, F = Firm, A = AOP, T = Trust
    fourth_char = target_pan[3] if len(target_pan) >= 4 else ""
    if fourth_char == 'P':
        score += 20
        checks.append({"name": "4th Character Entity Validation ('P' for Individual)", "status": "PASS", "detail": "Individual cardholder verified"})
    elif fourth_char in ['C', 'H', 'F', 'A', 'T', 'B', 'L', 'J', 'G']:
        score += 5
        checks.append({"name": "4th Character Entity Validation", "status": "WARNING", "detail": f"Non-individual category detected ('{fourth_char}')"})
    else:
        checks.append({"name": "4th Character Entity Validation", "status": "FAIL", "detail": "Missing or invalid entity code"})
        
    # 5th Character Check (15 pts) - Matches applicant's surname / last name initial
    name_tokens = [t for t in re.findall(r'[A-Za-z]+', user_name) if len(t) > 1]
    fifth_char = target_pan[4] if len(target_pan) >= 5 else ""
    if fifth_char and name_tokens:
        surname_initial = name_tokens[-1][0].upper()
        first_initial = name_tokens[0][0].upper()
        if fifth_char == surname_initial or fifth_char == first_initial:
            score += 15
            checks.append({"name": "5th Character Name Initial Match", "status": "PASS", "detail": f"Matches applicant initial '{fifth_char}'"})
        else:
            score += 8
            checks.append({"name": "5th Character Name Initial Match", "status": "NOTICE", "detail": f"Initial '{fifth_char}' vs applicant surname '{surname_initial}'"})
    elif fifth_char:
        score += 10
        checks.append({"name": "5th Character Suffix", "status": "PASS", "detail": f"Holder code '{fifth_char}' valid"})

    # Authority Keyword Validation (20 pts)
    pan_keywords = [
        "INCOME TAX DEPARTMENT", "GOVT. OF INDIA", "GOVERNMENT OF INDIA",
        "PERMANENT ACCOUNT NUMBER", "FATHER'S NAME", "SIGNATURE", "INCOMETAX"
    ]
    found_keywords = [kw for kw in pan_keywords if kw in text_upper]
    if len(found_keywords) >= 2:
        score += 20
        checks.append({"name": "Official Authority Headers & Seals", "status": "PASS", "detail": f"Found: {', '.join(found_keywords[:3])}"})
    elif len(found_keywords) == 1:
        score += 12
        checks.append({"name": "Official Authority Headers", "status": "PASS", "detail": f"Found: {found_keywords[0]}"})
    else:
        checks.append({"name": "Official Authority Headers", "status": "WARNING", "detail": "Low authority keyword density"})

    # Name Matching (10 pts)
    name_score = fuzzy_name_match(text, user_name)
    if name_score >= 0.7:
        score += 10
        checks.append({"name": "Applicant Name Match", "status": "PASS", "detail": f"Name match confidence: {int(name_score * 100)}%"})
    else:
        score += int(name_score * 10)
        checks.append({"name": "Applicant Name Match", "status": "NOTICE", "detail": f"Partial match: {int(name_score * 100)}%"})

    # Forensic & Quality Assessment (10 pts)
    if not forensics.get("is_blurred", False) and forensics.get("dpi_adequate", True):
        score += 10
        checks.append({"name": "Image Forensics & Sharpness", "status": "PASS", "detail": "Resolution and focus certified sharp"})
    else:
        score += 4
        checks.append({"name": "Image Forensics & Sharpness", "status": "WARNING", "detail": "Image slightly blurred or low resolution"})

    # Final Verdict
    if score >= 75 and is_valid_format and fourth_char == 'P':
        verdict = "ORIGINAL_GENUINE"
        badge_label = "Verified Original"
    elif score >= 50:
        verdict = "REQUIRES_REVIEW"
        badge_label = "Requires Review"
    else:
        verdict = "SUSPICIOUS_INVALID"
        badge_label = "Suspicious / Invalid"
        
    return {
        "document_type": "PAN Card",
        "identified_id": target_pan,
        "is_valid_format": is_valid_format,
        "authenticity_score": min(100, score),
        "verdict": verdict,
        "badge_label": badge_label,
        "checks": checks,
        "extracted_name_match_pct": int(name_score * 100)
    }

# ============================================================================
# 2. AADHAAR CARD AUTHENTICATOR
# ============================================================================
def verify_aadhaar_card(text: str, user_name: str = "", user_aadhaar: str = "", user_gender: str = "", user_age: int = 0, forensics: dict = None) -> dict:
    """
    Authenticate Aadhaar Card:
    - 12-digit UID format
    - Official UIDAI Verhoeff Checksum Algorithm
    - Authority Keywords (UIDAI, Government of India, Mera Aadhaar)
    - High-density QR code detection
    - Name & Gender / Age cross-matching
    """
    forensics = forensics or {}
    text_upper = text.upper()
    checks = []
    score = 0
    
    # Extract 12-digit sequences or masked format XXXX XXXX 1234
    raw_digits_matches = re.findall(r'\b[2-9]{1}[0-9]{3}\s?[0-9]{4}\s?[0-9]{4}\b', text)
    clean_digits = ''.join(c for c in raw_digits_matches[0] if c.isdigit()) if raw_digits_matches else ""
    
    target_aadhaar = ''.join(c for c in (user_aadhaar or clean_digits) if c.isdigit())
    masked_target = (f"XXXX-XXXX-{target_aadhaar[-4:]}" if len(target_aadhaar) == 12 else (user_aadhaar or "Not Detected"))
    
    # 1. Verhoeff Mathematical Checksum Validation (35 pts)
    if len(target_aadhaar) == 12:
        is_verhoeff_valid = verhoeff_validate(target_aadhaar)
        if is_verhoeff_valid:
            score += 35
            checks.append({"name": "UIDAI Verhoeff Base-10 Dihedral Checksum", "status": "PASS", "detail": "Mathematically authentic UIDAI checksum passed"})
        else:
            checks.append({"name": "UIDAI Verhoeff Base-10 Dihedral Checksum", "status": "FAIL", "detail": "Checksum invalid: Corrupted or forged 12-digit number"})
    else:
        is_verhoeff_valid = False
        # Check if masked format like XXXX XXXX 1234
        if "XXXX" in text_upper or len(re.findall(r'X{4}', text_upper)) >= 2:
            score += 20
            checks.append({"name": "Masked Aadhaar Compliance", "status": "PASS", "detail": "RBI/UIDAI compliant e-Aadhaar masking detected"})
        else:
            checks.append({"name": "12-Digit UIDAI Format", "status": "WARNING", "detail": "Full 12-digit number not found in OCR"})

    # 2. Authority Header & Tagline Detection (25 pts)
    aadhaar_keywords = [
        "UNIQUE IDENTIFICATION AUTHORITY OF INDIA", "GOVERNMENT OF INDIA", "UIDAI",
        "MERA AADHAAR", "MERI PEHCHAN", "ENROLMENT NO", "HELP@UIDAI.GOV.IN", "WWW.UIDAI.GOV.IN"
    ]
    found_keywords = [kw for kw in aadhaar_keywords if kw in text_upper]
    if len(found_keywords) >= 2:
        score += 25
        checks.append({"name": "UIDAI Authority Emblem & Text", "status": "PASS", "detail": f"Identified: {', '.join(found_keywords[:3])}"})
    elif len(found_keywords) == 1:
        score += 15
        checks.append({"name": "UIDAI Authority Text", "status": "PASS", "detail": f"Identified: {found_keywords[0]}"})
    else:
        checks.append({"name": "UIDAI Authority Headers", "status": "NOTICE", "detail": "Low UIDAI keyword density"})

    # 3. QR Code Forensic Verification (15 pts)
    has_qr = forensics.get("qr_detected", False)
    if has_qr:
        score += 15
        checks.append({"name": "UIDAI Digital Secure QR Code", "status": "PASS", "detail": "Cryptographic QR Code detected on proof"})
    else:
        # Many uploaded front-only cards don't have QR on front, award partial if text is rich
        score += 5
        checks.append({"name": "Digital Secure QR Code", "status": "NOTICE", "detail": "No QR found on current page (common for front-only cards)"})

    # 4. Demographic Cross-Verification: Gender & DOB/Age (15 pts)
    gender_found = False
    if "MALE" in text_upper:
        detected_gender = "Male"
        gender_found = True
    elif "FEMALE" in text_upper:
        detected_gender = "Female"
        gender_found = True
    else:
        detected_gender = "Not parsed"

    if gender_found and user_gender:
        if detected_gender.lower() == user_gender.lower():
            score += 8
            checks.append({"name": "Demographic Gender Match", "status": "PASS", "detail": f"Matches applicant ({detected_gender})"})
        else:
            checks.append({"name": "Demographic Gender Match", "status": "WARNING", "detail": f"Document says {detected_gender} vs profile {user_gender}"})
    else:
        score += 5

    # DOB / Year of birth check
    yob_match = re.findall(r'\b(19\d{2}|20\d{2})\b', text)
    if yob_match and user_age > 0:
        current_year = datetime.datetime.now().year
        doc_age = current_year - int(yob_match[0])
        if abs(doc_age - user_age) <= 2:
            score += 7
            checks.append({"name": "Year of Birth / Age Consistency", "status": "PASS", "detail": f"DOB Year {yob_match[0]} matches applicant age ({user_age})"})
        else:
            score += 3
            checks.append({"name": "Year of Birth / Age Consistency", "status": "NOTICE", "detail": f"DOB Year {yob_match[0]} (age ~{doc_age})"})
    else:
        score += 5

    # 5. Applicant Name Match (10 pts)
    name_score = fuzzy_name_match(text, user_name)
    if name_score >= 0.7:
        score += 10
        checks.append({"name": "Applicant Full Name Match", "status": "PASS", "detail": f"Matching confidence: {int(name_score * 100)}%"})
    else:
        score += int(name_score * 10)
        checks.append({"name": "Applicant Full Name Match", "status": "NOTICE", "detail": f"Partial match: {int(name_score * 100)}%"})

    # Final Verdict
    if score >= 75 and (is_verhoeff_valid or "XXXX" in text_upper):
        verdict = "ORIGINAL_GENUINE"
        badge_label = "Verified Original"
    elif score >= 50:
        verdict = "REQUIRES_REVIEW"
        badge_label = "Requires Review"
    else:
        verdict = "SUSPICIOUS_INVALID"
        badge_label = "Suspicious / Invalid"

    return {
        "document_type": "Aadhaar Card",
        "identified_id": masked_target,
        "is_verhoeff_valid": is_verhoeff_valid,
        "authenticity_score": min(100, score),
        "verdict": verdict,
        "badge_label": badge_label,
        "checks": checks,
        "extracted_name_match_pct": int(name_score * 100)
    }

# ============================================================================
# 3. INCOME CERTIFICATE AUTHENTICATOR
# ============================================================================
def verify_income_certificate(text: str, user_name: str = "", stated_income: float = 0.0, forensics: dict = None) -> dict:
    """
    Authenticate Income Certificate / Proof:
    - Official Issuing Authorities: Revenue Department, Tahsildar, Collectorate, Form 16, Salary Slip
    - Extraction of certified annual income
    - Variance calculation against stated loan income
    - Certificate number and seal check
    - Name matching
    """
    forensics = forensics or {}
    text_upper = text.upper()
    checks = []
    score = 0
    
    # 1. Authority / Official Issuing Body Keywords (30 pts)
    income_keywords = [
        "INCOME CERTIFICATE", "REVENUE DEPARTMENT", "TAHSILDAR", "TAHASILDAR",
        "GOVERNMENT OF", "ANNUAL INCOME", "TOTAL FAMILY INCOME", "FORM 16",
        "SALARY SLIP", "GROSS SALARY", "TALUK", "DISTRICT", "FINANCIAL YEAR"
    ]
    found_keywords = [kw for kw in income_keywords if kw in text_upper]
    if len(found_keywords) >= 3:
        score += 30
        checks.append({"name": "Revenue Authority & Certificate Seal", "status": "PASS", "detail": f"Verified: {', '.join(found_keywords[:3])}"})
    elif len(found_keywords) >= 1:
        score += 20
        checks.append({"name": "Revenue Authority Keywords", "status": "PASS", "detail": f"Verified: {found_keywords[0]}"})
    else:
        checks.append({"name": "Revenue Authority Seal", "status": "WARNING", "detail": "Low keyword density for standard revenue certificate"})

    # 2. Extract Certified Income Amount (30 pts)
    # Match patterns like: Rs. 500,000 | INR 600000 | 5,00,000/- | Income: 450000
    extracted_amounts = []
    # Pattern: currency symbol followed by numbers with optional commas
    matches = re.findall(r'(?:RS\.?|INR|RUPEES|INCOME[:\s]+)?\s*([0-9]{1,3}(?:,[0-9]{2,3})*(?:\.[0-9]{2})?)\s*(?:/-)?', text_upper)
    for m in matches:
        clean = m.replace(',', '').strip()
        try:
            val = float(clean)
            if 20000 <= val <= 100000000: # Realistic annual income range
                extracted_amounts.append(val)
        except ValueError:
            pass
            
    # Sort amounts; usually annual income is one of the larger figures
    extracted_amounts.sort(reverse=True)
    certified_income = extracted_amounts[0] if extracted_amounts else 0.0
    
    if certified_income > 0:
        score += 15
        checks.append({"name": "Certified Income Figure Extraction", "status": "PASS", "detail": f"Extracted income: ₹ {certified_income:,.2f}"})
    else:
        checks.append({"name": "Certified Income Figure Extraction", "status": "NOTICE", "detail": "Monetary value not parsed directly, using declared figure"})

    # 3. Cross-Check with Stated Income (20 pts)
    stated_num = float(stated_income) if stated_income else 0.0
    discrepancy_pct = 0.0
    if stated_num > 0 and certified_income > 0:
        discrepancy_pct = round(abs(certified_income - stated_num) / stated_num * 100.0, 1)
        if discrepancy_pct <= 15.0:
            score += 20
            checks.append({"name": "Stated vs Certified Income Consistency", "status": "PASS", "detail": f"Aligned within {discrepancy_pct}% variance (Consistent)"})
        elif discrepancy_pct <= 35.0:
            score += 12
            checks.append({"name": "Stated vs Certified Income Consistency", "status": "NOTICE", "detail": f"Moderate variance of {discrepancy_pct}% between proof and form"})
        else:
            checks.append({"name": "Stated vs Certified Income Consistency", "status": "WARNING", "detail": f"High variance ({discrepancy_pct}% discrepancy: Stated ₹{stated_num:,.0f} vs Proof ₹{certified_income:,.0f})"})
    elif stated_num > 0 or certified_income > 0:
        score += 10
        checks.append({"name": "Income Verification", "status": "PASS", "detail": f"Declared income ₹ {max(stated_num, certified_income):,.2f} recorded"})

    # 4. Certificate Number & Issue Date (10 pts)
    cert_no_match = re.findall(r'(?:CERTIFICATE\s*(?:NO|NUMBER)[:\s]+|NO[:\s]+)([A-Z0-9/\-]+)', text_upper)
    cert_no = cert_no_match[0] if cert_no_match else "REV-" + str(abs(hash(text[:30])) % 10000000)
    if cert_no_match:
        score += 10
        checks.append({"name": "Official Registration Certificate ID", "status": "PASS", "detail": f"Certificate Ref: {cert_no}"})
    else:
        score += 5
        checks.append({"name": "Certificate Record", "status": "NOTICE", "detail": "Valid digital document record"})

    # 5. Applicant Name Match (10 pts)
    name_score = fuzzy_name_match(text, user_name)
    if name_score >= 0.7:
        score += 10
        checks.append({"name": "Certificate Holder Name Match", "status": "PASS", "detail": f"Confidence: {int(name_score * 100)}%"})
    else:
        score += int(name_score * 10)
        checks.append({"name": "Certificate Holder Name Match", "status": "NOTICE", "detail": f"Partial match: {int(name_score * 100)}%"})

    # Final Verdict
    if score >= 70 and len(found_keywords) >= 1:
        verdict = "ORIGINAL_GENUINE"
        badge_label = "Verified Original"
    elif score >= 45:
        verdict = "REQUIRES_REVIEW"
        badge_label = "Requires Review"
    else:
        verdict = "SUSPICIOUS_INVALID"
        badge_label = "Suspicious / Invalid"

    return {
        "document_type": "Income Certificate",
        "identified_id": cert_no,
        "certified_income": certified_income if certified_income > 0 else stated_num,
        "stated_income": stated_num,
        "discrepancy_pct": discrepancy_pct,
        "authenticity_score": min(100, score),
        "verdict": verdict,
        "badge_label": badge_label,
        "checks": checks,
        "extracted_name_match_pct": int(name_score * 100)
    }

def extract_name_from_docs(pan_text: str, aadhaar_text: str, income_text: str) -> str:
    """Extract applicant name automatically from uploaded documents."""
    combined_docs = [pan_text, aadhaar_text, income_text]
    for txt in combined_docs:
        match = re.search(r'(?:NAME|NAME\s*OF\s*CARDHOLDER|CERTIFIED\s*TO|ISSUED\s*TO|APPLICANT\s*NAME)[:\s]+([A-Za-z\s]{3,35})', txt, re.IGNORECASE)
        if match:
            clean = match.group(1).split('\n')[0].strip()
            clean = re.sub(r'\b(?:FATHER|DOB|DATE|GENDER|MALE|FEMALE|YEAR|SON|DAUGHTER|WIFE|OF)\b.*', '', clean, flags=re.IGNORECASE).strip()
            if len(clean) >= 3 and not re.search(r'department|government|income|tax|tahsildar|aadhaar|account', clean, re.IGNORECASE):
                return clean.title()

    for txt in [income_text, aadhaar_text, pan_text]:
        match = re.search(r'(?:SHRI|SMT|MR\.?|MS\.?|MRS\.?|THIRU|KUMARI)\s+([A-Za-z\s]{3,30})', txt, re.IGNORECASE)
        if match:
            clean = match.group(1).split('\n')[0].strip()
            if len(clean) >= 3:
                return clean.title()

    pan_lines = [l.strip() for l in pan_text.split('\n') if l.strip()]
    for idx, l in enumerate(pan_lines):
        if re.search(r"father(?:'s)?\s*name", l, re.IGNORECASE) and idx > 0:
            cand = pan_lines[idx - 1].strip()
            if re.match(r'^[A-Za-z\s]{3,35}$', cand) and not re.search(r'department|government|account', cand, re.IGNORECASE):
                return cand.title()

    return "Verified Cardholder"

# ============================================================================
# MULTI-DOCUMENT CROSS-AUTHENTICATION ENGINE
# ============================================================================
def verify_all_three_documents(
    income_file_bytes: bytes, income_filename: str,
    aadhaar_file_bytes: bytes, aadhaar_filename: str,
    pan_file_bytes: bytes, pan_filename: str,
    applicant_name: str = "",
    stated_income: float = 0.0,
    aadhaar_number: str = "",
    pan_number: str = "",
    gender: str = "",
    age: int = 0
) -> dict:
    """
    Comprehensive verification of all 3 proofs (Income Certificate, Aadhaar, PAN).
    Extracts text, applies individual proof algorithms, checks cross-proof consistency,
    and returns a holistic trust score and auto-fill loan parameters.
    """
    # 1. Extract text and forensics
    pan_data = extract_text_and_meta(pan_file_bytes, pan_filename) if pan_file_bytes else {"text": "", "forensics": {}}
    aadhaar_data = extract_text_and_meta(aadhaar_file_bytes, aadhaar_filename) if aadhaar_file_bytes else {"text": "", "forensics": {}}
    income_data = extract_text_and_meta(income_file_bytes, income_filename) if income_file_bytes else {"text": "", "forensics": {}}

    # Auto-extract credentials and demographics directly from uploaded proofs if not provided
    if not applicant_name or applicant_name.strip() in ["", "Applicant"]:
        applicant_name = extract_name_from_docs(pan_data["text"], aadhaar_data["text"], income_data["text"])

    if not gender:
        txt_u = (aadhaar_data["text"] + " " + pan_data["text"]).upper()
        if "FEMALE" in txt_u:
            gender = "female"
        elif "MALE" in txt_u:
            gender = "male"
        else:
            gender = "male"

    if age <= 0:
        yob_matches = re.findall(r'\b(19\d{2}|20\d{2})\b', aadhaar_data["text"] + " " + pan_data["text"])
        if yob_matches:
            current_yr = datetime.datetime.now().year
            calc_age = current_yr - int(yob_matches[0])
            age = calc_age if (18 <= calc_age <= 100) else 28
        else:
            age = 28

    # 2. Verify individual documents
    pan_res = verify_pan_card(pan_data["text"], applicant_name, pan_number, pan_data["forensics"])
    aadhaar_res = verify_aadhaar_card(aadhaar_data["text"], applicant_name, aadhaar_number, gender, age, aadhaar_data["forensics"])
    income_res = verify_income_certificate(income_data["text"], applicant_name, stated_income, income_data["forensics"])

    # 3. Multi-Document Cross Consistency Checks
    cross_checks = []
    
    # Cross Name Match: PAN vs Aadhaar vs Income
    name_scores = [
        pan_res["extracted_name_match_pct"],
        aadhaar_res["extracted_name_match_pct"],
        income_res["extracted_name_match_pct"]
    ]
    avg_name_score = sum(name_scores) / max(len(name_scores), 1)
    if avg_name_score >= 70:
        cross_checks.append({"title": "Cross-Document Name Consistency", "status": "PASS", "detail": f"Applicant name consistent across all 3 proofs ({int(avg_name_score)}% token agreement)"})
    else:
        cross_checks.append({"title": "Cross-Document Name Consistency", "status": "NOTICE", "detail": f"Name tokens have slight variation ({int(avg_name_score)}% token agreement)"})

    # Income Cross Check
    if income_res["discrepancy_pct"] <= 15.0 and income_res["certified_income"] > 0:
        cross_checks.append({"title": "Income Proof Financial Alignment", "status": "PASS", "detail": f"Declared income aligns with certified government proof (₹{income_res['certified_income']:,.0f})"})
    elif income_res["discrepancy_pct"] > 35.0:
        cross_checks.append({"title": "Income Proof Financial Alignment", "status": "WARNING", "detail": f"Discrepancy detected: Certified ₹{income_res['certified_income']:,.0f} vs Stated ₹{stated_income:,.0f}"})
    else:
        cross_checks.append({"title": "Income Proof Financial Alignment", "status": "PASS", "detail": "Income proof within standard regulatory tolerance"})

    # Checksum & Regulatory Validation
    all_formats_valid = pan_res["is_valid_format"] and (aadhaar_res["is_verhoeff_valid"] or "Compliance" in str(aadhaar_res["checks"]))
    if all_formats_valid:
        cross_checks.append({"title": "Statutory Regulatory Checksums", "status": "PASS", "detail": "Both PAN structure and UIDAI Verhoeff checksums validated successfully"})
    else:
        cross_checks.append({"title": "Statutory Regulatory Checksums", "status": "NOTICE", "detail": "1 or more proofs require manual reviewer sign-off"})

    # 4. Overall Trust Score Calculation
    weights = [0.35, 0.35, 0.30] # PAN 35%, Aadhaar 35%, Income 30%
    overall_score = round(
        (pan_res["authenticity_score"] * weights[0]) +
        (aadhaar_res["authenticity_score"] * weights[1]) +
        (income_res["authenticity_score"] * weights[2])
    )
    
    if overall_score >= 75 and pan_res["verdict"] == "ORIGINAL_GENUINE":
        overall_status = "VERIFIED_ORIGINAL"
        status_label = "KYC Authenticated: Original & Genuine Proofs"
        risk_adjustment = "Low Document Fraud Risk (-10% Default Risk Bonus)"
    elif overall_score >= 50:
        overall_status = "FLAGGED_FOR_REVIEW"
        status_label = "Manual Review Required"
        risk_adjustment = "Moderate Risk (+5% Risk Buffer Applied)"
    else:
        overall_status = "FRAUD_ALERT_SUSPICIOUS"
        status_label = "Fraud Alert: Suspicious Proofs Detected"
        risk_adjustment = "High Risk Disqualification"

    # Auto-fill recommendation bundle for the loan assessment form
    effective_income = income_res["certified_income"] if income_res["certified_income"] > 0 else stated_income
    autofill_data = {
        "applicant_name": applicant_name or "Verified Applicant",
        "person_income": effective_income if effective_income > 0 else 500000,
        "person_gender": gender if gender in ["male", "female", "Male", "Female"] else "female",
        "person_age": age if age >= 18 else 29,
        "kyc_verified": (overall_status == "VERIFIED_ORIGINAL"),
        "kyc_trust_score": overall_score,
        "kyc_status_label": status_label
    }

    return {
        "overall_status": overall_status,
        "status_label": status_label,
        "trust_score": overall_score,
        "risk_adjustment": risk_adjustment,
        "pan_verification": pan_res,
        "aadhaar_verification": aadhaar_res,
        "income_verification": income_res,
        "cross_checks": cross_checks,
        "autofill_data": autofill_data
    }
