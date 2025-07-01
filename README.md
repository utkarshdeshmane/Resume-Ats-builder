# 🚀 Resume Builder API

A powerful **FastAPI-based Resume Builder** leveraging **Google Gemini AI** to parse, upgrade, and generate modern, ATS-friendly resumes in **PDF or Word formats**.

---

## 🌟 Features

- ✅ **Check ATS match** of uploaded resumes
- ✅ **Generate resumes** from job descriptions
- ✅ **Upgrade existing resumes** for targeted roles
- ✅ **Export** as PDF or DOCX
- ✅ **AI-powered parsing and formatting**

---

## 🛠️ Tech Stack

- **FastAPI** – Backend framework
- **Google Gemini AI** – NLP for resume parsing and generation
- **WeasyPrint** – PDF rendering
- **python-docx** – Word document creation
- **Jinja2** – HTML templating engine

---

## ⚙️ Installation

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/resume-builder-api.git
cd resume-builder-api

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt

GOOGLE_API_KEY=your_google_api_key_here

uvicorn main:app --reload
