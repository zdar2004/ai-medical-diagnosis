# AI Medical Diagnosis

AI-Powered Medical Diagnosis & Clinical Decision Support System built with **FastAPI, React, MongoDB Atlas, and Machine Learning**. The system is designed to assist healthcare professionals by securely managing patients, medical records, and AI-assisted diagnosis while implementing industry-standard authentication and authorization.

---

# 🚀 Tech Stack

## Backend
- FastAPI
- Python 3.13
- Motor (Async MongoDB Driver)
- Pydantic v2
- JWT Authentication
- Passlib (bcrypt)
- Python-JOSE

## Database
- MongoDB Atlas

## Frontend
- React (Coming in Week 3)

---

# ✨ Features (Week 1)

- Secure User Registration
- Secure User Login
- JWT Access Token Authentication
- Password Hashing using bcrypt
- Role-Based Access Control (Admin, Doctor, Staff)
- Protected API Endpoints
- Current User Profile Endpoint
- Admin-only User Management
- MongoDB Atlas Integration
- Swagger API Documentation
- Async FastAPI Backend
- Global Exception Handling
- Health Check APIs

---

# 📂 Project Structure

```
ai-medical-diagnosis/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── database/
│   │   ├── models/
│   │   ├── services/
│   │   └── main.py
│   │
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│
├── README.md
└── .gitignore
```

---

# 📌 Available API Endpoints

## Authentication

| Method | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/v1/auth/register` | Register a new user |
| POST | `/api/v1/auth/login` | Login and receive JWT token |

## Users

| Method | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/v1/users/me` | Get current authenticated user |
| GET | `/api/v1/users/` | List all users (Admin only) |
| GET | `/api/v1/users/role-check/staff` | Staff/Doctor/Admin access |
| GET | `/api/v1/users/role-check/doctor` | Doctor/Admin access |

## System

| Method | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/health` | API & Database Health Check |
| GET | `/api/ping` | API Ping |

---

# 🔐 Authentication

The application uses **JWT (JSON Web Tokens)** for secure authentication.

- Passwords are securely hashed using **bcrypt**
- Stateless authentication using JWT
- Protected routes require a valid Bearer Token
- Role-Based Authorization for Admin, Doctor, and Staff

---

# 📅 Project Roadmap

## ✅ Week 1 — Backend Foundation & Authentication
- FastAPI Project Setup
- MongoDB Atlas Integration
- User Registration
- User Login
- JWT Authentication
- Password Hashing
- Role-Based Authorization
- Protected APIs
- User Management APIs

## ⏳ Week 2 — Patient & Medical Records Module
- Patient CRUD APIs
- Medical History Management
- Diagnosis Records
- Search & Pagination
- Data Validation

## ⏳ Week 3 — AI Diagnosis & Frontend
- AI Diagnosis Integration
- React Frontend
- Dashboard
- Reports
- Testing
- Deployment

---

# ▶️ Running the Backend

```bash
cd backend

python -m venv venv

venv\Scripts\activate

pip install -r requirements.txt

uvicorn app.main:app --reload
```

---

# 📖 API Documentation

Once the backend is running:

- Swagger UI: `http://127.0.0.1:8000/api/docs`
- ReDoc: `http://127.0.0.1:8000/api/redoc`

---

# 👨‍💻 Author

**Zaina Dar**

BS Computer Science

GitHub: https://github.com/zdar2004

---

# 📄 License

This project is developed for learning, research, and academic purposes.
