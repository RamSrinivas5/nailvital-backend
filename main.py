from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
import datetime
import os
import uuid
from fpdf import FPDF
import json

from database import engine, get_db
from fastapi.staticfiles import StaticFiles
import models, schemas, auth
import otp_service
from groq import Groq
from io import BytesIO
from fastapi.responses import Response, JSONResponse
from ml_service import ml_predictor
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Initialize Google Gemini Client (Optional)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('models/gemini-flash-latest', 
            system_instruction="You are NailVital AI, a versatile and intelligent assistant. While you have expertise in nail health and dermatology, you are capable of answering any general-purpose questions from the user across any topic. Provide clear, concise, and helpful responses.")
        print("Google Gemini AI initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize Gemini AI: {e}")
        model = None
else:
    print("GEMINI_API_KEY not found. Gemini-specific features will be disabled.")
    model = None

# Initialize Groq Client for high-speed chat
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY)

# Detailed mapping for 22 nail conditions
DISEASE_DETAILS = {
    "aloperia_areata": {
        "name": "Alopecia Areata (Nail Changes)",
        "description": "Nail changes in alopecia areata often appear as small pits, horizontal ridges, or rough texture. This is an autoimmune condition where the immune system attacks hair follicles, sometimes affecting the nail matrix.",
        "recommendation": "Consult a dermatologist to evaluate the underlying autoimmune activity. Corticosteroids or other immune-modulating treatments may be discussed."
    },
    "beaus_lines": {
        "name": "Beau's Lines",
        "description": "Deep grooved lines that run across the nail. They form when growth at the area under the cuticle is interrupted by injury or severe illness (like a high fever or infection).",
        "recommendation": "Identify the cause of the systemic stress. Ensure proper nutrition and hydration as the nail grows out."
    },
    "bluish_nail": {
        "name": "Bluish Nails (Cyanosis)",
        "description": "A bluish tint to the nails indicates that the blood isn't getting enough oxygen. This can be caused by cold temperatures or underlying cardiovascular or respiratory issues.",
        "recommendation": "Monitor your oxygen levels. If persistent, seek medical attention to rule out circulation or lung problems."
    },
    "clubbing": {
        "name": "Nail Clubbing",
        "description": "Nails that curve around the fingertips, which become enlarged. This is often associated with long-term low blood oxygen levels related to heart or lung disease.",
        "recommendation": "Urgent medical consultation is recommended to evaluate heart and lung health."
    },
    "dariers_disease": {
        "name": "Darier's Disease",
        "description": "Nails may show longitudinal red or white streaks, or V-shaped nicks at the edge. It is a rare genetic skin disorder.",
        "recommendation": "Consult a specialist for topical retinoids or other management strategies."
    },
    "eczema": {
        "name": "Nail Eczema",
        "description": "Causes pitting, thickening, and irregular ridges. The surrounding skin is often red, itchy, and inflamed.",
        "recommendation": "Use hypoallergenic moisturizers and avoid harsh chemicals. Topical steroids may be needed for severe flare-ups."
    },
    "half_and_half_nails": {
        "name": "Half-and-Half Nails (Lindsay's Nails)",
        "description": "The bottom half is white while the top half is pink or brown. This can be a sign of chronic kidney disease.",
        "recommendation": "A medical check-up focusing on kidney function is highly advised."
    },
    "koilonychia": {
        "name": "Koilonychia (Spoon Nails)",
        "description": "Soft nails that look scooped out, forming a concave shape. This is a common indicator of iron deficiency anemia.",
        "recommendation": "A blood test for iron levels is recommended. Increase iron-rich foods in your diet."
    },
    "leukonychia": {
        "name": "Leukonychia (White Spots)",
        "description": "White spots or lines on the nail. Usually caused by minor trauma during nail formation or mild vitamin deficiencies.",
        "recommendation": "Usually harmless. Ensure a balanced diet (Zinc/Calcium) and protect nails from physical trauma."
    },
    "melanoma": {
        "name": "Subungual Melanoma",
        "description": "A dark, vertical streak typically on one nail that may expand or change color. This is a serious form of skin cancer.",
        "recommendation": "IMMEDIATE dermatological evaluation is required. Do not delay."
    },
    "muehrckes_lines": {
        "name": "Muehrcke's Lines",
        "description": "Pairs of transverse white lines extending across the nail. Often linked to low levels of albumin in the blood.",
        "recommendation": "Consult a doctor for liver or kidney function tests."
    },
    "onychogryphosis": {
        "name": "Onychogryphosis (Ram's Horn Nails)",
        "description": "Hypertrophy of the nail plate causing it to thicken and curve like a horn. Often caused by trauma or poor circulation.",
        "recommendation": "Professional podiatry care is recommended for safe trimming and management."
    },
    "onycholycis": {
        "name": "Onycholysis",
        "description": "Detachment of the nail from the nail bed. Can be caused by injury, fungal infection, or certain medications.",
        "recommendation": "Keep the nail trimmed short. Avoid moisture trapped under the nail. Consult a doctor if infection is suspected."
    },
    "onychomycosis": {
        "name": "Onychomycosis (Nail Fungus)",
        "description": "A common fungal infection causing thickened, brittle, and discolored nails (yellow/brown).",
        "recommendation": "Keep feet/hands dry. Over-the-counter or prescription antifungal treatments are usually required."
    },
    "pale_nail": {
        "name": "Pale Nails",
        "description": "Nails that appear very white or washed out. Can be a sign of anemia, liver disease, or malnutrition.",
        "recommendation": "Review your nutritional intake. Consult a doctor for blood work if accompanied by fatigue."
    },
    "pitting": {
        "name": "Nail Pitting",
        "description": "Small dents or pits on the nail surface. Frequently seen in people with psoriasis or connective tissue disorders.",
        "recommendation": "Consult a dermatologist to evaluate for psoriasis or underlying inflammatory conditions."
    },
    "psoriasis": {
        "name": "Nail Psoriasis",
        "description": "Causes pitting, crumbly texture, and discoloration (oil spots). It is linked to the chronic skin condition psoriasis.",
        "recommendation": "Specialized nail treatments or systemic therapies may be discussed with a dermatologist."
    },
    "red_lunula": {
        "name": "Red Lunula",
        "description": "The half-moon area at the base of the nail appears red. Can be associated with heart failure or autoimmune diseases.",
        "recommendation": "Detailed medical evaluation of cardiovascular and immune health is recommended."
    },
    "splinter_hemorrhage": {
        "name": "Splinter Hemorrhage",
        "description": "Tiny blood clots that look like splinters under the nail. Usually due to trauma, but can occasionally indicate heart infection (endocarditis).",
        "recommendation": "Often grows out. However, if multiple nails are affected without trauma, see a doctor."
    },
    "terrys_nail": {
        "name": "Terry's Nails",
        "description": "Most of the nail appears white with a narrow pink band at the tip. Frequently associated with liver aging or liver disease.",
        "recommendation": "Consult a doctor for liver health screening."
    },
    "yellow_nails": {
        "name": "Yellow Nail Syndrome",
        "description": "Thick yellow nails that grow slowly. Often associated with respiratory issues or chronic lymphedema.",
        "recommendation": "Evaluate for lung health and lymphatic drainage issues with a medical professional."
    },
    "healthy": {
        "name": "Healthy Nails",
        "description": "The nails appear smooth, consistent in color, and free of spots or severe ridges. This is a normal and healthy scan result.",
        "recommendation": "Continue maintaining good nail hygiene and a balanced diet."
    }
}

