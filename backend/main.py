from pathlib import Path
import shutil
import uuid

import pdfplumber

from fastapi import FastAPI
from fastapi import UploadFile
from fastapi import File
from fastapi import HTTPException

from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import text

from database import engine

# ============================================================
# FastAPI
# ============================================================

app = FastAPI(
    title="MediClaim Healthcare Claims Intake and Validation API",
    version="1.1.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Paths
# ============================================================

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent

UPLOAD_DIR = PROJECT_DIR / "uploads"

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# Helper: PDF extraction
# ============================================================

def extract_claim_fields(pdf_path: Path):

    extracted = {
        "claim_id": None,
        "patient_id": None,
        "provider_id": None,
        "payer_id": None,
        "claimed_amount": None
    }

    text_content = ""

    with pdfplumber.open(pdf_path) as pdf:

        for page in pdf.pages:

            page_text = page.extract_text()

            if page_text:
                text_content += page_text + "\n"

    for line in text_content.splitlines():

        line = line.strip()

        if line.startswith("Claim ID:"):

            extracted["claim_id"] = (
                line.split(":", 1)[1].strip()
            )

        elif line.startswith("Patient ID:"):

            extracted["patient_id"] = (
                line.split(":", 1)[1].strip()
            )

        elif line.startswith("Provider ID:"):

            extracted["provider_id"] = (
                line.split(":", 1)[1].strip()
            )

        elif line.startswith("Payer ID:"):

            value = (
                line.split(":", 1)[1].strip()
            )

            if value.lower() not in {
                "",
                "none",
                "null"
            }:
                extracted["payer_id"] = value

        elif line.startswith("Total Claim Cost:"):

            value = (
                line.split(":", 1)[1]
                .strip()
                .replace("$", "")
                .replace(",", "")
            )

            try:
                extracted["claimed_amount"] = float(
                    value
                )

            except ValueError:
                extracted["claimed_amount"] = None

    return extracted


# ============================================================
# Helper: get original Synthea claim
# ============================================================

def get_original_claim(claim_id):

    query = text("""
        SELECT
            c.id AS claim_id,
            c.patientid AS patient_id,
            c.providerid AS provider_id,
            c.primarypatientinsuranceid AS payer_id,

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

        WHERE c.id = :claim_id

        GROUP BY
            c.id,
            c.patientid,
            c.providerid,
            c.primarypatientinsuranceid
    """)

    with engine.connect() as connection:

        result = connection.execute(
            query,
            {
                "claim_id": claim_id
            }
        ).mappings().first()

    return result

from fastapi.responses import FileResponse

@app.get("/documents/{document_id}/file")
def get_document_file(document_id: int):

    query = text("""
        SELECT
            original_filename,
            file_path
        FROM claim_documents
        WHERE document_id = :document_id
    """)

    with engine.connect() as connection:

        document = connection.execute(
            query,
            {
                "document_id": document_id
            }
        ).mappings().first()


    if document is None:

        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )


    file_path = Path(
        document["file_path"]
    )


    if not file_path.exists():

        raise HTTPException(
            status_code=404,
            detail="PDF file not found"
        )


    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=document["original_filename"],
        content_disposition_type="inline"
    )

# ============================================================
# Helper: duplicate detection
# ============================================================

def is_duplicate(claim_id):

    if not claim_id:
        return False

    query = text("""
        SELECT COUNT(*) AS total

        FROM extracted_fields ef

        INNER JOIN claim_documents cd
            ON ef.document_id = cd.document_id

        WHERE ef.claim_id = :claim_id

          AND (
                (
                    cd.processing_status = 'COMPLETED'
                    AND cd.validation_status IN (
                        'VALIDATED',
                        'DUPLICATE'
                    )
                )
                OR cd.status IN (
                    'VALIDATED',
                    'DUPLICATE'
                )
          )
    """)

    with engine.connect() as connection:

        result = connection.execute(
            query,
            {
                "claim_id": claim_id
            }
        ).mappings().first()

    return result["total"] > 0


# ============================================================
# Helper: claim validation
# ============================================================

