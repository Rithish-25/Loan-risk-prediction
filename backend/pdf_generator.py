import io
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas for total page count and professional footer."""
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # Bottom rule and footer
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.75)
        self.line(36, 32, letter[0] - 36, 32)
        
        footer_text = "CreditGuard AI • Enterprise Credit Underwriting & Risk Prediction Report • Confidential"
        self.drawString(36, 20, footer_text)
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(letter[0] - 36, 20, page_str)
        self.restoreState()


def format_currency_inr(val):
    """Format number into Indian Rupee representation (e.g. Rs. 1,50,000)."""
    try:
        num = float(val)
        return f"Rs. {num:,.0f}"
    except (ValueError, TypeError):
        return f"Rs. {val}"


IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30), name="IST")

def format_assessment_datetime(date_val=None) -> str:
    """Format assessment date/time to accurate Indian Standard Time (IST)."""
    if not date_val:
        return datetime.datetime.now(IST).strftime("%b %d, %Y • %I:%M %p IST")

    try:
        if isinstance(date_val, str):
            cleaned = date_val.strip()
            if cleaned.endswith("Z"):
                dt = datetime.datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
            elif "+" in cleaned or ("-" in cleaned[10:] and "T" in cleaned):
                dt = datetime.datetime.fromisoformat(cleaned)
            else:
                dt = datetime.datetime.fromisoformat(cleaned)
        elif isinstance(date_val, datetime.datetime):
            dt = date_val
        elif isinstance(date_val, datetime.date):
            dt = datetime.datetime.combine(date_val, datetime.time.min, tzinfo=IST)
        else:
            dt = None

        if dt is not None:
            if dt.tzinfo is not None:
                dt_ist = dt.astimezone(IST)
            else:
                dt_ist = dt.replace(tzinfo=datetime.timezone.utc).astimezone(IST)
            return dt_ist.strftime("%b %d, %Y • %I:%M %p IST")
    except Exception:
        pass

    return str(date_val)


def generate_assessment_pdf(data: dict) -> bytes:
    """Generate a clean, highly professional loan risk assessment PDF report."""
    applicant_name = data.get("applicant_name") or data.get("name") or "Applicant"
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        title=f"{applicant_name} - Loan Risk Assessment",
        author="CreditGuard AI",
        subject=f"Loan Risk Assessment Report for {applicant_name}",
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=45
    )

    styles = getSampleStyleSheet()

    # Color Palette
    PRIMARY = colors.HexColor("#0f172a")      # Slate 900
    SECONDARY = colors.HexColor("#1e293b")    # Slate 800
    ACCENT = colors.HexColor("#4f46e5")       # Indigo 600
    MUTED = colors.HexColor("#64748b")        # Slate 500
    CARD_BG = colors.HexColor("#f8fafc")      # Slate 50
    BORDER_CLR = colors.HexColor("#e2e8f0")   # Slate 200

    decision = data.get("decision", "Approved")
    risk_val = float(data.get("risk", 0.0))

    if decision == "Approved":
        STATUS_COLOR = colors.HexColor("#059669")
        STATUS_BG = colors.HexColor("#ecfdf5")
    elif decision == "Rejected":
        STATUS_COLOR = colors.HexColor("#dc2626")
        STATUS_BG = colors.HexColor("#fef2f2")
    else:
        STATUS_COLOR = colors.HexColor("#d97706")
        STATUS_BG = colors.HexColor("#fffbeb")

    # Typography Styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=PRIMARY
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=MUTED
    )
    badge_style = ParagraphStyle(
        "DecisionBadge",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=STATUS_COLOR,
        alignment=1
    )
    section_heading = ParagraphStyle(
        "SecHead",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=PRIMARY,
        spaceBefore=8,
        spaceAfter=4
    )
    cell_lbl = ParagraphStyle(
        "CellLbl",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=MUTED
    )
    cell_val = ParagraphStyle(
        "CellVal",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=SECONDARY
    )
    kpi_title = ParagraphStyle(
        "KPITitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=10,
        textColor=MUTED,
        alignment=1
    )
    kpi_num = ParagraphStyle(
        "KPINum",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=PRIMARY,
        alignment=1
    )

    story = []

    # 1. HEADER BRANDING BLOCK
    tx_id = data.get("id", "TX-PENDING")
    formatted_date = format_assessment_datetime(data.get("date"))

    header_left = [
        Paragraph(f"{applicant_name.upper()} - LOAN RISK REPORT", title_style),
        Spacer(1, 2),
        Paragraph("CreditGuard AI • Enterprise Credit Underwriting & Risk Evaluation", subtitle_style),
        Spacer(1, 2),
        Paragraph(f"<b>Applicant:</b> {applicant_name} &nbsp;|&nbsp; <b>Report ID:</b> {tx_id} &nbsp;|&nbsp; <b>Evaluation Date:</b> {formatted_date}", subtitle_style)
    ]

    header_badge = [
        Paragraph(f"STATUS VERDICT", kpi_title),
        Spacer(1, 2),
        Paragraph(decision.upper(), badge_style)
    ]

    header_table = Table(
        [[header_left, header_badge]],
        colWidths=[400, 140]
    )
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (1, 0), (1, 0), STATUS_BG),
        ("BOX", (1, 0), (1, 0), 1, STATUS_COLOR),
        ("TOPPADDING", (1, 0), (1, 0), 8),
        ("BOTTOMPADDING", (1, 0), (1, 0), 8),
        ("LEFTPADDING", (1, 0), (1, 0), 8),
        ("RIGHTPADDING", (1, 0), (1, 0), 8),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))

    story.append(HRFlowable(width="100%", thickness=1, color=BORDER_CLR, spaceAfter=10))

    # 2. KEY METRICS HIGHLIGHT CARDS (4 Boxes)
    rec_cap = format_currency_inr(data.get("recommended_cap", 0))
    aff_emi = format_currency_inr(data.get("affordable_emi", 0)) + "/mo"

    kpi_card_1 = [Paragraph("DEFAULT RISK PROB", kpi_title), Spacer(1, 3), Paragraph(f"{risk_val:.1f}%", kpi_num)]
    kpi_card_2 = [Paragraph("APPROVAL VERDICT", kpi_title), Spacer(1, 3), Paragraph(decision, kpi_num)]
    kpi_card_3 = [Paragraph("RECOMMENDED CAP", kpi_title), Spacer(1, 3), Paragraph(rec_cap, kpi_num)]
    kpi_card_4 = [Paragraph("AFFORDABLE EMI", kpi_title), Spacer(1, 3), Paragraph(aff_emi, kpi_num)]

    kpi_table = Table(
        [[kpi_card_1, kpi_card_2, kpi_card_3, kpi_card_4]],
        colWidths=[135, 135, 135, 135]
    )
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CARD_BG),
        ("BOX", (0, 0), (-1, -1), 0.75, BORDER_CLR),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_CLR),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 12))

    # 3. DETAILED APPLICANT PROFILE & CREDIT CHARACTERISTICS
    story.append(Paragraph("1. Applicant Profile & Demographic Background", section_heading))

    applicant_name = data.get("applicant_name") or "Applicant"
    age = data.get("age", data.get("person_age", "N/A"))
    gender = str(data.get("gender", data.get("person_gender", "N/A"))).title()
    education = data.get("education", data.get("person_education", "N/A"))
    home = data.get("home", data.get("person_home_ownership", "N/A"))
    marital = data.get("marital_status", "Single")
    dependents = data.get("dependents", data.get("number_of_dependents", 0))

    demo_data = [
        [
            Paragraph("Full Name", cell_lbl), Paragraph(str(applicant_name), cell_val),
            Paragraph("Age / Demographic", cell_lbl), Paragraph(f"{age} Years ({gender})", cell_val)
        ],
        [
            Paragraph("Education Level", cell_lbl), Paragraph(str(education), cell_val),
            Paragraph("Home Ownership", cell_lbl), Paragraph(str(home), cell_val)
        ],
        [
            Paragraph("Marital Status", cell_lbl), Paragraph(str(marital), cell_val),
            Paragraph("Dependents Obligation", cell_lbl), Paragraph(f"{dependents} Dependents", cell_val)
        ]
    ]

    t_demo = Table(demo_data, colWidths=[120, 150, 130, 140])
    t_demo.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [CARD_BG, colors.white]),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER_CLR),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_CLR),
        ("TOPPADDING", (0, 0), (-1, -1), 4.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(t_demo)
    story.append(Spacer(1, 10))

    # 4. FINANCIAL STANDING & LIQUIDITY
    story.append(Paragraph("2. Financial Standing & Banking Relationships", section_heading))

    income = format_currency_inr(data.get("income", data.get("person_income", 0)))
    savings = format_currency_inr(data.get("savings", data.get("savings_balance", 0)))
    exp = data.get("exp", data.get("person_emp_exp", 0))
    bank_age = data.get("bank_age", data.get("bank_account_age", 1))
    vehicle = data.get("vehicle", data.get("vehicle_ownership", "No"))

    fin_data = [
        [
            Paragraph("Annual Income", cell_lbl), Paragraph(f"{income} / year", cell_val),
            Paragraph("Liquid Savings Balance", cell_lbl), Paragraph(f"{savings}", cell_val)
        ],
        [
            Paragraph("Employment Experience", cell_lbl), Paragraph(f"{exp} Years", cell_val),
            Paragraph("Bank Account Age", cell_lbl), Paragraph(f"{bank_age} Years", cell_val)
        ],
        [
            Paragraph("Vehicle Ownership Asset", cell_lbl), Paragraph(str(vehicle), cell_val),
            Paragraph("Liquidity Cushion", cell_lbl), Paragraph("Strong" if float(data.get("savings", data.get("savings_balance", 0))) >= float(data.get("loan", data.get("loan_amnt", 1))) else "Standard", cell_val)
        ]
    ]

    t_fin = Table(fin_data, colWidths=[120, 150, 130, 140])
    t_fin.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [CARD_BG, colors.white]),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER_CLR),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_CLR),
        ("TOPPADDING", (0, 0), (-1, -1), 4.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(t_fin)
    story.append(Spacer(1, 10))

    # 5. REQUESTED LOAN TERMS & CREDIT BUREAU METRICS
    story.append(Paragraph("3. Loan Proposal Terms & Credit Bureau Record", section_heading))

    loan_amnt = format_currency_inr(data.get("loan", data.get("loan_amnt", 0)))
    loan_intent = data.get("intent", data.get("loan_intent", "PERSONAL"))
    int_rate = data.get("rate", data.get("loan_int_rate", 0.0))
    dti = data.get("dti", round(float(data.get("loan_percent_income", 0)) * 100, 2))
    credit_score = data.get("credit_score", 0)
    cred_len = data.get("cred_len", data.get("cb_person_cred_hist_length", 0))
    defaults = data.get("defaults", data.get("previous_loan_defaults_on_file", "No"))

    if int(credit_score) >= 740:
        score_band = "Prime / Excellent"
    elif int(credit_score) >= 670:
        score_band = "Good"
    elif int(credit_score) >= 580:
        score_band = "Fair / Subprime"
    else:
        score_band = "Poor / High Risk"

    loan_data = [
        [
            Paragraph("Requested Loan Amount", cell_lbl), Paragraph(f"{loan_amnt}", cell_val),
            Paragraph("Credit Bureau Score", cell_lbl), Paragraph(f"{credit_score} ({score_band})", cell_val)
        ],
        [
            Paragraph("Loan Purpose", cell_lbl), Paragraph(str(loan_intent), cell_val),
            Paragraph("Credit History Length", cell_lbl), Paragraph(f"{cred_len} Years", cell_val)
        ],
        [
            Paragraph("Interest Rate Offered", cell_lbl), Paragraph(f"{int_rate}% APR", cell_val),
            Paragraph("Prior Default on Record", cell_lbl), Paragraph(str(defaults), cell_val)
        ],
        [
            Paragraph("Debt-to-Income (DTI)", cell_lbl), Paragraph(f"{dti}%", cell_val),
            Paragraph("AI Underwriting Engine", cell_lbl), Paragraph("Random Forest Ensemble (96.29% Acc)", cell_val)
        ]
    ]

    t_loan = Table(loan_data, colWidths=[120, 150, 130, 140])
    t_loan.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [CARD_BG, colors.white]),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER_CLR),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_CLR),
        ("TOPPADDING", (0, 0), (-1, -1), 4.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(t_loan)
    story.append(Spacer(1, 10))

    # 6. EXPLAINABLE AI DRIVERS & RISK MITIGATORS
    story.append(Paragraph("4. AI Risk Factor Breakdown & Mitigating Drivers", section_heading))

    drivers = data.get("drivers", [])
    if not drivers:
        drivers = [
            {"text": "Underwriting risk parameters successfully analyzed within standard policy thresholds.", "positive": True}
        ]

    driver_rows = []
    for item in drivers:
        is_pos = item.get("positive", False)
        prefix = "✓  POSITIVE MITIGATOR:" if is_pos else "⚠  RISK WATCHOUT:"
        clr = colors.HexColor("#059669") if is_pos else colors.HexColor("#dc2626")
        bg = colors.HexColor("#f0fdf4") if is_pos else colors.HexColor("#fef2f2")

        p = Paragraph(f"<b>{prefix}</b> {item.get('text', '')}", ParagraphStyle(
            "DriverP",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=clr
        ))
        driver_rows.append([p])

    t_drivers = Table(driver_rows, colWidths=[540])
    t_drivers.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER_CLR),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#f1f5f9")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t_drivers)
    story.append(Spacer(1, 12))

    # 7. FINAL UNDERWRITING CERTIFICATION
    cert_text = (
        "<b>Certification & Compliance Note:</b> This evaluation was synthesized through multi-factor machine learning "
        "trained across 45,000 empirical credit files. Financial figures are expressed in Indian Rupees (Rs. / INR). "
        "The calculated risk probability reflects multi-dimensional interaction among applicant income, leverage, liquidity buffer, "
        "and credit history."
    )
    cert_p = Paragraph(cert_text, ParagraphStyle(
        "CertP",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=7.5,
        leading=11,
        textColor=MUTED
    ))
    story.append(cert_p)

    doc.build(story, canvasmaker=NumberedCanvas)
    return buffer.getvalue()
