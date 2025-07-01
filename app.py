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
    builder_prompt = f"""
    Write a resume for a candidate applying to the following JD:
    {jd}

    Include:
    - Contact Info (dummy)
    - Summary
    - Skills
    - Work Experience
    - Education
    - Certifications
    - Projects

    Format it nicely in markdown/plain text.
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
async def generate_resume(data: ResumeData):
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