def validate_claim(extracted):

    issues = []

    claim_id = extracted.get("claim_id")
    patient_id = extracted.get("patient_id")
    provider_id = extracted.get("provider_id")
    payer_id = extracted.get("payer_id")
    claimed_amount = extracted.get("claimed_amount")


    # --------------------------------------------------------
    # Claim ID is required because it identifies the
    # reference claim in the structured healthcare records.
    # --------------------------------------------------------

    if not claim_id:

        issues.append({
            "field_name":
                "claim_id",

            "expected_value":
                "A valid claim ID",

            "extracted_value":
                None,

            "issue_type":
                "MISSING_FIELD",

            "issue_message":
                "Claim ID was not found in the uploaded PDF."
        })

        return "NEEDS_REVIEW", issues


    # --------------------------------------------------------
    # Find the reference claim in Synthea/MySQL
    # --------------------------------------------------------

    original = get_original_claim(
        claim_id
    )


    if original is None:

        issues.append({
            "field_name":
                "claim_id",

            "expected_value":
                "Claim ID present in the healthcare database",

            "extracted_value":
                str(claim_id),

            "issue_type":
                "CLAIM_NOT_FOUND",

            "issue_message":
                "The extracted Claim ID does not exist in the healthcare records."
        })

        return "NEEDS_REVIEW", issues


    # --------------------------------------------------------
    # Patient ID
    # --------------------------------------------------------

    expected_patient = (
        str(original["patient_id"])
        if original["patient_id"] is not None
        else None
    )

    if not patient_id:

        issues.append({
            "field_name":
                "patient_id",

            "expected_value":
                expected_patient,

            "extracted_value":
                None,

            "issue_type":
                "MISSING_FIELD",

            "issue_message":
                "Patient ID is missing from the uploaded claim."
        })

    elif str(patient_id) != expected_patient:

        issues.append({
            "field_name":
                "patient_id",

            "expected_value":
                expected_patient,

            "extracted_value":
                str(patient_id),

            "issue_type":
                "VALUE_MISMATCH",

            "issue_message":
                "Patient ID does not match the patient associated with this claim."
        })


    # --------------------------------------------------------
    # Provider ID
    # --------------------------------------------------------

    expected_provider = (
        str(original["provider_id"])
        if original["provider_id"] is not None
        else None
    )

    if not provider_id:

        issues.append({
            "field_name":
                "provider_id",

            "expected_value":
                expected_provider,

            "extracted_value":
                None,

            "issue_type":
                "MISSING_FIELD",

            "issue_message":
                "Provider ID is missing from the uploaded claim."
        })

    elif str(provider_id) != expected_provider:

        issues.append({
            "field_name":
                "provider_id",

            "expected_value":
                expected_provider,

            "extracted_value":
                str(provider_id),

            "issue_type":
                "VALUE_MISMATCH",

            "issue_message":
                "Provider ID does not match the provider associated with this claim."
        })


    # --------------------------------------------------------
    # Payer ID
    #
    # Some Synthea records can legitimately have no primary
    # payer, so NULL/None is handled separately.
    # --------------------------------------------------------

    expected_payer = (
        str(original["payer_id"])
        if original["payer_id"] is not None
        else None
    )

    extracted_payer = (
        str(payer_id)
        if payer_id is not None
        else None
    )

    if expected_payer is not None and extracted_payer is None:

        issues.append({
            "field_name":
                "payer_id",

            "expected_value":
                expected_payer,

            "extracted_value":
                None,

            "issue_type":
                "MISSING_FIELD",

            "issue_message":
                "Payer ID is missing from the uploaded claim."
        })

    elif extracted_payer != expected_payer:

        issues.append({
            "field_name":
                "payer_id",

            "expected_value":
                expected_payer,

            "extracted_value":
                extracted_payer,

            "issue_type":
                "VALUE_MISMATCH",

            "issue_message":
                "Payer ID does not match the insurance record associated with this claim."
        })


    # --------------------------------------------------------
    # Claim Amount
    # --------------------------------------------------------

    expected_amount = float(
        original["claimed_amount"] or 0
    )

    if claimed_amount is None:

        issues.append({
            "field_name":
                "claimed_amount",

            "expected_value":
                f"{expected_amount:.2f}",

            "extracted_value":
                None,

            "issue_type":
                "MISSING_FIELD",

            "issue_message":
                "Total claim cost could not be extracted from the uploaded PDF."
        })

    elif abs(
        float(claimed_amount)
        -
        expected_amount
    ) > 0.01:

        issues.append({
            "field_name":
                "claimed_amount",

            "expected_value":
                f"{expected_amount:.2f}",

            "extracted_value":
                f"{float(claimed_amount):.2f}",

            "issue_type":
                "VALUE_MISMATCH",

            "issue_message":
                "Total claim cost does not match the amount in the healthcare records."
        })


    # --------------------------------------------------------
    # Final validation result
    # --------------------------------------------------------

    if issues:
        return "NEEDS_REVIEW", issues

    return "VALIDATED", []


# ============================================================
# Root
# ============================================================

@app.get("/")
def root():

    return {
        "message":
            "Healthcare Claims API is running"
    }


