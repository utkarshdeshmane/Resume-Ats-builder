# main.py

from fastapi import FastAPI, UploadFile, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings
from typing import List
import os
from uuid import uuid4
from dotenv import load_dotenv
import logging
import json

# Import your utility functions
from resume_utils import (
    extract_text_from_pdf,
    get_gemini_response,
    parse_gemini_resume_to_data,
    render_pdf,
    render_word_document,
    render_resume
)

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Initialize templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

# Settings class
class Settings(BaseSettings):
    MAX_FILE_SIZE: int = 5 * 1024 * 1024
    ALLOWED_EXPORT_FORMATS: List[str] = ["PDF", "WORD"]
    OUTPUTS_DIR: str = "outputs"
    TEMPLATES_DIR: str = "templates"
    GOOGLE_API_KEY: str

    @field_validator("ALLOWED_EXPORT_FORMATS", mode="before")
    def validate_formats(cls, v):
        if isinstance(v, str):
            v = v.replace("'", "").replace('"', "").replace(" ", "")
            if v.startswith("[") and v.endswith("]"):
                v = v[1:-1].split(",")
        return v

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }

# Initialize settings
settings = Settings()
logger.info(f"Loaded settings: {settings.dict()}")

# Pydantic model for structured resume data
class ResumeData(BaseModel):
    name: str
    email: str
    phone: str
    summary: str = None
    skills: list[str] = []
    experience: list[str] = []
    education: list[str] = []
    certifications: list[str] = []
    projects: list[str] = []

# Routes

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/resume/{template_name}", response_class=HTMLResponse)
async def generate_resume(request: Request, template_name: str):
    """
    Render resume templates dynamically based on template_name
    """
    template_map = {
        "template1": "resume_template1.html",
        "template2": "resume_template2.html",
        "template3": "resume_template3.html",
    }

    if template_name not in template_map:
        return HTMLResponse(content="Invalid template name", status_code=400)

    # Example context data for rendering
    context = {
        "request": request,
        "name": "Utkarsh Deshmane",
        "email": "utkarsh@example.com",
        "skills": ["Python", "FastAPI", "SQL"],
        # Extend with dynamic data as needed
    }

    return templates.TemplateResponse(template_map[template_name], context)


@app.post("/check-ats/")
async def check_ats(jd: str = Form(...), file: UploadFile = Form(...)):
    """
    Check how well a resume matches a job description using ATS analysis
    """
    content = await file.read()
    resume_text = extract_text_from_pdf(content)

    ats_prompt = f"""
    You are a top-tier ATS (Applicant Tracking System) engine. Evaluate the resume against the job description.

    Your response must be a valid JSON object with the following structure:
    {{
      "match_percentage": "XX%",
      "missing_keywords": ["keyword1", "keyword2", ...],
      "profile_summary": "Brief evaluation of the candidate's fit for the role",
      "improvement_suggestions": ["suggestion1", "suggestion2", ...]
    }}

    Resume:
    {resume_text}

    Job Description:
    {jd}

    Provide an honest assessment with actionable feedback. Return ONLY the JSON object with no additional text.
    """

    ats_result = await get_gemini_response(ats_prompt)
    cleaned_result = ats_result.strip()

    # Clean up markdown code block indicators if present
    if cleaned_result.startswith("```json"):
        cleaned_result = cleaned_result[7:]
    if cleaned_result.endswith("```"):
        cleaned_result = cleaned_result[:-3]
    cleaned_result = cleaned_result.strip()

    try:
        result_json = json.loads(cleaned_result)
        return JSONResponse(content=result_json)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing failed: {e}")
        return JSONResponse(content={"raw_result": ats_result, "error": str(e)})


