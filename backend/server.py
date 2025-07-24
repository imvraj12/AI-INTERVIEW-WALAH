import os
import uuid
import io
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
import jwt
from dotenv import load_dotenv
import PyPDF2
import asyncio
from emergentintegrations.llm.chat import LlmChat, UserMessage

load_dotenv()

# Database setup
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# FastAPI app
app = FastAPI(title="AI Interview Platform")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database client
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# JWT settings
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"

# Pydantic models
class UserRegistration(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class InterviewRequest(BaseModel):
    job_role: str
    experience_level: str
    interview_type: str  # "text" or "voice"

class InterviewResponse(BaseModel):
    question_id: str
    answer: str

class User(BaseModel):
    id: str
    email: str
    name: str
    created_at: datetime

class Interview(BaseModel):
    id: str
    user_id: str
    job_role: str
    experience_level: str
    interview_type: str
    status: str  # "in_progress", "completed"
    questions: List[dict]
    responses: List[dict]
    feedback: Optional[str]
    created_at: datetime

# Helper functions
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

def extract_text_from_pdf(pdf_file):
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading PDF: {str(e)}")

async def generate_interview_questions(resume_text: str, job_role: str, experience_level: str) -> List[dict]:
    try:
        # Create Gemini chat instance
        chat = LlmChat(
            api_key=GEMINI_API_KEY,
            session_id=f"interview_{uuid.uuid4()}",
            system_message=f"""You are an expert technical interviewer conducting interviews for {job_role} positions at {experience_level} level. 
            Based on the candidate's resume, generate 5-7 relevant interview questions that cover:
            1. Technical skills mentioned in the resume
            2. Projects and experience
            3. Problem-solving abilities
            4. Role-specific knowledge
            
            Return the questions in JSON format as an array of objects with 'id', 'question', 'type' (technical/behavioral), and 'topic' fields."""
        ).with_model("gemini", "gemini-2.0-flash")

        user_message = UserMessage(
            text=f"""Resume Content: {resume_text[:3000]}
            
            Job Role: {job_role}
            Experience Level: {experience_level}
            
            Generate appropriate interview questions based on this resume and role."""
        )

        response = await chat.send_message(user_message)
        
        # Parse the response and create questions
        questions = []
        question_texts = response.split('\n')
        for i, q in enumerate(question_texts[:7]):
            if q.strip() and not q.startswith('#'):
                questions.append({
                    "id": str(uuid.uuid4()),
                    "question": q.strip(),
                    "type": "technical" if i % 2 == 0 else "behavioral",
                    "topic": "general"
                })
        
        # Fallback questions if parsing fails
        if len(questions) < 3:
            questions = [
                {"id": str(uuid.uuid4()), "question": f"Tell me about your experience with {job_role} technologies.", "type": "technical", "topic": "experience"},
                {"id": str(uuid.uuid4()), "question": "Walk me through a challenging project you've worked on.", "type": "behavioral", "topic": "projects"},
                {"id": str(uuid.uuid4()), "question": f"How do you stay updated with the latest trends in {job_role}?", "type": "behavioral", "topic": "learning"},
                {"id": str(uuid.uuid4()), "question": "Describe a time when you had to solve a complex technical problem.", "type": "technical", "topic": "problem-solving"},
                {"id": str(uuid.uuid4()), "question": f"What interests you most about working as a {job_role}?", "type": "behavioral", "topic": "motivation"}
            ]
        
        return questions
    except Exception as e:
        print(f"Error generating questions: {str(e)}")
        # Fallback questions
        return [
            {"id": str(uuid.uuid4()), "question": f"Tell me about your experience in {job_role}.", "type": "technical", "topic": "experience"},
            {"id": str(uuid.uuid4()), "question": "Walk me through your most challenging project.", "type": "behavioral", "topic": "projects"},
            {"id": str(uuid.uuid4()), "question": "How do you approach problem-solving?", "type": "technical", "topic": "problem-solving"}
        ]

async def generate_feedback(questions: List[dict], responses: List[dict], job_role: str) -> str:
    try:
        chat = LlmChat(
            api_key=GEMINI_API_KEY,
            session_id=f"feedback_{uuid.uuid4()}",
            system_message=f"""You are an expert interviewer providing detailed feedback for a {job_role} interview. 
            Analyze the candidate's responses and provide constructive feedback covering:
            1. Strengths demonstrated
            2. Areas for improvement
            3. Technical knowledge assessment
            4. Communication skills
            5. Overall interview performance
            6. Specific recommendations for improvement
            
            Provide a comprehensive but concise feedback report."""
        ).with_model("gemini", "gemini-2.0-flash")

        # Prepare interview content
        interview_content = "Interview Questions and Responses:\n\n"
        for i, (q, r) in enumerate(zip(questions, responses)):
            interview_content += f"Q{i+1}: {q.get('question', '')}\n"
            interview_content += f"A{i+1}: {r.get('answer', '')}\n\n"

        user_message = UserMessage(
            text=f"Job Role: {job_role}\n\n{interview_content}\n\nProvide detailed feedback on this interview performance."
        )

        response = await chat.send_message(user_message)
        return response
    except Exception as e:
        print(f"Error generating feedback: {str(e)}")
        return "Thank you for completing the interview. Your responses have been recorded and our team will review them shortly."

# Routes
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.post("/api/register")
async def register(user: UserRegistration):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    user_id = str(uuid.uuid4())
    hashed_password = hash_password(user.password)
    
    user_doc = {
        "id": user_id,
        "email": user.email,
        "name": user.name,
        "password": hashed_password,
        "created_at": datetime.utcnow()
    }
    
    await db.users.insert_one(user_doc)
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user_id}, expires_delta=timedelta(days=1)
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "email": user.email,
            "name": user.name
        }
    }

