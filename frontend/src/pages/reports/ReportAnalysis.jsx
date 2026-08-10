import { useState } from 'react'
import styles from './ReportAnalysis.module.css'

const API_URL = 'http://127.0.0.1:8000/api/v1/reports/analyse'
const TOKEN_STORAGE_KEY = 'token'

// helper to render finding status inline
const renderFindingStatus = (direction, status) => {
  const statusClass =
    direction === 'up'
      ? styles.findingUp
      : direction === 'down'
        ? styles.findingDown
        : styles.findingNormal

  return (
    <span className={`${styles.findingStatus} ${statusClass}`}>
      {status}
      {direction === 'up' && ' ↑'}
      {direction === 'down' && ' ↓'}
    </span>
  )
}

function ReportAnalysis() {
  const [selectedFile, setSelectedFile] = useState(null)
  const [analysis, setAnalysis] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleFileChange = (event) => {
    const file = event.target.files?.[0]

    if (!file) {
      return
    }

    setError('')
    setAnalysis(null)

    const allowedTypes = [
      'application/pdf',
      'text/plain',
    ]

    const allowedExtensions = ['.pdf', '.txt']

    const extension = file.name
      .substring(file.name.lastIndexOf('.'))
      .toLowerCase()

    if (
      !allowedTypes.includes(file.type) &&
      !allowedExtensions.includes(extension)
    ) {
      setError('Only PDF and TXT files are allowed.')
      return
    }

    if (file.size > 10 * 1024 * 1024) {
      setError('File size must not exceed 10 MB.')
      return
    }

    setSelectedFile(file)
  }

  const handleRemoveFile = () => {
    setSelectedFile(null)
    setAnalysis(null)
    setError('')

    const input = document.getElementById('medical-report-file')

    if (input) {
      input.value = ''
    }
  }

  const handleAnalyze = async () => {
    if (!selectedFile) {
      setError('Please choose a medical report first.')
      return
    }

    setLoading(true)
    setError('')
    setAnalysis(null)

    try {
      const token = localStorage.getItem(TOKEN_STORAGE_KEY)

      if (!token) {
        throw new Error(
          'Authentication token not found. Please login again.'
        )
      }

      const formData = new FormData()
      formData.append('file', selectedFile)

      const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          Accept: 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(
          data?.detail || `Analysis failed with status ${response.status}.`
        )
      }

      setAnalysis(data.report_analysis)
    } catch (err) {
      console.error('Medical report analysis failed:', err)

      setError(
        err.message || 'Unable to analyze the medical report.'
      )
    } finally {
      setLoading(false)
    }
  }

  const laboratoryValues = analysis?.laboratory_values || {}
  const interpretedValues = analysis?.interpreted_values || {}
  const abnormalFindings = analysis?.abnormal_findings || []
  const clinicalSummary = analysis?.clinical_summary?.clinical_summary || ''
  const warnings = analysis?.clinical_summary?.warnings || []

  return (
    <div className={styles.page}>
      <h1>Medical Report Analysis</h1>

      <p>
        Analyze Medical Report
      </p>

      <p>
        Upload laboratory reports or clinical documents and review the
        AI-generated medical summary.
      </p>

      {/* Upload Card */}
      <section
        className={styles.card}
        aria-labelledby="upload-heading"
      >
        <h2
          id="upload-heading"
          className={styles.cardTitle}
        >
          Upload Report
        </h2>

        <div className={styles.uploadArea}>
          <svg
            className={styles.uploadIcon}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.75"
            aria-hidden="true"
          >
            <path
              d="M12 16V4"
              strokeLinecap="round"
              strokeLinejoin="round"
            />

            <path
              d="M7 9l5-5 5 5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />

            <path
              d="M4 16v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>

          <p className={styles.uploadTitle}>
            Drag &amp; Drop PDF or TXT Report
          </p>

          <p className={styles.uploadSubtitle}>
            or click to browse
          </p>

          {/* Hidden real file input */}
          <input
            id="medical-report-file"
            type="file"
            accept=".pdf,.txt,application/pdf,text/plain"
            onChange={handleFileChange}
            style={{ display: 'none' }}
          />

          <label
            htmlFor="medical-report-file"
            className={styles.chooseFileButton}
          >
            Choose File
          </label>

          <p className={styles.uploadMeta}>
            Allowed formats: PDF, TXT · Maximum size: 10 MB
          </p>
        </div>
      </section>

      {/* Error */}
      {error && (
        <section
          className={styles.noticeCard}
          aria-live="assertive"
        >
          <p className={styles.noticeText}>
            {error}
          </p>
        </section>
      )}

      {/* Selected File Card */}
      {selectedFile && (
        <section
          className={styles.card}
          aria-labelledby="selected-file-heading"
        >
          <h2
            id="selected-file-heading"
            className={styles.cardTitle}
          >
            Selected File
          </h2>

          <div className={styles.fileRow}>
            <div
              className={styles.fileIcon}
              aria-hidden="true"
            >
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.75"
              >
                <path
                  d="M7 3h7l5 5v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z"
                  strokeLinejoin="round"
                />

                <path
                  d="M14 3v5h5"
                  strokeLinejoin="round"
                />
              </svg>
            </div>

            <div className={styles.fileInfo}>
              <p className={styles.fileName}>
                {selectedFile.name}
              </p>

              <p className={styles.fileMeta}>
                {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                {' · '}
                Ready for analysis
              </p>
            </div>

            <button
              type="button"
              className={styles.removeButton}
              onClick={handleRemoveFile}
            >
              Remove
            </button>
          </div>
        </section>
      )}

      {/* Analyze Button */}
      <section
        className={styles.analyzeSection}
        aria-label="Analyze report action"
      >
        <button
          type="button"
          className={styles.analyzeButton}
          onClick={handleAnalyze}
          disabled={!selectedFile || loading}
        >
          {loading ? 'Analyzing Report...' : 'Analyze Report'}
        </button>
      </section>

      {/* Loading Card */}
      {loading && (
        <section
          className={styles.loadingCard}
          aria-label="Analyzing report"
          aria-live="polite"
        >
          <span
            className={styles.spinner}
            aria-hidden="true"
          />

          <p className={styles.loadingTitle}>
            Analyzing Report...
          </p>

          <p className={styles.loadingSubtitle}>
            Gemini is preparing the clinical summary...
          </p>
        </section>
      )}

      {/* Results */}
      {analysis && !loading && (
        <>
          {/* Analysis Summary */}
          <section
            className={styles.card}
            aria-labelledby="overview-heading"
          >
            <h2
              id="overview-heading"
              className={styles.cardTitle}
            >
              Analysis Summary
            </h2>

            <p className={styles.overviewText}>
              {clinicalSummary}
            </p>
          </section>

          {/* Laboratory Values */}
          <section
            className={styles.card}
            aria-labelledby="laboratory-heading"
          >
            <h2
              id="laboratory-heading"
              className={styles.cardTitle}
            >
              Laboratory Values
            </h2>

            <div>
              {Object.entries(laboratoryValues).map(
                ([parameter, data]) => {
                  const interpretation =
                    interpretedValues[parameter]

                  return (
                    <div
                      className={styles.fileRow}
                      key={parameter}
                    >
                      <div className={styles.fileInfo}>
                        <p className={styles.fileName}>
                          {parameter}
                        </p>

                        <p className={styles.fileMeta}>
                          {data.value} {data.unit || ''}
                          {' · '}
                          {interpretation?.reference_range
                            ? `Reference: ${interpretation.reference_range}`
                            : ''}
                        </p>
                      </div>

                      {renderFindingStatus(
                        interpretation?.status === 'High'
                          ? 'up'
                          : interpretation?.status === 'Low'
                            ? 'down'
                            : 'normal',
                        interpretation?.status || 'Unknown'
                      )}
                    </div>
                  )
                }
              )}
            </div>
          </section>

          {/* Key Findings */}
          <section
            className={styles.card}
            aria-labelledby="findings-heading"
          >
            <h2
              id="findings-heading"
              className={styles.cardTitle}
            >
              Key Findings
            </h2>

            {abnormalFindings.length > 0 ? (
              <ul className={styles.findingsList}>
                {abnormalFindings.map(
                  (finding, index) => (
                    <li
                      className={styles.findingItem}
                      key={`${finding.parameter}-${index}`}
                    >
                      <div className={styles.findingTop}>
                        <p className={styles.findingName}>
                          {finding.parameter}
                        </p>

                        {renderFindingStatus(
                          finding.status === 'High'
                            ? 'up'
                            : 'down',
                          finding.status
                        )}
                      </div>

                      <p className={styles.findingInterpretation}>
                        {finding.message}
                      </p>
                    </li>
                  )
                )}
              </ul>
            ) : (
              <p className={styles.overviewText}>
                No abnormal laboratory findings were detected.
              </p>
            )}
          </section>

          {/* Clinical Warnings */}
          {warnings.length > 0 && (
            <section
              className={styles.noticeCard}
              aria-label="Clinical warning"
            >
              <svg
                className={styles.noticeIcon}
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.75"
                aria-hidden="true"
              >
                <circle cx="12" cy="12" r="9" />
                <path
                  d="M12 8v5"
                  strokeLinecap="round"
                />
                <path d="M12 16h.01" />
              </svg>

              <p className={styles.noticeText}>
                {warnings.join(' ')}
              </p>
            </section>
          )}

          {/* Important Notice */}
          <section
            className={styles.noticeCard}
            aria-label="Important notice"
          >
            <svg
              className={styles.noticeIcon}
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.75"
            >
              <circle cx="12" cy="12" r="9" />

              <path
                d="M12 8v5"
                strokeLinecap="round"
              />

              <path d="M12 16h.01" />
            </svg>

            <p className={styles.noticeText}>
              This analysis is AI-assisted and should always be
              reviewed by a qualified healthcare professional.
            </p>
          </section>
        </>
      )}
    </div>
  )
}

export default ReportAnalysis