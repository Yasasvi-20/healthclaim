from sqlalchemy import text
from backend.database import engine
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from pathlib import Path



# ============================================================
# Output Folder
# ============================================================

OUTPUT_DIR = Path("generated_claims")
OUTPUT_DIR.mkdir(exist_ok=True)


# ============================================================
# Number of Claims
# ============================================================

VALID_COUNT = 10
REVIEW_COUNT = 7
FAILED_COUNT = 3

TOTAL_COUNT = (
    VALID_COUNT
    + REVIEW_COUNT
    + FAILED_COUNT
)


# ============================================================
# Clear Previously Generated PDFs
# ============================================================

for old_file in OUTPUT_DIR.glob("*.pdf"):
    old_file.unlink()


# ============================================================
# Select 20 Different Claims From MySQL
# ============================================================

query = text(f"""
    SELECT
        c.id AS claim_id,
        c.patientid AS patient_id,
        c.providerid AS provider_id,
        c.primarypatientinsuranceid AS payer_id,
        c.servicedate AS service_date,

        COALESCE(
            NULLIF(
                SUM(
                    CASE
                        WHEN UPPER(ct.type) = 'CHARGE'
                        THEN ct.amount
                        ELSE 0
                    END
                ),
                0
            ),
            SUM(ct.amount),
            0
        ) AS claimed_amount

    FROM claims c

    LEFT JOIN claims_transactions ct
        ON c.id = ct.claimid

    WHERE c.id IS NOT NULL
      AND c.patientid IS NOT NULL
      AND c.providerid IS NOT NULL
      AND c.primarypatientinsuranceid IS NOT NULL

    GROUP BY
        c.id,
        c.patientid,
        c.providerid,
        c.primarypatientinsuranceid,
        c.servicedate

    ORDER BY RAND()

    LIMIT {TOTAL_COUNT}
""")


with engine.connect() as connection:
    claims = connection.execute(
        query
    ).mappings().all()


if len(claims) < TOTAL_COUNT:

    print(
        f"Only {len(claims)} eligible claims "
        f"were found."
    )

    print(
        f"{TOTAL_COUNT} claims are required."
    )

    exit()


# ============================================================
# Create Normal PDF
# ============================================================

def create_pdf(claim, pdf_path):

    pdf = canvas.Canvas(
        str(pdf_path),
        pagesize=letter
    )


    # --------------------------------------------------------
    # Title
    # --------------------------------------------------------

    pdf.setFont(
        "Helvetica-Bold",
        16
    )

    pdf.drawString(
        70,
        750,
        "Synthetic Healthcare Claim"
    )


    # --------------------------------------------------------
    # Claim Information
    # --------------------------------------------------------

    pdf.setFont(
        "Helvetica",
        11
    )

    y = 700


    fields = [

        (
            "Claim ID",
            claim["claim_id"]
        ),

        (
            "Patient ID",
            claim["patient_id"]
        ),

        (
            "Provider ID",
            claim["provider_id"]
        ),

        (
            "Payer ID",
            claim["payer_id"]
        ),

        (
            "Service Date",
            claim["service_date"]
        ),

        (
            "Total Claim Cost",
            claim["claimed_amount"]
        )
    ]


    for label, value in fields:

        pdf.drawString(
            70,
            y,
            f"{label}: {value}"
        )

        y -= 30


    # --------------------------------------------------------
    # Footer
    # --------------------------------------------------------

    pdf.setFont(
        "Helvetica-Oblique",
        9
    )

    pdf.drawString(
        70,
        100,
        "Synthetic claim generated from healthcare reference data."
    )


    pdf.save()


# ============================================================
# Filename Helper
# ============================================================

def get_filename(
    original_patient_id,
    claim_id
):

    return (
        f"claim_"
        f"{original_patient_id}_"
        f"{claim_id}.pdf"
    )


# ============================================================
# Keep Expected Results Only In Terminal
# ============================================================

expected_results = []


# ============================================================
# 1. Generate 10 Correct Claims
# ============================================================

