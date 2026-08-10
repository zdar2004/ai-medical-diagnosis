import styles from './Diagnosis.module.css'
import { useEffect, useState } from "react";
import api from "../../services/api";

function RiskBadge({ level }) {
  const badgeClass =
    level === 'High' ? styles.badgeHigh : level === 'Moderate' ? styles.badgeModerate : styles.badgeLow
  return <span className={`${styles.badge} ${badgeClass}`}>{level}</span>
}

function Diagnosis() {
  const [patients, setPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState("");
  const [symptoms, setSymptoms] = useState("");
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);

  const selectedPatientData = patients.find((patient) => patient.id === selectedPatient) || {};
  const recommendations = prediction?.recommended_tests || [];

  const handlePredict = async () => {
    if (!selectedPatient || !symptoms.trim()) {
      alert("Please select a patient and enter symptoms");
      return;
    }

    setLoading(true);
    try {
       // Step 1: Create diagnosis
      const createResponse = await api.post("/diagnoses/", {
        patient_id: selectedPatient,
        symptoms: symptoms.split(",").map(s => s.trim())
      });

      // Step 2: Run AI
      const analyseResponse = await api.post(
        `/diagnoses/${createResponse.data.id}/analyse`
      );

      // Step 3: Save prediction
      setPrediction(analyseResponse.data);
    } catch (err) {
      console.error(err);
      alert("Error generating prediction");
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setSelectedPatient("");
    setSymptoms("");
    setPrediction(null);
  };

  useEffect(() => {
    async function loadPatients() {
      console.log("Token:", localStorage.getItem("token"));
      try {
        const response = await api.get("/patients/");
        console.log(response.data);
        setPatients(response.data);
      } catch (err) {
        console.error(err);
      }
    }

    loadPatients();
  }, []);
  return (
    <div className={styles.page}>
      <section className={styles.header}>
        <p className={styles.eyebrow}>Clinical Decision Support</p>
        <h1 className={styles.title}>AI Disease Diagnosis</h1>
        <p className={styles.subtitle}>
          Enter patient symptoms to generate AI-assisted disease prediction.
        </p>
      </section>

      {/* Section — Patient Selection */}
      <section className={styles.card} aria-labelledby="patient-selection-heading">
        <h2 id="patient-selection-heading" className={styles.cardTitle}>
          Patient Selection
        </h2>

        <div className={styles.field}>
          <label htmlFor="patientSelect" className={styles.label}>
            Patient
          </label>
          <select
          id="patientSelect"
          className={styles.select}
          value={selectedPatient}
          onChange={(e) => setSelectedPatient(e.target.value)}
        >
          <option value="">Select Patient</option>

          {patients.map((patient) => (
            <option key={patient.id} value={patient.id}>
              {patient.first_name} {patient.last_name}
            </option>
          ))}
        </select>
        </div>

        <div className={styles.patientGrid}>
          <div className={styles.patientItem}>
            <p className={styles.patientLabel}>Age</p>
            <p className={styles.patientValue}>{selectedPatientData.age || '-'}</p>
          </div>
          <div className={styles.patientItem}>
            <p className={styles.patientLabel}>Gender</p>
            <p className={styles.patientValue}>{selectedPatientData.gender || '-'}</p>
          </div>
          <div className={styles.patientItem}>
            <p className={styles.patientLabel}>Blood Group</p>
            <p className={styles.patientValue}>{selectedPatientData.blood_group || '-'}</p>
          </div>
        </div>
      </section>

      {/* Section — Symptoms */}
      <section className={styles.card} aria-labelledby="symptoms-heading">
        <h2 id="symptoms-heading" className={styles.cardTitle}>
          Symptoms Input
        </h2>
        <textarea
          className={styles.symptomsTextarea}
          placeholder="Enter patient symptoms..."
          rows={7}
          value={symptoms}
          onChange={(e) => setSymptoms(e.target.value)}
        />
        <p className={styles.helperNote}>
          Example: Fever, headache, cough, sore throat...
        </p>
      </section>

      {/* Section — AI Prediction Result */}
      <section className={styles.card} aria-labelledby="prediction-heading">
        <div className={styles.predictionHeader}>
          <h2 id="prediction-heading" className={styles.cardTitle}>
            AI Prediction Result
          </h2>
          <RiskBadge level={prediction?.risk_level || 'Unknown'} />
        </div>

        <p className={styles.diseaseName}>
          {prediction?.predicted_disease || "No prediction yet"}
        </p>

        <div className={styles.predictionGrid}>
          <div className={styles.predictionItem}>
            <p className={styles.predictionLabel}>Confidence</p>
            <p className={styles.predictionValue}>
              {prediction
                ? `${(prediction.confidence_score * 100).toFixed(2)}%`
                : "-"}
            </p>
          </div>
          <div className={styles.predictionItem}>
            <p className={styles.predictionLabel}>Risk Level</p>
            <p className={styles.predictionValue}>{prediction?.risk_level || '-'}</p>
          </div>
          <div className={styles.predictionItem}>
            <p className={styles.predictionLabel}>Recommended Specialist</p>
            <p className={styles.predictionValue}>{prediction?.recommended_specialist || '-'}</p>
          </div>
        </div>
        {prediction?.top_predictions?.length > 0 && (
          <div className={styles.topPredictions}>
            <h3 className={styles.topPredictionTitle}>Top 3 Predictions</h3>

            {prediction.top_predictions.map((item, index) => (
              <div key={index} className={styles.topPredictionItem}>
                <span>
                  {index + 1}. {item.disease}
                </span>

                <span>{item.confidence}%</span>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Section — Clinical Recommendations */}
      <section className={styles.card} aria-labelledby="recommendations-heading">
        <h2 id="recommendations-heading" className={styles.cardTitle}>
          Clinical Recommendations
        </h2>
        <ul className={styles.recommendationsList}>
          {recommendations.map((recommendation) => (
            <li className={styles.recommendationItem} key={recommendation}>
              {recommendation}
            </li>
          ))}
        </ul>
      </section>

      {/* Section — Action Buttons */}
      <section className={styles.controls} aria-label="Diagnosis actions">
        <button
          type="button"
          className={styles.clearButton}
          onClick={handleClear}
        >
          Clear Form
        </button>
        <button
            type="button"
            className={styles.primaryButton}
            onClick={handlePredict}
            disabled={loading}
          >
            {loading ? "Predicting..." : "Predict Disease"}
        </button>
      </section>
    </div>
  )
}

export default Diagnosis