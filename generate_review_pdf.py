import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class ReviewNumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8.5)
        self.setFillColor(colors.HexColor("#4b5563"))

        if self._pageNumber > 1:
            self.drawString(54, 11 * 72 - 36, "5 Machine Learning Models Review Guide — Loan Risk Assessment")
            self.drawRightString(8.5 * 72 - 54, 11 * 72 - 36, f"Page {self._pageNumber} of {page_count}")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 11 * 72 - 42, 8.5 * 72 - 54, 11 * 72 - 42)

        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(8.5 * 72 - 54, 36, page_text)
        self.drawString(54, 36, "Department of Computer Science and Engineering, Kongu Engineering College")
        self.setStrokeColor(colors.HexColor("#e5e7eb"))
        self.setLineWidth(0.5)
        self.line(54, 48, 8.5 * 72 - 54, 48)

        self.restoreState()

def build_review_pdf():
    pdf_filename = os.path.join(os.path.dirname(__file__), "Loan_Risk_5_Models_Review_Guide.pdf")
    
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Clean Academic Typography
    title_style = ParagraphStyle(
        'ReviewTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        alignment=1,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'ReviewSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10.5,
        leading=14.5,
        alignment=1,
        textColor=colors.HexColor('#475569'),
        spaceAfter=12
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12.5,
        leading=16,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    model_title_style = ParagraphStyle(
        'ModelTitleStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#1e1b4b'),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor('#334155'),
        spaceAfter=6
    )

    def_box_style = ParagraphStyle(
        'DefBoxStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor('#0f172a'),
        backColor=colors.HexColor('#f0fdf4'),
        borderColor=colors.HexColor('#86efac'),
        borderWidth=1,
        borderPadding=8,
        spaceBefore=4,
        spaceAfter=8
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
        alignment=1
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#1e293b')
    )

    table_cell_center = ParagraphStyle(
        'TableCellCenter',
        parent=table_cell_style,
        alignment=1
    )

    story = []

    # Title Banner
    story.append(Spacer(1, 5))
    story.append(Paragraph("5 Machine Learning Models — Quick Review Guide", title_style))
    story.append(Paragraph("<b>Project:</b> Loan Default Risk Prediction & Financial Guidance System<br/><i>Definitions, Explanations, Strengths, and Metrics for Review Presentation</i>", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#6366f1'), spaceBefore=2, spaceAfter=12))

    # Summary Intro
    story.append(Paragraph("Overview of the 5 Evaluated Models", h1_style))
    story.append(Paragraph(
        "In our Loan Risk Assessment project, we trained and evaluated <b>5 distinct Machine Learning models</b> to classify loan applicants as either "
        "<b>Safe (Approved)</b> or <b>High Default Risk (Declined)</b> based on 18 financial and demographic features. Below is the definition, simple explanation, strengths, and accuracy metrics for each model.",
        body_style
    ))

    # MODEL 1
    story.append(Spacer(1, 4))
    story.append(Paragraph("1. Random Forest Classifier (Selected Production Model)", model_title_style))
    m1_def = (
        "<b>Easy Definition:</b> Random Forest is an <b>ensemble model</b> that creates a 'forest' of 100 independent decision trees "
        "trained on random subsets of data. Each tree makes its own prediction, and the final loan decision is decided by <b>majority voting</b>.<br/><br/>"
        "<b>Simple Explanation:</b> Imagine asking 100 different loan experts for their opinion. If 90 experts say the applicant is safe and 10 say risky, "
        "the system approves the loan based on the majority vote! This makes it extremely reliable and accurate."
    )
    story.append(Paragraph(m1_def, def_box_style))
    story.append(Paragraph(
        "• <b>Key Strengths:</b> Highest accuracy, zero overfitting risk, handles complex non-linear financial patterns effortlessly.<br/>"
        "• <b>Accuracy:</b> <b>100.00%</b> | <b>Precision:</b> 100.00% | <b>Recall:</b> 100.00% | <b>F1-Score:</b> 100.00%<br/>"
        "• <b>Confusion Matrix:</b> <code>[[6990 True Safe, 0 False Risk], [0 False Safe, 2010 True Risk]]</code>",
        body_style
    ))

    # MODEL 2
    story.append(Spacer(1, 4))
    story.append(Paragraph("2. XGBoost Classifier (Extreme Gradient Boosting)", model_title_style))
    m2_def = (
        "<b>Easy Definition:</b> XGBoost stands for <b>eXtreme Gradient Boosting</b>. It builds decision trees <b>one after another in sequence</b>, "
        "where each new tree specifically focuses on correcting the mistakes made by the previous trees.<br/><br/>"
        "<b>Simple Explanation:</b> Imagine a student taking a practice test. After the 1st attempt, they review their mistakes and focus only on the hard questions "
        "in the 2nd attempt, making them smarter with every round! XGBoost does the exact same thing with decision trees."
    )
    story.append(Paragraph(m2_def, def_box_style))
    story.append(Paragraph(
        "• <b>Key Strengths:</b> Ultra-fast speed, high accuracy, built-in regularization penalty to prevent overfitting.<br/>"
        "• <b>Accuracy:</b> <b>96.93%</b> | <b>Precision:</b> 96.36% | <b>Recall:</b> 89.65% | <b>F1-Score:</b> 92.89%<br/>"
        "• <b>Confusion Matrix:</b> <code>[[6922 True Safe, 68 False Risk], [208 False Safe, 1802 True Risk]]</code>",
        body_style
    ))

    # MODEL 3
    story.append(Spacer(1, 4))
    story.append(Paragraph("3. LightGBM Classifier (Fast Leaf-Wise Boosting)", model_title_style))
    m3_def = (
        "<b>Easy Definition:</b> LightGBM (Light Gradient Boosting Machine) is a boosting framework that grows decision trees <b>leaf-wise</b> "
        "(expanding the node with maximum loss reduction) instead of level-wise.<br/><br/>"
        "<b>Simple Explanation:</b> Instead of building a big symmetrical tree, it quickly focuses on the specific rules that reduce prediction error the fastest, "
        "making it memory-light and super fast on large tabular datasets."
    )
    story.append(Paragraph(m3_def, def_box_style))
    story.append(Paragraph(
        "• <b>Key Strengths:</b> Low memory usage, extremely fast training speed, handles large datasets efficiently.<br/>"
        "• <b>Accuracy:</b> <b>94.56%</b> | <b>Precision:</b> 92.27% | <b>Recall:</b> 82.54% | <b>F1-Score:</b> 87.13%<br/>"
        "• <b>Confusion Matrix:</b> <code>[[6851 True Safe, 139 False Risk], [351 False Safe, 1659 True Risk]]</code>",
        body_style
    ))

    # MODEL 4
    story.append(Spacer(1, 4))
    story.append(Paragraph("4. Gradient Boosting Classifier (Classic Boosting)", model_title_style))
    m4_def = (
        "<b>Easy Definition:</b> Gradient Boosting builds an additive ensemble of weak decision trees step-by-step by minimizing loss using <b>gradient descent</b>.<br/><br/>"
        "<b>Simple Explanation:</b> Each decision tree attempts to predict the residual error (remaining mistakes) of all earlier decision trees combined, "
        "gradually improving overall loan default predictions step by step."
    )
    story.append(Paragraph(m4_def, def_box_style))
    story.append(Paragraph(
        "• <b>Key Strengths:</b> Classic boosting baseline, high prediction stability, built directly into scikit-learn.<br/>"
        "• <b>Accuracy:</b> <b>92.46%</b> | <b>Precision:</b> 88.27% | <b>Recall:</b> 76.37% | <b>F1-Score:</b> 81.89%<br/>"
        "• <b>Confusion Matrix:</b> <code>[[6786 True Safe, 204 False Risk], [475 False Safe, 1535 True Risk]]</code>",
        body_style
    ))

    # MODEL 5
    story.append(Spacer(1, 4))
    story.append(Paragraph("5. Logistic Regression (Linear Financial Baseline)", model_title_style))
    m5_def = (
        "<b>Easy Definition:</b> Logistic Regression is a statistical linear model that calculates a weighted sum of inputs and converts it into a <b>probability score between 0 and 1</b> using the Sigmoid curve.<br/><br/>"
        "<b>Simple Explanation:</b> It draws a straight decision boundary line separating safe borrowers from risky borrowers based on income, credit score, and debt ratios. "
        "It serves as our baseline comparison model."
    )
    story.append(Paragraph(m5_def, def_box_style))
    story.append(Paragraph(
        "• <b>Key Strengths:</b> Simple, highly interpretable, traditional banking baseline.<br/>"
        "• <b>Accuracy:</b> <b>89.39%</b> | <b>Precision:</b> 77.35% | <b>Recall:</b> 74.23% | <b>F1-Score:</b> 75.76%<br/>"
        "• <b>Confusion Matrix:</b> <code>[[6553 True Safe, 437 False Risk], [518 False Safe, 1492 True Risk]]</code>",
        body_style
    ))

    # COMPARISON TABLE
    story.append(Spacer(1, 8))
    story.append(Paragraph("5-Model Comparative Performance Summary Table", h1_style))

    t_data = [
        [Paragraph("Model Name", table_header_style), Paragraph("Type / Family", table_header_style), Paragraph("Accuracy (%)", table_header_style), Paragraph("Precision (%)", table_header_style), Paragraph("Recall (%)", table_header_style), Paragraph("F1 Score (%)", table_header_style)],
        [Paragraph("<b>Random Forest</b>", table_cell_style), Paragraph("Bagging Ensemble", table_cell_style), Paragraph("<b>100.00%</b>", table_cell_center), Paragraph("<b>100.00%</b>", table_cell_center), Paragraph("<b>100.00%</b>", table_cell_center), Paragraph("<b>100.00%</b>", table_cell_center)],
        [Paragraph("XGBoost", table_cell_style), Paragraph("Gradient Boosting", table_cell_style), Paragraph("96.93%", table_cell_center), Paragraph("96.36%", table_cell_center), Paragraph("89.65%", table_cell_center), Paragraph("92.89%", table_cell_center)],
        [Paragraph("LightGBM", table_cell_style), Paragraph("Leaf-wise Boosting", table_cell_style), Paragraph("94.56%", table_cell_center), Paragraph("92.27%", table_cell_center), Paragraph("82.54%", table_cell_center), Paragraph("87.13%", table_cell_center)],
        [Paragraph("Gradient Boosting", table_cell_style), Paragraph("Classic Boosting", table_cell_style), Paragraph("92.46%", table_cell_center), Paragraph("88.27%", table_cell_center), Paragraph("76.37%", table_cell_center), Paragraph("81.89%", table_cell_center)],
        [Paragraph("Logistic Regression", table_cell_style), Paragraph("Linear Baseline", table_cell_style), Paragraph("89.39%", table_cell_center), Paragraph("77.35%", table_cell_center), Paragraph("74.23%", table_cell_center), Paragraph("75.76%", table_cell_center)]
    ]
    t = Table(t_data, colWidths=[120, 110, 70, 70, 65, 69])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e293b')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#ecfdf5'), colors.white, colors.HexColor('#f8fafc'), colors.white, colors.HexColor('#f8fafc')]),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))

    # REVIEW DEFENSE SUMMARY
    story.append(Paragraph("Why Tree Ensembles Win (Key Answer for Examiner)", h1_style))
    defense_p = (
        "<b>Examiner Question:</b> <i>Why do Random Forest (100.00%) and XGBoost (96.93%) perform much better than Logistic Regression (89.39%)?</i><br/><br/>"
        "<b>Answer:</b> Credit risk datasets have complex non-linear relationships (e.g., how high income interacts with low credit score vs high savings balance). "
        "Linear models like Logistic Regression can only draw a single straight decision boundary line. In contrast, Tree Ensemble models (Random Forest & XGBoost) "
        "create non-linear decision splits that capture multi-dimensional risk patterns accurately."
    )
    story.append(Paragraph(defense_p, def_box_style))

    doc.build(story, canvasmaker=ReviewNumberedCanvas)
    print(f"Review PDF generated successfully: {pdf_filename}")

if __name__ == '__main__':
    build_review_pdf()
