USE healthcare_claims;

CREATE TABLE IF NOT EXISTS claim_documents (
    document_id INT AUTO_INCREMENT PRIMARY KEY,
    original_filename VARCHAR(255) NOT NULL,
    stored_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
	
    status ENUM(
        'QUEUED',
        'PROCESSING',
        'VALIDATED',
        'NEEDS_REVIEW',
        'DUPLICATE',
        'FAILED'
    ) NOT NULL DEFAULT 'QUEUED',
    
    processing_status ENUM(
    'QUEUED',
    'PROCESSING',
    'COMPLETED',
    'FAILED'
	) NOT NULL DEFAULT 'QUEUED',

	validation_status ENUM(
    'VALIDATED',
    'NEEDS_REVIEW',
    'DUPLICATE'
	) NULL,

    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS extracted_fields (
    extracted_id INT AUTO_INCREMENT PRIMARY KEY,

    document_id INT NOT NULL UNIQUE,

    claim_id VARCHAR(100),
    patient_id VARCHAR(100),
    provider_id VARCHAR(100),
    payer_id VARCHAR(100),

    claimed_amount DECIMAL(15,2),

    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (document_id)
        REFERENCES claim_documents(document_id)
        ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS validation_issues (
    issue_id INT AUTO_INCREMENT PRIMARY KEY,

    document_id INT NOT NULL,

    field_name VARCHAR(100),
    expected_value TEXT,
    extracted_value TEXT,

    issue_type VARCHAR(100),
    issue_message TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (document_id)
        REFERENCES claim_documents(document_id)
        ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS processing_events (
    event_id INT AUTO_INCREMENT PRIMARY KEY,

    document_id INT NOT NULL,

    event_type VARCHAR(100),
    message TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (document_id)
        REFERENCES claim_documents(document_id)
        ON DELETE CASCADE
);
