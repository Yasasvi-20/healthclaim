# MediClaim

MediClaim is a healthcare claims intake and validation system designed to process synthetic healthcare claim PDFs, validate claim information against structured healthcare records, detect inconsistencies and duplicate claims, and provide an exception-review workflow.

The project is currently implemented locally using React, FastAPI, and MySQL and is designed for deployment using Google Cloud services.

---

## Features

- Upload individual or multiple healthcare claim PDFs
- Extract claim information from PDF documents
- Validate claims against structured healthcare data
- Detect duplicate claims
- Identify claims requiring manual review
- Track claim processing states
- View uploaded claim documents
- Review validation results and exceptions
- Maintain processing event history
- Dashboard for claim-processing statistics

### Claim Processing Flow

Claims move through the following processing stages:

```text
QUEUED → PROCESSING → COMPLETED
                     ↘ FAILED
```

After successful processing, claims receive a validation result:

```text
VALIDATED
NEEDS_REVIEW
DUPLICATE
```

---

## Technology Stack

### Frontend
- React
- Vite
- JavaScript
- CSS

### Backend
- Python
- FastAPI
- REST APIs

### Database
- MySQL
- Synthea synthetic healthcare data

### Document Processing
- Python PDF processing
- Synthetic healthcare claim PDFs

### Planned Cloud Architecture
- Google Cloud SQL
- Google Cloud Storage
- Google Pub/Sub
- Google Cloud Run
- Docker
- Google Cloud Logging and Monitoring

---

## Project Structure

```text
healthcare-claims-system/
│
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   └── vite.config.js
│
├── database_schema.sql
├── generate_claim_pdf.py
├── inspect_data.py
├── load_mysql.py
├── .gitignore
└── README.md
```

> `.env`, virtual environments, uploaded documents, generated claims, and local Synthea data are excluded from GitHub through `.gitignore`.

---

# Local Setup Instructions

## 1. Prerequisites

Install the following before running the project:

- Python 3
- Node.js and npm
- MySQL 8
- Git

---

## 2. Clone the Repository

```bash
git clone https://github.com/Yasasvi-20/healthclaim.git
cd healthclaim
```

---

## 3. Create the MySQL Database

Start MySQL and create the project database.

```sql
CREATE DATABASE healthcare_claims;
```

Select it:

```sql
USE healthcare_claims;
```

Run the database schema:

```bash
mysql -u root -p healthcare_claims < database_schema.sql
```

Alternatively, open `database_schema.sql` in MySQL Workbench or the MySQL command-line client and execute it.

---

## 4. Configure Backend Environment

Navigate to the backend folder:

```bash
cd backend
```

Create a Python virtual environment:

```bash
python -m venv .venv
```

### Windows

Activate it with:

```bash
.venv\Scripts\activate
```

### macOS/Linux

```bash
source .venv/bin/activate
```

Install the backend dependencies:

```bash
pip install -r requirements.txt
```

---

## 5. Configure Database Connection

Create a `.env` file inside the `backend` directory.

Example:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=YOUR_MYSQL_PASSWORD
DB_NAME=healthcare_claims
```

Do not commit the `.env` file to GitHub.

Update the values according to your local MySQL configuration.

---

## 6. Load Synthetic Healthcare Data

The application uses synthetic healthcare records generated from Synthea.

After placing the required Synthea CSV files in the expected local directory, run:

```bash
python load_mysql.py
```

This loads the structured healthcare records used during claim validation.

---

## 7. Generate Synthetic Claim PDFs

To generate sample healthcare claim PDFs for testing:

```bash
python generate_claim_pdf.py
```

The generated claims can be used to test different validation scenarios such as:

- Valid claims
- Claims requiring review
- Duplicate claims
- Failed or malformed claims

Generated claim files are intentionally excluded from GitHub.

---

## 8. Start the FastAPI Backend

Navigate to the backend directory if necessary:

```bash
cd backend
```

Start the API:

```bash
uvicorn main:app --reload
```

The backend should run at:

```text
http://127.0.0.1:8000
```

FastAPI API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

---

## 9. Start the React Frontend

Open a second terminal.

Navigate to the frontend:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the Vite development server:

```bash
npm run dev
```

The frontend will normally be available at:

```text
http://localhost:5173
```

Open this address in a browser.

---

# Using MediClaim

Once both the backend and frontend are running:

1. Open the MediClaim dashboard.
2. Select one or multiple synthetic healthcare claim PDFs.
3. Upload the selected claims.
4. The backend records the claim and begins processing.
5. Claim processing status is tracked through `QUEUED`, `PROCESSING`, and `COMPLETED` or `FAILED`.
6. Successfully processed claims are classified as `VALIDATED`, `NEEDS_REVIEW`, or `DUPLICATE`.
7. Open the Claims page to review processed claims.
8. Open Exceptions to inspect claims requiring attention.
9. Open Documents to view uploaded claim documents and their processing status.

---

# Database Components

The system uses relational healthcare records for validation and application-specific tables for claim processing.

Important application tables include:

- Claim documents
- Validation issues
- Processing events

The processing-event history records important stages such as:

```text
QUEUED
PROCESSING_STARTED
PROCESSING_COMPLETED
```

This provides an audit trail of claim processing activity.

---

# Cloud Architecture

The local implementation is designed to migrate to Google Cloud.

The planned workflow is:

```text
React Frontend
      ↓
FastAPI API
      ↓
Cloud Storage
      ↓
Pub/Sub
      ↓
Cloud Run Worker
      ↓
Cloud SQL
      ↓
Validation Results
      ↓
MediClaim Dashboard
```

Cloud Storage will store claim documents, Pub/Sub will support asynchronous processing, Cloud Run will process queued claims, and Cloud SQL will store structured healthcare and claim-processing data.

---

# Project Goal

The goal of MediClaim is to demonstrate a scalable healthcare claim-processing workflow combining relational databases, APIs, document processing, asynchronous processing, cloud architecture, and a user-facing claims management dashboard.

The final cloud implementation is intended to demonstrate batch claim intake, asynchronous processing, validation against Cloud SQL, exception handling, document storage, autoscaling, and application monitoring.