@app.post("/api/login")
async def login(user: UserLogin):
    # Find user
    db_user = await db.users.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create access token
    access_token = create_access_token(
        data={"sub": db_user["id"]}, expires_delta=timedelta(days=1)
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": db_user["id"],
            "email": db_user["email"],
            "name": db_user["name"]
        }
    }

@app.post("/api/upload-resume")
async def upload_resume(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user)
):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Extract text from PDF
    content = await file.read()
    pdf_file = io.BytesIO(content)
    resume_text = extract_text_from_pdf(pdf_file)
    
    # Save resume to database
    resume_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "filename": file.filename,
        "text_content": resume_text,
        "uploaded_at": datetime.utcnow()
    }
    
    await db.resumes.insert_one(resume_doc)
    
    return {
        "message": "Resume uploaded successfully",
        "resume_id": resume_doc["id"],
        "text_preview": resume_text[:200] + "..." if len(resume_text) > 200 else resume_text
    }

@app.post("/api/start-interview")
async def start_interview(
    request: InterviewRequest,
    user_id: str = Depends(get_current_user)
):
    # Get user's latest resume
    resume = await db.resumes.find_one(
        {"user_id": user_id}, 
        sort=[("uploaded_at", -1)]
    )
    
    if not resume:
        raise HTTPException(status_code=400, detail="Please upload a resume first")
    
    # Generate interview questions
    questions = await generate_interview_questions(
        resume["text_content"], 
        request.job_role, 
        request.experience_level
    )
    
    # Create interview session
    interview_id = str(uuid.uuid4())
    interview_doc = {
        "id": interview_id,
        "user_id": user_id,
        "job_role": request.job_role,
        "experience_level": request.experience_level,
        "interview_type": request.interview_type,
        "status": "in_progress",
        "questions": questions,
        "responses": [],
        "feedback": None,
        "created_at": datetime.utcnow()
    }
    
    await db.interviews.insert_one(interview_doc)
    
    return {
        "interview_id": interview_id,
        "questions": questions,
        "total_questions": len(questions)
    }

@app.post("/api/submit-response")
async def submit_response(
    response: InterviewResponse,
    user_id: str = Depends(get_current_user)
):
    # Find the interview
    interview = await db.interviews.find_one({
        "user_id": user_id,
        "status": "in_progress"
    }, sort=[("created_at", -1)])
    
    if not interview:
        raise HTTPException(status_code=404, detail="No active interview found")
    
    # Add response to interview
    response_doc = {
        "question_id": response.question_id,
        "answer": response.answer,
        "submitted_at": datetime.utcnow()
    }
    
    await db.interviews.update_one(
        {"id": interview["id"]},
        {"$push": {"responses": response_doc}}
    )
    
    # Check if all questions are answered
    updated_interview = await db.interviews.find_one({"id": interview["id"]})
    if len(updated_interview["responses"]) >= len(updated_interview["questions"]):
        # Generate feedback
        feedback = await generate_feedback(
            updated_interview["questions"],
            updated_interview["responses"],
            updated_interview["job_role"]
        )
        
        # Mark interview as completed
        await db.interviews.update_one(
            {"id": interview["id"]},
            {
                "$set": {
                    "status": "completed",
                    "feedback": feedback,
                    "completed_at": datetime.utcnow()
                }
            }
        )
        
        return {
            "message": "Interview completed!",
            "feedback": feedback,
            "completed": True
        }
    
    return {
        "message": "Response recorded",
        "completed": False,
        "next_question": len(updated_interview["responses"])
    }

@app.get("/api/interview-history")
async def get_interview_history(user_id: str = Depends(get_current_user)):
    interviews = await db.interviews.find(
        {"user_id": user_id}
    ).sort("created_at", -1).to_list(50)
    
    return {"interviews": interviews}

@app.get("/api/interview/{interview_id}")
async def get_interview(interview_id: str, user_id: str = Depends(get_current_user)):
    interview = await db.interviews.find_one({
        "id": interview_id,
        "user_id": user_id
    })
    
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    return interview

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)