# Create Database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="NailVital AI Backend")

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for mobile app flexibility
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

@app.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    otp_code = otp_service.generate_otp()
    
    new_user = models.User(
        name=user.name, 
        email=user.email, 
        phone=user.phone,
        age=user.age,
        gender=user.gender,
        height=user.height,
        hashed_password=hashed_password, 
        otp=otp_code
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Send OTP
    otp_service.send_otp(user.email, otp_code)
    
    return new_user

@app.get("/users/me/export-data")
def export_data(current_user: models.User = Depends(auth.get_current_user)):
    data = {
        "user": {
            "name": current_user.name,
            "email": current_user.email,
            "phone": current_user.phone,
            "age": current_user.age,
            "gender": current_user.gender,
            "height": current_user.height
        },
        "scans": [
            {
                "date": s.created_at.strftime('%Y-%m-%d'),
                "result": s.result_class,
                "confidence": s.confidence
            } for s in current_user.scans
        ]
    }
    return JSONResponse(content=data)

@app.get("/users/me", response_model=schemas.UserResponse)
def get_user_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

@app.put("/users/me", response_model=schemas.UserResponse)
def update_user_me(
    user_update: schemas.UserUpdate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if user_update.name is not None:
        current_user.name = user_update.name
    if user_update.phone is not None:
        current_user.phone = user_update.phone
    if user_update.age is not None:
        current_user.age = user_update.age
    if user_update.gender is not None:
        current_user.gender = user_update.gender
    if user_update.height is not None:
        current_user.height = user_update.height
    if user_update.password is not None:
        current_user.hashed_password = auth.get_password_hash(user_update.password)
    
    db.commit()
    db.refresh(current_user)
    return current_user

@app.delete("/users/me")
def delete_user_me(
    request: schemas.DeleteAccountRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not auth.verify_password(request.password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")

    # Manually delete all associated scans to prevent MySQL foreign key IntegrityError
    db.query(models.Scan).filter(models.Scan.user_id == current_user.id).delete()
    
    db.delete(current_user)
    db.commit()
    return {"message": "Account deleted successfully"}

@app.post("/verify-otp")
def verify_otp(email: str, otp: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.otp == otp:
        user.is_verified = True
        user.otp = None # Clear OTP after success
        db.commit()
        return {"message": "Verification successful"}
    else:
        raise HTTPException(status_code=400, detail="Invalid OTP")

@app.post("/resend-otp")
def resend_otp(email: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_otp = otp_service.generate_otp()
    user.otp = new_otp
    user.is_verified = False
    db.commit()
    
    otp_service.send_otp(email, new_otp)
    return {"message": "OTP resent"}

@app.post("/forgot-password")
def forgot_password(email: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    otp = otp_service.generate_otp()
    user.otp = otp
    db.commit()
    
    otp_service.send_otp(email, otp)
    return {"message": "Reset OTP sent"}

@app.post("/reset-password")
def reset_password(email: str, otp: str, new_password: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.otp == otp:
        user.hashed_password = auth.get_password_hash(new_password)
        user.otp = None
        db.commit()
        return {"message": "Password reset successful"}
    else:
        raise HTTPException(status_code=400, detail="Invalid OTP")

@app.post("/login", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "user": user}

@app.post("/scan", response_model=schemas.ScanResponse)
async def analyze_nail(
    file: UploadFile = File(...), 
    finger: str = "Unknown",
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    contents = await file.read()
    
    # Run ML Prediction
    try:
        prediction = ml_predictor.predict(contents)
        if "error" in prediction:
            raise HTTPException(
                status_code=400, 
                detail=f"NOT_A_NAIL:{prediction.get('reason', 'UNKNOWN')}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

    # Save File with unique UUID to prevent caching issues
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    with open(file_path, "wb") as f:
        f.write(contents)

    # Save Scan to Database
    new_scan = models.Scan(
        user_id=current_user.id,
        image_path=file_path,
        finger=finger,
        result_class=prediction["result_class"],
        confidence=prediction["confidence"]
    )
    db.add(new_scan)
    
    # Handle multiple findings
    findings = prediction.get("findings", [])
    new_scan.findings_json = json.dumps(findings)
    
    db.commit()
    db.refresh(new_scan)

    # Enrich response
    response_findings = []
    for f in findings:
        details = DISEASE_DETAILS.get(f["result_class"], {})
        response_findings.append(schemas.Finding(
            result_class=f["result_class"],
            display_name=details.get("name"),
            description=details.get("description"),
            recommendation=details.get("recommendation"),
            confidence=f["confidence"]
        ))
    
    # Enrich primary result for backward compatibility
    primary_details = DISEASE_DETAILS.get(new_scan.result_class, {})
    new_scan.display_name = primary_details.get("name")
    new_scan.description = primary_details.get("description")
    new_scan.recommendation = primary_details.get("recommendation")
    new_scan.findings = response_findings

    return new_scan

@app.get("/history", response_model=list[schemas.ScanResponse])
def get_scan_history(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    scans = db.query(models.Scan).filter(models.Scan.user_id == current_user.id).order_by(models.Scan.created_at.desc()).all()
    
    # Enrich all scans with professional metadata and multiple findings
    for scan in scans:
        findings = []
        if scan.findings_json:
            try:
                findings_data = json.loads(scan.findings_json)
                for f in findings_data:
                    details = DISEASE_DETAILS.get(f["result_class"], {})
                    findings.append(schemas.Finding(
                        result_class=f["result_class"],
                        display_name=details.get("name"),
                        description=details.get("description"),
                        recommendation=details.get("recommendation"),
                        confidence=f["confidence"]
                    ))
            except:
                pass
        
        # Primary result enrichment
        details = DISEASE_DETAILS.get(scan.result_class, {})
        scan.display_name = details.get("name")
        scan.description = details.get("description")
        scan.recommendation = details.get("recommendation")
        scan.findings = findings
        
    return scans

@app.delete("/scans/{scan_id}")
def delete_scan(scan_id: int, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    scan = db.query(models.Scan).filter(models.Scan.id == scan_id, models.Scan.user_id == current_user.id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Delete the physical file
    if os.path.exists(scan.image_path):
        try:
            os.remove(scan.image_path)
        except:
            pass
            
    db.delete(scan)
    db.commit()
    return {"message": "Scan deleted successfully"}

@app.get("/scans/{scan_id}/export-pdf")
def export_scan_pdf(scan_id: int, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    scan = db.query(models.Scan).filter(models.Scan.id == scan_id, models.Scan.user_id == current_user.id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Header
    pdf.set_font("helvetica", 'B', 20)
    pdf.set_text_color(0, 51, 102) # Dark Blue
    pdf.cell(0, 15, txt="NailVital AI Health Report", ln=True, align='C')
    pdf.set_draw_color(0, 51, 102)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(10)
    
    # Patient Info Header (Enhanced Layout)
    pdf.set_font("helvetica", 'B', 12)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 10, "PATIENT INFORMATION", ln=True)
    pdf.set_draw_color(220, 220, 220)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)

    pdf.set_font("helvetica", 'B', 10)
    pdf.set_text_color(50, 50, 50)
    
    # Column 1
    curr_y = pdf.get_y()
    pdf.cell(30, 7, "Name:", 0)
    pdf.set_font("helvetica", '', 10)
    pdf.cell(60, 7, f"{current_user.name}", 0)
    
    # Column 2
    pdf.set_font("helvetica", 'B', 10)
    pdf.cell(30, 7, "Age:", 0)
    pdf.set_font("helvetica", '', 10)
    pdf.cell(0, 7, f"{current_user.age or 'N/A'}", ln=True)
    
    pdf.set_font("helvetica", 'B', 10)
    pdf.cell(30, 7, "Gender:", 0)
    pdf.set_font("helvetica", '', 10)
    pdf.cell(60, 7, f"{current_user.gender or 'N/A'}", 0)
    
    pdf.set_font("helvetica", 'B', 10)
    pdf.cell(30, 7, "Phone:", 0)
    pdf.set_font("helvetica", '', 10)
    pdf.cell(0, 7, f"{current_user.phone or 'N/A'}", ln=True)

    pdf.set_font("helvetica", 'B', 10)
    pdf.cell(30, 7, "Height:", 0)
    pdf.set_font("helvetica", '', 10)
    pdf.cell(60, 7, f"{current_user.height or 'N/A'}", 0)
    
    pdf.set_font("helvetica", 'B', 10)
    pdf.cell(30, 7, "Scan Date:", 0)
    pdf.set_font("helvetica", '', 10)
    pdf.cell(0, 7, f"{scan.created_at.strftime('%Y-%m-%d')}", ln=True)
    
    pdf.set_font("helvetica", 'B', 10)
    pdf.cell(30, 7, "Nail Location:", 0)
    pdf.set_font("helvetica", '', 10)
    pdf.cell(0, 7, f"{scan.finger or 'Not Specified'}", ln=True)
    pdf.ln(5)
    
    # Result Box
    pdf.set_fill_color(240, 248, 255) # Light Blue
    pdf.rect(10, pdf.get_y(), 190, 30, 'F')
    pdf.set_y(pdf.get_y() + 5)
    
    pdf.set_font("helvetica", 'B', 14)
    display_result = scan.result_class.replace("_", " ").title()
    pdf.cell(0, 10, txt=f"DIAGNOSIS: {display_result}", ln=True, align='C')
    pdf.set_font("helvetica", '', 12)
    pdf.cell(0, 10, txt=f"AI Confidence: {scan.confidence:.2f}%", ln=True, align='C')
    pdf.ln(10)
    
    # Image Section
    abs_image_path = os.path.abspath(scan.image_path)
    if os.path.exists(abs_image_path):
        try:
            # Centering image
            pdf.image(abs_image_path, x=45, y=None, w=120)
        except Exception as e:
            pdf.set_font("helvetica", 'I', 10)
            pdf.set_text_color(200, 0, 0)
            pdf.cell(0, 10, txt=f"[Note: Image could not be embedded: {str(e)}]", ln=True, align='C')
    else:
         pdf.cell(0, 10, txt="[Image file not found on server]", ln=True)

    # Condition Deep Dive
    details = DISEASE_DETAILS.get(scan.result_class, {"name": display_result, "description": "No detailed information available.", "recommendation": "Consult a doctor."})
    
    pdf.set_font("helvetica", 'B', 14)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 10, txt="CONDITION DEEP DIVE", ln=True)
    pdf.set_draw_color(0, 51, 102)
    pdf.line(10, pdf.get_y(), 100, pdf.get_y())
    pdf.ln(3)
    
    pdf.set_font("helvetica", 'B', 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, txt=f"Condition: {details['name']}", ln=True)
    
    pdf.set_font("helvetica", '', 11)
    pdf.multi_cell(0, 6, txt=f"About: {details['description']}")
    pdf.ln(3)
    
    pdf.set_font("helvetica", 'B', 11)
    pdf.set_text_color(0, 102, 51) # Dark Green
    pdf.multi_cell(0, 6, txt=f"Recommendation: {details['recommendation']}")
    
    pdf.ln(10)
    pdf.set_font("helvetica", 'I', 10)
    pdf.set_text_color(128, 128, 128)
    pdf.multi_cell(0, 5, txt="Disclaimer: This report is generated by an advanced AI model. It is intended for informational and tracking purposes only. Please consult a qualified health professional for clinical diagnosis or treatment.", align='C')

    # Return as bytes to prevent blank file/corruption
    try:
        pdf_bytes = bytes(pdf.output())
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": f"PDF generation failed: {str(e)}"})
        
    return Response(content=pdf_bytes, media_type="application/pdf", headers={
        "Content-Disposition": f"attachment; filename=NailVital_Report_{scan_id}.pdf"
    })

@app.get("/history/export-pdf")
def export_history_pdf(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    scans = db.query(models.Scan).filter(models.Scan.user_id == current_user.id).order_by(models.Scan.created_at.desc()).all()
    
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    pdf.set_font("helvetica", 'B', 20)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 15, txt="NailVital - Complete History Report", ln=True, align='C')
    pdf.set_draw_color(0, 51, 102)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(10)
    
    pdf.set_font("helvetica", 'B', 12)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 10, "PATIENT PROFILE", ln=True)
    pdf.set_draw_color(220, 220, 220)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)

    pdf.set_font("helvetica", 'B', 10)
    pdf.set_text_color(50, 50, 50)
    
    # Header Info in columns
    pdf.cell(30, 8, "Name:", 0)
    pdf.set_font("helvetica", '', 10)
    pdf.cell(60, 8, f"{current_user.name}", 0)
    
    pdf.set_font("helvetica", 'B', 10)
    pdf.cell(30, 8, "Age/Gender:", 0)
    pdf.set_font("helvetica", '', 10)
    pdf.cell(0, 8, f"{current_user.age or 'N/A'} / {current_user.gender or 'N/A'}", ln=True)
    
    pdf.set_font("helvetica", 'B', 10)
    pdf.cell(30, 8, "Email:", 0)
    pdf.set_font("helvetica", '', 10)
    pdf.cell(60, 8, f"{current_user.email}", 0)
    
    pdf.set_font("helvetica", 'B', 10)
    pdf.cell(30, 8, "Report Date:", 0)
    pdf.set_font("helvetica", '', 10)
    pdf.cell(0, 8, f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
    
    pdf.ln(5)
    pdf.set_font("helvetica", 'B', 11)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 8, txt=f"SUMMARY: Total {len(scans)} AI Scans Recorded", ln=True)
    pdf.ln(5)
    
    for scan in scans:
        if pdf.get_y() > 220:
            pdf.add_page()
            
        pdf.set_font("helvetica", 'B', 12)
        details = DISEASE_DETAILS.get(scan.result_class, {"name": scan.result_class.replace("_", " ").title(), "description": ""})
        finger_info = f" | Nail Location: {scan.finger}" if scan.finger else ""
        pdf.cell(0, 8, txt=f"{scan.created_at.strftime('%Y-%m-%d')} - {details['name']}{finger_info}", ln=True)
        
        pdf.set_font("helvetica", '', 11)
        pdf.cell(0, 8, txt=f"AI Confidence: {scan.confidence:.2f}%", ln=True)
        
        # Add short condition summary
        if details['description']:
            pdf.set_font("helvetica", 'I', 9)
            pdf.set_text_color(80, 80, 80)
            summary = details['description'].split('.')[0] + '.' # Just the first sentence
            pdf.multi_cell(0, 5, txt=f"Info: {summary}")
            pdf.set_text_color(0, 0, 0)
        abs_image_path = os.path.abspath(scan.image_path)
        
        # Save current Y to reset afterwards
        start_y = pdf.get_y()
        
        if os.path.exists(abs_image_path):
            try:
                # Add image below text
                pdf.image(abs_image_path, x=15, y=pdf.get_y() + 2, w=40)
                pdf.set_y(pdf.get_y() + 45) # Advance Y past the image
            except Exception as e:
                pdf.set_font("helvetica", 'I', 10)
                pdf.set_text_color(200, 0, 0)
                pdf.cell(0, 10, txt=f"[Image error: {str(e)}]", ln=True)
                pdf.set_text_color(0, 0, 0)
        else:
            pdf.set_font("helvetica", 'I', 10)
            pdf.set_text_color(150, 150, 150)
            pdf.cell(0, 10, txt=f"[Image missing: {scan.image_path}]", ln=True)
            pdf.set_text_color(0, 0, 0)
            
        pdf.ln(5)
        pdf.set_draw_color(200, 200, 200)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(8)

    try:
        pdf_bytes = bytes(pdf.output())
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": f"PDF generation failed: {str(e)}"})
        
    return Response(content=pdf_bytes, media_type="application/pdf", headers={
        "Content-Disposition": "attachment; filename=NailVital_History_Report.pdf"
    })

@app.post("/chat", response_model=schemas.ChatResponse)
def get_ai_advice(request: schemas.ChatRequest, current_user: models.User = Depends(auth.get_current_user)):
    try:
        # Inject current date into context to keep the AI up to date
        current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
        
        # System prompt for context awareness
        system_prompt = (
            f"You are NailVital AI, an intelligent assistant. Today is {current_date}. "
            "You have expertise in nail health and dermatology, but can answer any general-purpose questions. "
            "Provide clear, concise, and helpful responses."
        )
        
        # Using Groq (Llama 3.3 70B) for lightning fast chat
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.message}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=1024,
        )
        
        reply = chat_completion.choices[0].message.content
        return schemas.ChatResponse(reply=reply)
    except Exception as e:
        error_msg = str(e)
        if "413" in error_msg or "rate" in error_msg.lower():
             return schemas.ChatResponse(reply="AI Advisor is currently processing many requests. Please take a deep breath and try again in a few seconds.")
        
        # Fallback if API fails
        return schemas.ChatResponse(reply="I'm currently updating my knowledge base. For now, please ensure you keep your nails clean and dry. If you have specific symptoms, check your scan history or consult a dermatologist.")

@app.get("/")
def root():
    return {"message": "Welcome to NailVital AI API"}
