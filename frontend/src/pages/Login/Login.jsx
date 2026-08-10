import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import api from "../../services/api";
import styles from "./Login.module.css";
function Login() {
  const navigate = useNavigate();
  const { login, setUser } = useAuth();
  


  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (event) => {
    const { name, value } = event.target;

    setFormData((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    try {
      const response = await api.post("/auth/login", {
      email: formData.email,
      password: formData.password,
    });
    console.log(response.data);

    login(response.data.access_token, response.data.user);

    const me = await api.get("/auth/me", {
      headers: {
        Authorization: `Bearer ${response.data.access_token}`,
      },
    });

    setUser(me.data);

    navigate("/dashboard");
    } catch (error) {
      alert(
        error.response?.data?.detail ||
        "Login failed."
      );
    }
  };

  return (
    <section className={styles.wrapper}>
      <div className={styles.card}>
        <p className={styles.eyebrow}>Clinician access</p>

        <h1 className={styles.title}>Sign in</h1>

        <p className={styles.subtitle}>
          Enter your credentials to access the clinical workspace.
        </p>

        {error && (
          <p style={{ color: "red", marginBottom: "15px" }}>
            {error}
          </p>
        )}

        <form
          className={styles.form}
          onSubmit={handleSubmit}
          noValidate
        >
          <label className={styles.field}>
            <span className={styles.label}>Email</span>

            <input
              type="email"
              name="email"
              autoComplete="email"
              value={formData.email}
              onChange={handleChange}
              className={styles.input}
              placeholder="you@hospital.org"
              required
            />
          </label>

          <label className={styles.field}>
            <span className={styles.label}>Password</span>

            <input
              type="password"
              name="password"
              autoComplete="current-password"
              value={formData.password}
              onChange={handleChange}
              className={styles.input}
              placeholder="••••••••"
              required
            />
          </label>

          <button
            type="submit"
            className={styles.submit}
            disabled={loading}
          >
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <p className={styles.footnote}>
          Not a member of this workspace?{" "}
          <Link to="/">Return home</Link>.
        </p>
      </div>
    </section>
  );
}

export default Login;