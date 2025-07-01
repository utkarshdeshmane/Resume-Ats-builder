🚀 Resume Builder API
A FastAPI-based Resume Builder that uses Google Gemini AI to parse, upgrade, and build modern, ATS-friendly resumes in PDF or Word formats.

✨ Features
✅ Upload resume PDF and check ATS match
✅ Generate new resumes from job descriptions
✅ Upgrade existing resumes for specific jobs
✅ Export to PDF or Word (.docx)
✅ Powered by Google Gemini AI (gemini-1.5-flash)
✅ Structured with Jinja2 templates and python-docx
✅ Clean, modular code with error handling and logging

🛠️ Tech Stack
FastAPI for API endpoints

Google Gemini AI for NLP tasks

WeasyPrint for PDF rendering

python-docx for Word document generation

Jinja2 for HTML templating

dotenv for environment management

⚡ Installation
Clone the repository

bash
Copy
Edit
git clone https://github.com/yourusername/resume-builder-api.git
cd resume-builder-api
Create virtual environment

bash
Copy
Edit
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
Install dependencies

bash
Copy
Edit
pip install -r requirements.txt
Add your environment variables

Create a .env file:

env
Copy
Edit
GOOGLE_API_KEY=your_google_api_key_here
Run the API

bash
Copy
Edit
uvicorn main:app --reload
Visit http://127.0.0.1:8000 to access endpoints.

📝 API Endpoints
1. Home
GET /

Renders index.html template.

2. Check ATS Match
POST /check-ats/

Form Data:

jd: Job description (string)

file: Resume PDF (file)

Returns:
ATS match percentage, missing keywords, profile summary, improvement suggestions (JSON).

3. Build Resume
POST /build-resume/

Form Data:

jd: Job description (string)

export_format: "PDF" or "WORD"

Returns:
Generated resume file (PDF or DOCX).

4. Upgrade Resume
POST /upgrade-resume/

Form Data:

jd: Job description (string)

file: Existing resume PDF (file)

export_format: "PDF" or "WORD"

Returns:
Upgraded resume tailored to the job description.

5. Generate Resume
POST /generate-resume/

Body (JSON):

json
Copy
Edit
{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "1234567890",
  "summary": "Experienced software engineer...",
  "skills": ["Python", "FastAPI"],
  "experience": ["Software Engineer at ABC Corp"],
  "education": ["B.Tech in Computer Science"],
  "certifications": ["AWS Certified Developer"],
  "projects": ["AI Resume Builder API"]
}
Returns:
Generated resume PDF file.

📂 Project Structure
graphql
Copy
Edit
resume-builder-api/
│
├── main.py                # FastAPI routes and initialization
├── resume_utils.py        # Utility functions (PDF/Word rendering, Gemini integration)
├── templates/
│   └── resume_template.html
├── outputs/               # Generated files
├── requirements.txt
└── README.md
✅ Requirements
Python >= 3.9

Google API key with Gemini AI access