@app.post("/build-resume/")
async def build_resume(jd: str = Form(...), export_format: str = Form(...)):
    """
    Build a resume from a job description in specified export format (PDF or Word)
    """
    builder_prompt = f"""
        Write an ATS-friendly resume for a candidate applying to the following JD:
        {jd}

        Include at the top:
        - Name: Dummy Name
        - Location: Dummy City, Dummy Country
        - Phone: +91-9999999999
        - Email: dummy@example.com
        - Years of Experience: X years
        - Resume Link: dummyresume.com

        Mandatory Sections:
        - Professional Summary (highlight 2-3 impactful soft skills such as Time Management, Problem Solving, or Leadership relevant to the JD)
        - Skills (include both technical and soft skills with proper casing, avoiding weak verbs)
        - Work Experience (use strong action verbs, avoid repeated or weak verbs)
        - Educational History
        - Certifications
        - Projects (brief impact statements)
        - Hobbies (list 1-2 only if meaningful to the role)

        Formatting Requirements:
        - Content formatted in clean, structured markdown or plain text
        - Avoid images in the resume
        - Ensure ATS compatibility with proper headings
        - No unwanted personal information such as religion, caste, or marital status
        - Professional email formatting
        - Skill ratings if applicable (e.g. Python - Advanced)
        - File size within optimal limits

        Grammar Requirements:
        - Avoid weak verbs; use strong, specific action verbs
        - Maintain consistent skill casing (e.g. Python, Machine Learning)
        - Avoid excessive pronoun use; keep achievements direct

        Provide the final resume draft ready for ATS parsing.
        """


    resume = await get_gemini_response(builder_prompt)
    data = parse_gemini_resume_to_data(resume)

    output_filename = f"resume_{uuid4().hex}.{'pdf' if export_format == 'PDF' else 'docx'}"
    output_path = os.path.join(settings.OUTPUTS_DIR, output_filename)
    os.makedirs(settings.OUTPUTS_DIR, exist_ok=True)

    render_resume(data, output_path)
    return FileResponse(output_path, filename=output_filename)


@app.post("/upgrade-resume/")
async def upgrade_resume(jd: str = Form(...), file: UploadFile = Form(...), export_format: str = Form(...)):
    """
    Upgrade an existing resume based on a job description and export as PDF or Word
    """
    content = await file.read()
    resume_text = extract_text_from_pdf(content)

    upgrade_prompt = f"""
    Take the resume below and improve it based on the job description. Make it modern, ATS-friendly, and tailored:

    Resume:
    {resume_text}

    Job Description:
    {jd}

    Output a polished, updated resume in markdown/plain text format.
    """

    upgraded = await get_gemini_response(upgrade_prompt)
    data = parse_gemini_resume_to_data(upgraded)

    output_filename = f"resume_{uuid4().hex}.{'pdf' if export_format == 'PDF' else 'docx'}"
    output_path = os.path.join(settings.OUTPUTS_DIR, output_filename)
    os.makedirs(settings.OUTPUTS_DIR, exist_ok=True)

    render_resume(data, output_path)
    return FileResponse(output_path, filename=output_filename)


@app.post("/generate-resume/")
async def generate_resume_api(data: ResumeData):
    """
    Generate resume PDF from structured data input
    """
    try:
        output_filename = f"{uuid4().hex}_resume.pdf"
        output_path = os.path.join(settings.OUTPUTS_DIR, output_filename)
        os.makedirs(settings.OUTPUTS_DIR, exist_ok=True)

        render_resume(data.dict(), output_path)
        return FileResponse(
            path=output_path,
            media_type='application/pdf',
            filename=output_filename
        )

    except Exception as e:
        logger.error(f"Resume generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/new-resume/", response_class=HTMLResponse)
async def new_resume_form(request: Request):
    """
    Serve a form for users to create a new resume from scratch.
    """
    return templates.TemplateResponse("new_resume.html", {"request": request})


@app.get("/list-resumes/", response_class=HTMLResponse)
async def list_resumes(request: Request):
    """
    List all generated resumes for download.
    """
    try:
        files = os.listdir(settings.OUTPUTS_DIR)
        resume_files = [f for f in files if f.endswith(".pdf") or f.endswith(".docx")]
        return templates.TemplateResponse("list_resumes.html", {"request": request, "files": resume_files})
    except Exception as e:
        logger.error(f"Failed to list resumes: {str(e)}")
        return HTMLResponse(content="Error listing resumes.", status_code=500)

