from fastapi import FastAPI, UploadFile, File, HTTPException
import shutil
import os
from app.exif_extractor import get_exif_data
from app.image_verifier import verify_image_integrity

app = FastAPI(title="E-NETRA Backend")

# Temporary folder to hold uploaded images for processing
UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/api/v1/verify-image")
async def verify_uploaded_image(file: UploadFile = File(...)):
    # Save uploaded file locally
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 1. Extract EXIF & GPS Metadata
        exif_data = get_exif_data(file_path)
        
        # 2. Run Image Integrity & Tamper Checks
        verification_result = verify_image_integrity(file_path)
        
        return {
            "filename": file.filename,
            "exif": exif_data,
            "verification": verification_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temporary file
        if os.path.exists(file_path):
            os.remove(file_path)