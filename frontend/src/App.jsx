import { useEffect, useMemo, useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [activePage, setActivePage] = useState("dashboard");
  const [dashboard, setDashboard] = useState({
    total_claims: 0,
    validated: 0,
    needs_review: 0,
    duplicates: 0,
    failed: 0,
  });

  const [claims, setClaims] = useState([]);
  const [selectedClaim, setSelectedClaim] = useState(null);
  const [files, setFiles] = useState([]);
  const [uploadProgress, setUploadProgress] = useState({ current: 0, total: 0 });
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState("");
  const [claimSearch, setClaimSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");

  async function loadDashboard() {
    try {
      const response = await fetch(`${API_URL}/dashboard`);
      if (!response.ok) throw new Error("Unable to load dashboard.");
      setDashboard(await response.json());
    } catch (error) {
      console.error("Dashboard error:", error);
    }
  }

  async function loadClaims() {
    try {
      const response = await fetch(`${API_URL}/claims`);
      if (!response.ok) throw new Error("Unable to load claims.");
      setClaims(await response.json());
    } catch (error) {
      console.error("Claims error:", error);
    }
  }

  useEffect(() => {
    loadDashboard();
    loadClaims();
  }, []);

  async function refreshAll() {
    await Promise.all([loadDashboard(), loadClaims()]);
  }

  async function uploadClaim() {
    if (files.length === 0) {
      setMessage("Please select one or more claim PDFs first.");
      return;
    }

    try {
      setUploading(true);
      setUploadProgress({ current: 0, total: files.length });

      let successful = 0;
      let failed = 0;

      for (let index = 0; index < files.length; index++) {
        const currentFile = files[index];
        setMessage(`Processing ${index + 1} of ${files.length}: ${currentFile.name}`);
        setUploadProgress({ current: index + 1, total: files.length });

        const formData = new FormData();
        formData.append("file", currentFile);

        try {
          const response = await fetch(`${API_URL}/claims/upload`, {
            method: "POST",
            body: formData,
          });

          const data = await response.json();

          if (!response.ok) {
            throw new Error(data.detail || "Upload failed.");
          }

          successful += 1;
        } catch (error) {
          console.error(`Upload failed for ${currentFile.name}:`, error);
          failed += 1;
        }
      }

      setMessage(
        `Batch completed: ${successful} processed successfully, ${failed} failed.`
      );

      setFiles([]);
      const input = document.getElementById("claim-file");
      if (input) input.value = "";

      await refreshAll();
    } catch (error) {
      setMessage(error.message);
    } finally {
      setUploading(false);
      setUploadProgress({ current: 0, total: 0 });
    }
  }

  async function viewClaim(documentId) {
    try {
      const response = await fetch(`${API_URL}/claims/${documentId}`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Unable to load claim.");
      }

      setSelectedClaim(data);
    } catch (error) {
      alert(error.message);
    }
  }

  const total = Number(dashboard.total_claims || 0);

  const percentage = (value) => {
    if (!total) return 0;
    return Math.round((Number(value || 0) / total) * 100);
  };

  const exceptionClaims = useMemo(
    () =>
      claims.filter(
        (claim) =>
          ["NEEDS_REVIEW", "DUPLICATE"].includes(claim.validation_status) ||
          claim.processing_status === "FAILED"
      ),
    [claims]
  );

  const filteredClaims = useMemo(() => {
    const query = claimSearch.trim().toLowerCase();

    return claims.filter((claim) => {
      const matchesStatus =
        statusFilter === "ALL" ||
        claim.validation_status === statusFilter ||
        (statusFilter === "FAILED" && claim.processing_status === "FAILED");

      const searchable = [
        claim.claim_id,
        claim.patient_id,
        claim.provider_id,
        claim.original_filename,
        claim.validation_status,
        claim.processing_status,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

      return matchesStatus && (!query || searchable.includes(query));
    });
  }, [claims, claimSearch, statusFilter]);

  function statusClass(status) {
    return status?.toLowerCase().replaceAll("_", "-") || "";
  }

  function processingClass(status) {
    return status?.toLowerCase().replaceAll("_", "-") || "";
  }

  function formatDate(value) {
    if (!value) return "-";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString();
  }

  const pageInfo = {
    dashboard: {
      eyebrow: "MEDICLAIM OPERATIONS",
      title: "Claims Command Center",
      subtitle: "Monitor intake, validation quality and claim-processing health.",
    },
    claims: {
      eyebrow: "CLAIM WORKSPACE",
      title: "Claims Register",
      subtitle: "Search, filter and review all processed healthcare claims.",
    },
    exceptions: {
      eyebrow: "EXCEPTION WORKBENCH",
      title: "Claims Requiring Attention",
      subtitle: "Review validation mismatches, duplicate submissions and processing failures.",
    },
    documents: {
      eyebrow: "DOCUMENT VAULT",
      title: "Uploaded Claim Documents",
      subtitle: "Open claim PDFs and track their current processing state.",
    },
  };

  const currentPage = pageInfo[activePage];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">M</div>
          <div className="brand-copy">
            <h2>MediClaim</h2>
            <span>Claims Intelligence</span>
          </div>
        </div>

        <div className="sidebar-label">WORKSPACE</div>

        <nav className="nav-list">
          <NavButton
            icon="⌂"
            label="Overview"
            active={activePage === "dashboard"}
            onClick={() => setActivePage("dashboard")}
          />
          <NavButton
            icon="▤"
            label="Claims"
            active={activePage === "claims"}
            onClick={() => setActivePage("claims")}
          />
          <NavButton
            icon="!"
            label="Exceptions"
            active={activePage === "exceptions"}
            onClick={() => setActivePage("exceptions")}
            badge={exceptionClaims.length}
          />
          <NavButton
            icon="▣"
            label="Documents"
            active={activePage === "documents"}
            onClick={() => setActivePage("documents")}
          />
        </nav>

        <div className="sidebar-spacer" />

        <div className="system-card">
          <div className="system-row">
            <span className="system-dot" />
            <strong>Local environment</strong>
          </div>
          <span>MySQL + FastAPI connected</span>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <p className="eyebrow">{currentPage.eyebrow}</p>
            <h1>{currentPage.title}</h1>
            <p className="subtitle">{currentPage.subtitle}</p>
          </div>

          <div className="topbar-actions">
            <button className="ghost-button" onClick={refreshAll}>
              ↻ Refresh data
            </button>
            <div className="live-pill">
              <span className="online-dot" />
              Live
            </div>
          </div>
        </header>

        {activePage === "dashboard" && (
          <>
            <section className="metric-grid">
              <MetricCard
                label="Total claims"
                value={dashboard.total_claims}
                meta="Processed documents"
                icon="▤"
              />
              <MetricCard
                label="Validated"
                value={dashboard.validated}
                meta={`${percentage(dashboard.validated)}% success rate`}
                icon="✓"
                type="success"
              />
              <MetricCard
                label="Needs review"
                value={dashboard.needs_review}
                meta={`${percentage(dashboard.needs_review)}% flagged`}
                icon="!"
                type="warning"
              />
              <MetricCard
                label="Duplicates"
                value={dashboard.duplicates}
                meta="Previously processed"
                icon="⧉"
                type="purple"
              />
              <MetricCard
                label="Failed"
                value={dashboard.failed}
                meta="Processing failures"
                icon="×"
                type="danger"
              />
            </section>

            <section className="hero-grid">
              <div className="panel upload-panel">
                <div className="panel-title-row">
                  <div>
                    <span className="section-tag">CLAIM INTAKE</span>
                    <h2>Upload claim documents</h2>
                    <p>Select one or multiple healthcare claim PDFs.</p>
                  </div>
                  <div className="mini-stat">
                    <span>Selected</span>
                    <strong>{files.length}</strong>
                  </div>
                </div>

                <label className="drop-zone" htmlFor="claim-file">
                  <div className="upload-glyph">↑</div>
                  <strong>
                    {files.length
                      ? `${files.length} PDF${files.length > 1 ? "s" : ""} ready`
                      : "Drop claim PDFs here or browse"}
                  </strong>
                  <span>PDF only · multiple files supported</span>

                  <input
                    id="claim-file"
                    type="file"
                    accept=".pdf"
                    multiple
                    onChange={(event) =>
                      setFiles(Array.from(event.target.files || []))
                    }
                  />
                </label>

                {files.length > 0 && (
                  <div className="selected-files">
                    <div className="selected-files-header">
                      <strong>Selected files</strong>
                      <button
                        type="button"
                        onClick={() => {
                          setFiles([]);
                          const input = document.getElementById("claim-file");
                          if (input) input.value = "";
                        }}
                      >
                        Clear all
                      </button>
                    </div>

                    <div className="selected-files-list">
                      {files.map((selectedFile, index) => (
                        <div className="selected-file" key={`${selectedFile.name}-${index}`}>
                          <span className="file-index">{index + 1}</span>
                          <span className="file-name">{selectedFile.name}</span>
                          <button
                            type="button"
                            className="remove-file"
                            onClick={() =>
                              setFiles((current) =>
                                current.filter((_, fileIndex) => fileIndex !== index)
                              )
                            }
                          >
                            ×
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <button
                  className="primary-button"
                  disabled={uploading || files.length === 0}
                  onClick={uploadClaim}
                >
                  {uploading
                    ? `Processing ${uploadProgress.current} / ${uploadProgress.total}`
                    : files.length > 1
                    ? `Process ${files.length} claims`
                    : "Process claim"}
                </button>

                {uploading && uploadProgress.total > 0 && (
                  <div className="batch-progress">
                    <div className="batch-progress-info">
                      <span>Batch processing</span>
                      <strong>
                        {Math.round(
                          (uploadProgress.current / uploadProgress.total) * 100
                        )}
                        %
                      </strong>
                    </div>
                    <div className="batch-progress-track">
                      <div
                        className="batch-progress-fill"
                        style={{
                          width: `${
                            (uploadProgress.current / uploadProgress.total) * 100
                          }%`,
                        }}
                      />
                    </div>
                  </div>
                )}

                {message && <div className="notification">{message}</div>}
              </div>

              <div className="panel quality-panel">
                <span className="section-tag">PROCESSING QUALITY</span>
                <h2>Validation health</h2>
                <p className="panel-subtitle">
                  Current distribution across processed documents.
                </p>

                <div className="quality-score">
                  <div>
                    <span>Validation rate</span>
                    <strong>{percentage(dashboard.validated)}%</strong>
                  </div>
                  <div className="score-ring">
                    {percentage(dashboard.validated)}%
                  </div>
                </div>

                <ProgressRow
                  label="Validated"
                  value={percentage(dashboard.validated)}
                  type="green"
                />
                <ProgressRow
                  label="Needs review"
                  value={percentage(dashboard.needs_review)}
                  type="orange"
                />
                <ProgressRow
                  label="Duplicates"
                  value={percentage(dashboard.duplicates)}
                  type="purple"
                />
                <ProgressRow
                  label="Failed"
                  value={percentage(dashboard.failed)}
                  type="red"
                />
              </div>
            </section>

            <ClaimsTable
              title="Recent activity"
              tag="LATEST CLAIMS"
              subtitle="The two most recently processed claim documents."
              claims={claims.slice(0, 2)}
              viewClaim={viewClaim}
              statusClass={statusClass}
              processingClass={processingClass}
              emptyTitle="No claims processed yet"
              emptyMessage="Upload your first claim PDF to begin."
              onRefresh={refreshAll}
            />
          </>
        )}

        {activePage === "claims" && (
          <>
            <section className="toolbar-card">
              <div>
                <span className="section-tag">CLAIM SEARCH</span>
                <h2>Find a processed claim</h2>
              </div>

              <div className="toolbar-controls">
                <input
                  type="search"
                  placeholder="Search claim, patient, provider or file..."
                  value={claimSearch}
                  onChange={(event) => setClaimSearch(event.target.value)}
                />

                <select
                  value={statusFilter}
                  onChange={(event) => setStatusFilter(event.target.value)}
                >
                  <option value="ALL">All statuses</option>
                  <option value="VALIDATED">Validated</option>
                  <option value="NEEDS_REVIEW">Needs review</option>
                  <option value="DUPLICATE">Duplicate</option>
                  <option value="FAILED">Failed</option>
                </select>
              </div>
            </section>

            <ClaimsTable
              title="Claims register"
              tag="ALL CLAIMS"
              subtitle={`${filteredClaims.length} claim${
                filteredClaims.length === 1 ? "" : "s"
              } shown`}
              claims={filteredClaims}
              viewClaim={viewClaim}
              statusClass={statusClass}
              processingClass={processingClass}
              emptyTitle="No claims match your filters"
              emptyMessage="Try another search term or status."
              onRefresh={refreshAll}
            />
          </>
        )}

        {activePage === "exceptions" && (
          <>
            <section className="metric-grid compact">
              <MetricCard
                label="Total exceptions"
                value={exceptionClaims.length}
                meta="Require attention"
                icon="!"
                type="warning"
              />
              <MetricCard
                label="Needs review"
                value={dashboard.needs_review}
                meta="Validation mismatch"
                icon="?"
                type="warning"
              />
              <MetricCard
                label="Duplicates"
                value={dashboard.duplicates}
                meta="Already processed"
                icon="⧉"
                type="purple"
              />
              <MetricCard
                label="Failed"
                value={dashboard.failed}
                meta="Processing error"
                icon="×"
                type="danger"
              />
            </section>

            <ClaimsTable
              title="Exception queue"
              tag="REVIEW WORKBENCH"
              subtitle="Claims that require manual attention."
              claims={exceptionClaims}
              viewClaim={viewClaim}
              statusClass={statusClass}
              processingClass={processingClass}
              emptyTitle="No exceptions found"
              emptyMessage="Problematic claims will appear here."
              onRefresh={refreshAll}
            />
          </>
        )}

        {activePage === "documents" && (
          <section className="panel document-panel">
            <div className="table-heading">
              <div>
                <span className="section-tag">DOCUMENT VAULT</span>
                <h2>Uploaded documents</h2>
                <p>Click a filename to open the original uploaded PDF.</p>
              </div>

              <button className="ghost-button" onClick={refreshAll}>
                ↻ Refresh
              </button>
            </div>

            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>DOCUMENT</th>
                    <th>FILE</th>
                    <th>CLAIM ID</th>
                    <th>UPLOADED</th>
                    <th>PROCESSING</th>
                    <th>VALIDATION</th>
                    <th></th>
                  </tr>
                </thead>

                <tbody>
                  {claims.length === 0 ? (
                    <tr>
                      <td colSpan="7" className="empty-state">
                        <strong>No documents uploaded yet</strong>
                        <span>Uploaded PDFs will appear here.</span>
                      </td>
                    </tr>
                  ) : (
                    claims.map((claim) => (
                      <tr key={claim.document_id}>
                        <td>
                          <strong>#{claim.document_id}</strong>
                        </td>

                        <td>
                          <div className="file-cell">
                            <a
                              href={`${API_URL}/documents/${claim.document_id}/file`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="document-link"
                            >
                              {claim.original_filename || "Unknown"}
                            </a>
                            <span>PDF document</span>
                          </div>
                        </td>

                        <td className="mono">{claim.claim_id || "-"}</td>
                        <td>{formatDate(claim.upload_time)}</td>

                        <td>
                          <span
                            className={`processing-chip ${processingClass(
                              claim.processing_status
                            )}`}
                          >
                            {claim.processing_status || "-"}
                          </span>
                        </td>

                        <td>
                          {claim.validation_status ? (
                            <span
                              className={`status ${statusClass(
                                claim.validation_status
                              )}`}
                            >
                              {claim.validation_status}
                            </span>
                          ) : (
                            <span className="status-empty">—</span>
                          )}
                        </td>

                        <td>
                          <button
                            className="text-button"
                            onClick={() => viewClaim(claim.document_id)}
                          >
                            Review →
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {selectedClaim && (
          <div className="modal-overlay" onClick={() => setSelectedClaim(null)}>
            <div className="claim-modal" onClick={(event) => event.stopPropagation()}>
              <div className="modal-header">
                <div>
                  <span className="section-tag">CLAIM REVIEW</span>
                  <h2>
                    {selectedClaim.claim.claim_id ||
                      (selectedClaim.claim.status === "FAILED"
                        ? "Processing failed"
                        : "Pending claim")}
                  </h2>
                </div>

                <button
                  className="modal-close"
                  onClick={() => setSelectedClaim(null)}
                >
                  ×
                </button>
              </div>

              <div className="claim-detail-grid">
                <DetailItem
                  label="Patient ID"
                  value={selectedClaim.claim.patient_id}
                />
                <DetailItem
                  label="Provider ID"
                  value={selectedClaim.claim.provider_id}
                />
                <DetailItem
                  label="Payer ID"
                  value={selectedClaim.claim.payer_id}
                />
                <DetailItem
                  label="Claim amount"
                  value={
                    selectedClaim.claim.claimed_amount !== null &&
                    selectedClaim.claim.claimed_amount !== undefined
                      ? `$${Number(selectedClaim.claim.claimed_amount).toFixed(2)}`
                      : "-"
                  }
                />
                <DetailItem
                  label="Processing status"
                  value={selectedClaim.claim.processing_status}
                />
                <DetailItem
                  label="Validation status"
                  value={selectedClaim.claim.validation_status || "-"}
                />
                <DetailItem
                  label="Document"
                  value={`#${selectedClaim.claim.document_id}`}
                />
              </div>

              <div className="issues-section">
                <h3>Validation results</h3>

                {selectedClaim.claim.processing_status === "FAILED" ? (
                  <div className="result-card failed-result">
                    <div className="result-icon">×</div>
                    <div>
                      <strong>Claim processing failed</strong>
                      <p>
                        The document could not be processed successfully, so validation
                        could not be completed.
                      </p>
                    </div>
                  </div>
                ) : selectedClaim.validation_issues.length === 0 ? (
                  <div className="result-card success-result">
                    <div className="result-icon">✓</div>
                    <div>
                      <strong>Claim successfully validated</strong>
                      <p>No inconsistencies were detected.</p>
                    </div>
                  </div>
                ) : (
                  selectedClaim.validation_issues.map((issue) => (
                    <div className="result-card warning-result" key={issue.issue_id}>
                      <div className="result-icon">!</div>
                      <div>
                        <strong>{issue.field_name}</strong>
                        <p>{issue.issue_message}</p>
                        <div className="comparison">
                          <span>
                            Expected <b>{issue.expected_value || "-"}</b>
                          </span>
                          <span>
                            Extracted <b>{issue.extracted_value || "-"}</b>
                          </span>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

function NavButton({ icon, label, active, onClick, badge }) {
  return (
    <button className={`nav-item ${active ? "active" : ""}`} onClick={onClick}>
      <span className="nav-icon">{icon}</span>
      <span>{label}</span>
      {badge > 0 && <span className="nav-badge">{badge}</span>}
    </button>
  );
}

function MetricCard({ label, value, meta, icon, type = "" }) {
  return (
    <div className={`metric-card ${type}`}>
      <div className="metric-header">
        <span>{label}</span>
        <div className="metric-icon">{icon}</div>
      </div>
      <strong className="metric-value">{value || 0}</strong>
      <small>{meta}</small>
    </div>
  );
}

function ClaimsTable({
  title,
  tag,
  subtitle,
  claims,
  viewClaim,
  statusClass,
  processingClass,
  emptyTitle,
  emptyMessage,
  onRefresh,
}) {
  return (
    <section className="panel claims-panel">
      <div className="table-heading">
        <div>
          <span className="section-tag">{tag}</span>
          <h2>{title}</h2>
          <p>{subtitle}</p>
        </div>

        <button className="ghost-button" onClick={onRefresh}>
          ↻ Refresh
        </button>
      </div>

      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>CLAIM</th>
              <th>PATIENT</th>
              <th>PROVIDER</th>
              <th>AMOUNT</th>
              <th>PROCESSING</th>
              <th>VALIDATION</th>
              <th></th>
            </tr>
          </thead>

          <tbody>
            {claims.length === 0 ? (
              <tr>
                <td colSpan="7" className="empty-state">
                  <strong>{emptyTitle}</strong>
                  <span>{emptyMessage}</span>
                </td>
              </tr>
            ) : (
              claims.map((claim) => (
                <tr key={claim.document_id}>
                  <td>
                    <div className="claim-cell">
                      <strong>
                        {claim.claim_id ||
                          (claim.processing_status === "FAILED"
                            ? "Processing failed"
                            : "Pending")}
                      </strong>
                      <span>{claim.original_filename}</span>
                    </div>
                  </td>
                  <td className="mono">{claim.patient_id || "-"}</td>
                  <td className="mono">{claim.provider_id || "-"}</td>
                  <td className="amount">
                    {claim.claimed_amount !== null &&
                    claim.claimed_amount !== undefined
                      ? `$${Number(claim.claimed_amount).toFixed(2)}`
                      : "-"}
                  </td>
                  <td>
                    <span
                      className={`processing-chip ${processingClass(
                        claim.processing_status
                      )}`}
                    >
                      {claim.processing_status || "-"}
                    </span>
                  </td>
                  <td>
                    {claim.validation_status ? (
                      <span
                        className={`status ${statusClass(
                          claim.validation_status
                        )}`}
                      >
                        {claim.validation_status}
                      </span>
                    ) : (
                      <span className="status-empty">—</span>
                    )}
                  </td>
                  <td>
                    <button
                      className="text-button"
                      onClick={() => viewClaim(claim.document_id)}
                    >
                      Review →
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function ProgressRow({ label, value, type }) {
  return (
    <div className="progress-row">
      <div className="progress-heading">
        <span>{label}</span>
        <strong>{value}%</strong>
      </div>
      <div className="progress-track">
        <div
          className={`progress-value ${type}`}
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  );
}

function DetailItem({ label, value }) {
  return (
    <div className="detail-item">
      <span>{label}</span>
      <strong>{value || "-"}</strong>
    </div>
  );
}

export default App;