for index in range(
    VALID_COUNT
):

    claim = dict(
        claims[index]
    )


    original_patient_id = str(
        claim["patient_id"]
    )

    claim_id = str(
        claim["claim_id"]
    )


    filename = get_filename(
        original_patient_id,
        claim_id
    )

    pdf_path = (
        OUTPUT_DIR
        /
        filename
    )


    create_pdf(
        claim,
        pdf_path
    )


    expected_results.append(
        (
            filename,
            "VALIDATED"
        )
    )


# ============================================================
# 2. Generate 7 Claims With Data Problems
# ============================================================

for index in range(
    REVIEW_COUNT
):

    source_index = (
        VALID_COUNT
        + index
    )


    claim = dict(
        claims[source_index]
    )


    # Keep ORIGINAL values for filename
    original_patient_id = str(
        claim["patient_id"]
    )

    claim_id = str(
        claim["claim_id"]
    )


    # --------------------------------------------------------
    # Introduce Different Validation Errors
    # --------------------------------------------------------

    error_type = (
        index % 4
    )


    # Wrong patient
    if error_type == 0:

        claim["patient_id"] = (
            f"OUTSIDE-PATIENT-{index + 1:03d}"
        )


    # Wrong provider
    elif error_type == 1:

        claim["provider_id"] = (
            f"OUTSIDE-PROVIDER-{index + 1:03d}"
        )


    # Wrong payer
    elif error_type == 2:

        claim["payer_id"] = (
            f"OUTSIDE-PAYER-{index + 1:03d}"
        )


    # Wrong amount
    else:

        correct_amount = float(
            claim["claimed_amount"]
            or 0
        )

        claim["claimed_amount"] = (
            correct_amount
            + 500.00
        )


    filename = get_filename(
        original_patient_id,
        claim_id
    )


    pdf_path = (
        OUTPUT_DIR
        /
        filename
    )


    create_pdf(
        claim,
        pdf_path
    )


    expected_results.append(
        (
            filename,
            "NEEDS_REVIEW"
        )
    )


# ============================================================
# 3. Generate 3 Processing-Failure PDFs
# ============================================================

for index in range(
    FAILED_COUNT
):

    source_index = (
        VALID_COUNT
        + REVIEW_COUNT
        + index
    )


    claim = dict(
        claims[source_index]
    )


    original_patient_id = str(
        claim["patient_id"]
    )

    claim_id = str(
        claim["claim_id"]
    )


    filename = get_filename(
        original_patient_id,
        claim_id
    )


    pdf_path = (
        OUTPUT_DIR
        /
        filename
    )


    # --------------------------------------------------------
    # Intentionally invalid PDF content
    #
    # Filename still looks like a normal claim.
    # Extension is .pdf, but contents are not a real PDF.
    # --------------------------------------------------------

    with open(
        pdf_path,
        "wb"
    ) as file:

        file.write(
            b"""
            Synthetic Healthcare Claim

            This file intentionally contains
            invalid PDF data for testing the
            HCIMS processing failure workflow.
            """
        )


    expected_results.append(
        (
            filename,
            "FAILED"
        )
    )


# ============================================================
# Final Report
# ============================================================

print(
    "\n"
    "=============================================="
)

print(
    "HCIMS CLAIM TEST BATCH GENERATED"
)

print(
    "==============================================\n"
)


print(
    f"Total files: {TOTAL_COUNT}"
)

print(
    f"Expected VALIDATED: {VALID_COUNT}"
)

print(
    f"Expected NEEDS_REVIEW: {REVIEW_COUNT}"
)

print(
    f"Expected FAILED: {FAILED_COUNT}"
)


print(
    "\nGenerated folder:"
)

print(
    OUTPUT_DIR.resolve()
)


print(
    "\n"
    "----------------------------------------------"
)

print(
    "EXPECTED RESULTS"
)

print(
    "----------------------------------------------"
)


for number, (
    filename,
    expected_status
) in enumerate(
    expected_results,
    start=1
):

    print(
        f"{number:02d}. "
        f"{filename}"
    )

    print(
        f"    Expected: "
        f"{expected_status}"
    )


print(
    "\n"
    "=============================================="
)

print(
    "Generation completed successfully."
)

print(
    "=============================================="
)