# ============================================================
# Health
# ============================================================

@app.get("/health")
def health():

    try:

        with engine.connect() as connection:

            connection.execute(
                text("SELECT 1")
            )

        return {
            "api": "running",
            "database": "connected"
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ============================================================
# Dashboard
# ============================================================

@app.get("/dashboard")
def dashboard():

    query = text("""
        SELECT
            COUNT(*) AS total_claims,

            COALESCE(
                SUM(
                    CASE
                        WHEN COALESCE(
                            validation_status,
                            CASE
                                WHEN status IN (
                                    'VALIDATED',
                                    'NEEDS_REVIEW',
                                    'DUPLICATE'
                                )
                                THEN status
                                ELSE NULL
                            END
                        ) = 'VALIDATED'
                        THEN 1
                        ELSE 0
                    END
                ),
                0
            ) AS validated,

            COALESCE(
                SUM(
                    CASE
                        WHEN COALESCE(
                            validation_status,
                            CASE
                                WHEN status IN (
                                    'VALIDATED',
                                    'NEEDS_REVIEW',
                                    'DUPLICATE'
                                )
                                THEN status
                                ELSE NULL
                            END
                        ) = 'NEEDS_REVIEW'
                        THEN 1
                        ELSE 0
                    END
                ),
                0
            ) AS needs_review,

            COALESCE(
                SUM(
                    CASE
                        WHEN COALESCE(
                            validation_status,
                            CASE
                                WHEN status IN (
                                    'VALIDATED',
                                    'NEEDS_REVIEW',
                                    'DUPLICATE'
                                )
                                THEN status
                                ELSE NULL
                            END
                        ) = 'DUPLICATE'
                        THEN 1
                        ELSE 0
                    END
                ),
                0
            ) AS duplicates,

            COALESCE(
                SUM(
                    CASE
                        WHEN processing_status = 'FAILED'
                             OR status = 'FAILED'
                        THEN 1
                        ELSE 0
                    END
                ),
                0
            ) AS failed

        FROM claim_documents
    """)

    with engine.connect() as connection:

        result = connection.execute(
            query
        ).mappings().first()

    return dict(result)


# ============================================================
# Claims list
# ============================================================

@app.get("/claims")
def get_claims():

    query = text("""
        SELECT
            cd.document_id,
            cd.original_filename,
            cd.upload_time,

            cd.processing_status,
            cd.validation_status,

            CASE
                WHEN cd.processing_status = 'FAILED'
                    THEN 'FAILED'

                WHEN cd.processing_status IN (
                    'QUEUED',
                    'PROCESSING'
                )
                AND cd.validation_status IS NULL
                AND cd.status NOT IN (
                    'VALIDATED',
                    'NEEDS_REVIEW',
                    'DUPLICATE',
                    'FAILED'
                )
                    THEN cd.processing_status

                WHEN cd.validation_status IS NOT NULL
                    THEN cd.validation_status

                ELSE cd.status
            END AS status,

            ef.claim_id,
            ef.patient_id,
            ef.provider_id,
            ef.payer_id,
            ef.claimed_amount

        FROM claim_documents cd

        LEFT JOIN extracted_fields ef
            ON cd.document_id = ef.document_id

        ORDER BY cd.document_id DESC

        LIMIT 100
    """)

    with engine.connect() as connection:

        rows = connection.execute(
            query
        ).mappings().all()

    return [
        dict(row)
        for row in rows
    ]


# ============================================================
# Claim details
# ============================================================

@app.get("/claims/{document_id}")
def get_claim(document_id: int):

    claim_query = text("""
        SELECT
            cd.document_id,
            cd.original_filename,
            cd.file_path,
            cd.upload_time,

            cd.processing_status,
            cd.validation_status,

            CASE
                WHEN cd.processing_status = 'FAILED'
                    THEN 'FAILED'

                WHEN cd.processing_status IN (
                    'QUEUED',
                    'PROCESSING'
                )
                AND cd.validation_status IS NULL
                AND cd.status NOT IN (
                    'VALIDATED',
                    'NEEDS_REVIEW',
                    'DUPLICATE',
                    'FAILED'
                )
                    THEN cd.processing_status

                WHEN cd.validation_status IS NOT NULL
                    THEN cd.validation_status

                ELSE cd.status
            END AS status,

            ef.claim_id,
            ef.patient_id,
            ef.provider_id,
            ef.payer_id,
            ef.claimed_amount

        FROM claim_documents cd

        LEFT JOIN extracted_fields ef
            ON cd.document_id = ef.document_id

        WHERE cd.document_id = :document_id
    """)


    issue_query = text("""
        SELECT

            issue_id,
            field_name,
            expected_value,
            extracted_value,
            issue_type,
            issue_message,
            created_at

        FROM validation_issues

        WHERE document_id
              = :document_id

        ORDER BY issue_id
    """)


    with engine.connect() as connection:

        claim = connection.execute(
            claim_query,
            {
                "document_id":
                    document_id
            }
        ).mappings().first()


        issues = connection.execute(
            issue_query,
            {
                "document_id":
                    document_id
            }
        ).mappings().all()


    if claim is None:

        raise HTTPException(
            status_code=404,
            detail="Claim not found"
        )


    return {
        "claim":
            dict(claim),

        "validation_issues":
            [
                dict(issue)
                for issue in issues
            ]
    }


# ============================================================
# Upload + validation
# ============================================================

@app.post("/claims/upload")
def upload_claim(
    file: UploadFile = File(...)
):

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No file selected"
        )


    if (
        not file.filename
        .lower()
        .endswith(".pdf")
    ):

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )


    stored_filename = (
        f"{uuid.uuid4()}_"
        f"{file.filename}"
    )

    file_path = (
        UPLOAD_DIR
        /
        stored_filename
    )

    document_id = None


    try:

        # ----------------------------------------------------
        # 1. Save PDF locally
        # ----------------------------------------------------

        with open(
            file_path,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )


        # ----------------------------------------------------
        # 2. Insert document as QUEUED
        #
        # The legacy status column is temporarily maintained
        # so the existing MediClaim frontend still works.
        # ----------------------------------------------------

        with engine.begin() as connection:

            result = connection.execute(
                text("""
                    INSERT INTO claim_documents
                    (
                        original_filename,
                        stored_filename,
                        file_path,
                        status,
                        processing_status,
                        validation_status
                    )

                    VALUES
                    (
                        :original_filename,
                        :stored_filename,
                        :file_path,
                        'QUEUED',
                        'QUEUED',
                        NULL
                    )
                """),

                {
                    "original_filename":
                        file.filename,

                    "stored_filename":
                        stored_filename,

                    "file_path":
                        str(file_path)
                }
            )

            document_id = result.lastrowid


            connection.execute(
                text("""
                    INSERT INTO processing_events
                    (
                        document_id,
                        event_type,
                        message
                    )

                    VALUES
                    (
                        :document_id,
                        'QUEUED',
                        'Claim accepted and queued for processing'
                    )
                """),

                {
                    "document_id":
                        document_id
                }
            )


        # ----------------------------------------------------
        # 3. Move QUEUED -> PROCESSING
        # ----------------------------------------------------

        with engine.begin() as connection:

            connection.execute(
                text("""
                    UPDATE claim_documents

                    SET
                        status = 'PROCESSING',
                        processing_status = 'PROCESSING',
                        validation_status = NULL

                    WHERE document_id = :document_id
                """),

                {
                    "document_id":
                        document_id
                }
            )


            connection.execute(
                text("""
                    INSERT INTO processing_events
                    (
                        document_id,
                        event_type,
                        message
                    )

                    VALUES
                    (
                        :document_id,
                        'PROCESSING_STARTED',
                        'Claim processing started'
                    )
                """),

                {
                    "document_id":
                        document_id
                }
            )


        # ----------------------------------------------------
        # 4. Extract fields from the actual PDF contents
        # ----------------------------------------------------

        extracted = (
            extract_claim_fields(
                file_path
            )
        )


        # ----------------------------------------------------
        # 5. Duplicate check BEFORE storing the current
        #    document's extracted claim record
        # ----------------------------------------------------

        duplicate = is_duplicate(
            extracted["claim_id"]
        )


        # ----------------------------------------------------
        # 6. Save extracted fields
        # ----------------------------------------------------

        with engine.begin() as connection:

            connection.execute(
                text("""
                    INSERT INTO extracted_fields
                    (
                        document_id,
                        claim_id,
                        patient_id,
                        provider_id,
                        payer_id,
                        claimed_amount
                    )

                    VALUES
                    (
                        :document_id,
                        :claim_id,
                        :patient_id,
                        :provider_id,
                        :payer_id,
                        :claimed_amount
                    )
                """),

                {
                    "document_id":
                        document_id,

                    "claim_id":
                        extracted["claim_id"],

                    "patient_id":
                        extracted["patient_id"],

                    "provider_id":
                        extracted["provider_id"],

                    "payer_id":
                        extracted["payer_id"],

                    "claimed_amount":
                        extracted["claimed_amount"]
                }
            )


        # ----------------------------------------------------
        # 7. Validation
        # ----------------------------------------------------

        if duplicate:

            validation_status = "DUPLICATE"

            issues = [{
                "field_name":
                    "claim_id",

                "expected_value":
                    "Unique claim",

                "extracted_value":
                    extracted["claim_id"],

                "issue_type":
                    "DUPLICATE_CLAIM",

                "issue_message":
                    "This claim was already validated previously."
            }]

        else:

            (
                validation_status,
                issues
            ) = validate_claim(
                extracted
            )


        # ----------------------------------------------------
        # 8. Save validation issues
        # ----------------------------------------------------

        if issues:

            with engine.begin() as connection:

                for issue in issues:

                    connection.execute(
                        text("""
                            INSERT INTO validation_issues
                            (
                                document_id,
                                field_name,
                                expected_value,
                                extracted_value,
                                issue_type,
                                issue_message
                            )

                            VALUES
                            (
                                :document_id,
                                :field_name,
                                :expected_value,
                                :extracted_value,
                                :issue_type,
                                :issue_message
                            )
                        """),

                        {
                            "document_id":
                                document_id,

                            "field_name":
                                issue["field_name"],

                            "expected_value":
                                issue["expected_value"],

                            "extracted_value":
                                issue["extracted_value"],

                            "issue_type":
                                issue["issue_type"],

                            "issue_message":
                                issue["issue_message"]
                        }
                    )


        # ----------------------------------------------------
        # Validation audit event
        # ----------------------------------------------------

        with engine.begin() as connection:

            connection.execute(
                text("""
                    INSERT INTO processing_events
                    (
                        document_id,
                        event_type,
                        message
                    )

                    VALUES
                    (
                        :document_id,
                        'VALIDATION_COMPLETED',
                        :message
                    )
                """),

                {
                    "document_id":
                        document_id,

                    "message":
                        (
                            f"Validation result: {validation_status}. "
                            f"Issues found: {len(issues)}"
                        )
                }
            )


        # ----------------------------------------------------
        # 9. Processing successfully completed
        #
        # processing_status = COMPLETED
        # validation_status = VALIDATED / NEEDS_REVIEW /
        #                     DUPLICATE
        #
        # status is still updated for current frontend
        # compatibility.
        # ----------------------------------------------------

        with engine.begin() as connection:

            connection.execute(
                text("""
                    UPDATE claim_documents

                    SET
                        status = :legacy_status,
                        processing_status = 'COMPLETED',
                        validation_status = :validation_status

                    WHERE document_id = :document_id
                """),

                {
                    "legacy_status":
                        validation_status,

                    "validation_status":
                        validation_status,

                    "document_id":
                        document_id
                }
            )


            connection.execute(
                text("""
                    INSERT INTO processing_events
                    (
                        document_id,
                        event_type,
                        message
                    )

                    VALUES
                    (
                        :document_id,
                        'PROCESSING_COMPLETED',
                        :message
                    )
                """),

                {
                    "document_id":
                        document_id,

                    "message":
                        (
                            "Claim processing completed. "
                            f"Validation result: {validation_status}"
                        )
                }
            )


        return {
            "message":
                "Claim processing completed",

            "document_id":
                document_id,

            "filename":
                file.filename,

            # Kept for the existing frontend
            "status":
                validation_status,

            # New lifecycle values
            "processing_status":
                "COMPLETED",

            "validation_status":
                validation_status,

            "extracted_fields":
                extracted,

            "validation_issues":
                issues
        }


    except Exception as error:

        # ----------------------------------------------------
        # Genuine processing/system failure
        # ----------------------------------------------------

        if document_id is not None:

            try:

                with engine.begin() as connection:

                    # Mark the processing lifecycle as failed
                    connection.execute(
                        text("""
                            UPDATE claim_documents

                            SET
                                status = 'FAILED',
                                processing_status = 'FAILED',
                                validation_status = NULL

                            WHERE document_id = :document_id
                        """),

                        {
                            "document_id":
                                document_id
                        }
                    )


                    # Record the actual failure reason
                    connection.execute(
                        text("""
                            INSERT INTO processing_events
                            (
                                document_id,
                                event_type,
                                message
                            )

                            VALUES
                            (
                                :document_id,
                                'PROCESSING_FAILED',
                                :message
                            )
                        """),

                        {
                            "document_id":
                                document_id,

                            "message":
                                str(error)
                        }
                    )


            except Exception as logging_error:

                print(
                    "Unable to save failure event:",
                    logging_error
                )


        print(
            f"Claim processing failed for document "
            f"{document_id}: {error}"
        )


        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

