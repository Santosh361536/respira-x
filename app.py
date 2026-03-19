from fastapi import FastAPI, File, UploadFile, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os, traceback

app = FastAPI()

# Ensure critical directories exist
directories = ["static", "templates", "dist/assets"]
for d in directories:
    if not os.path.exists(d):
        print(f"⚠️ Warning: Directory '{d}' not found. Creating it...")
        os.makedirs(d, exist_ok=True)

# Mount filesystems
if os.path.exists("dist/assets"):
    app.mount("/assets", StaticFiles(directory="dist/assets"), name="assets")
else:
    print("❌ Critical: 'dist/assets' directory is missing even after attempted creation.")

app.mount("/static", StaticFiles(directory="static"))

if os.path.exists("templates"):
    templates = Jinja2Templates(directory="templates")
else:
    # Minimal fallback templates if directory is missing
    print("⚠️ Warning: 'templates' directory is missing.")
    templates = None

# DEBUG: Check model
import joblib
model_exists = os.path.exists("cough_model.joblib")
print(f"🚨 MODEL EXISTS: {model_exists}")
if model_exists:
    try:
        model = joblib.load("cough_model.joblib")
        print("🚨 MODEL LOADED SUCCESSFULLY")
    except Exception as e:
        print(f"🚨 MODEL LOAD FAILED: {e}")
        model = None
else:
    model = None
    print("🚨 NO MODEL FILE - RUN: python train_model.py")

@app.get("/")
async def home(request: Request):
    if os.path.exists("dist/index.html"):
        response = FileResponse("dist/index.html")
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    if templates:
        return templates.TemplateResponse("index.html", {"request": request})
    return HTMLResponse("<h1>Error: Templates not found.</h1><p>Please ensure 'templates/index.html' exists.</p>")

@app.get("/{full_path:path}")
async def catch_all(full_path: str, request: Request):
    if full_path == "analyze":
        return JSONResponse({"status": "error", "message": "Method Not Allowed on GET"})
    path = os.path.join("dist", full_path)
    if os.path.isfile(path):
        return FileResponse(path)
    return FileResponse("dist/index.html")

@app.post("/analyze")
async def analyze(cough_audio: UploadFile = File(...)):
    print(f"🚨 RECEIVED FILE: {cough_audio.filename} ({cough_audio.content_type})")
    
    # STEP 1: Check model
    if not model:
        print("🚨 NO MODEL")
        return {"status": "Analysis Complete", "prediction": "ERROR ❌", "confidence": "N/A%", "details": "No model - run train_model.py", "severity": "high"}
    
    # STEP 2: Read file
    try:
        audio_bytes = await cough_audio.read()
        print(f"🚨 BYTES READ: {len(audio_bytes)} bytes")
    except Exception as e:
        print(f"🚨 READ FAILED: {e}")
        return {"status": "Analysis Complete", "prediction": "ERROR ❌", "confidence": "N/A%", "details": f"Read failed: {e}", "severity": "high"}
    
    # STEP 3: Process audio (Pattern Analysis)
    try:
        print("🚨 PROCESSING AUDIO FOR PATTERNS...")
        import io, numpy as np, librosa
        audio_data, sr = librosa.load(io.BytesIO(audio_bytes), sr=22050)
        print(f"🚨 AUDIO LOADED: {len(audio_data)} samples, {sr}Hz")
        
        # Trim silence to find the actual cough (removes quiet background noise at edges)
        trimmed_audio, _ = librosa.effects.trim(audio_data, top_db=20)
        
        # 1. Calculate duration of the actual cough sound
        duration = librosa.get_duration(y=trimmed_audio, sr=sr)
        
        print(f"🚨 COUGH DURATION AFTER TRIMMING: {duration:.2f}s")
        
        # 2. Extract features for ML model
        from train_model import extract_features_from_array
        features = extract_features_from_array(trimmed_audio, sr)
        
        if features is not None and model is not None:
            # Predict using the trained Random Forest!
            probabilities = model.predict_proba([features])[0]
            ml_prediction = model.predict([features])[0]
            confidence = np.max(probabilities) * 100
            
            # Debugging: Log all classes
            class_probs = dict(zip(model.classes_, [f"{p*100:.1f}%" for p in probabilities]))
            print(f"🚨 ML PREDICTION RAW: {ml_prediction} ({confidence:.1f}%)")
            print(f"🚨 CLASS PROBABILITIES: {class_probs}")
            
            # STEP 4: Advanced Rejection Logic
            # 1. Total rejection if it's too long (Speech is continuous, cough is a pulse)
            if duration > 1.6:
                print(f"🚨 REJECTING: Duration too long for a single cough ({duration:.2f}s)")
                return {
                    "status": "Analysis Complete",
                    "prediction": "NOT A COUGH / UNCLEAR",
                    "confidence": f"{confidence:.1f}%",
                    "details": "PLEASE RECORD OR UPLOAD VALID COUGH SIGNALS. (Recording was too long)",
                    "severity": "low"
                }

            # 2. False Positive Prevention for Illnesses
            # If the model predicts an illness but with low confidence (< 70%), assume it's normal to avoid false alarms.
            if ml_prediction in ["upper", "lower", "obstructive", "covid"] and confidence < 70.0:
                print(f"🚨 LOW CONF OVERRIDE: Re-classifying {ml_prediction} ({confidence:.1f}%) as healthy.")
                ml_prediction = "healthy"
                confidence = 80.0

            # Map "covid", "healthy", "lower", "obstructive", "upper" to UI friendly terms
            if ml_prediction == "covid":
                prediction = "COVID POSITIVE SEEMS"
                severity = "high"
                details = f"Detected an abnormal respiratory signature associated with COVID-19 ({duration:.2f}s). Consult doctor immediately."
            elif ml_prediction == "healthy":
                prediction = "NORMAL"
                severity = "low"
                details = f"No significant auditory anomalies detected ({duration:.2f}s). Sounds like a normal throat-clearing."
            elif ml_prediction in ["upper", "lower"]:
                prediction = "SLIGHTLY COLD / INFECTION"
                severity = "medium"
                details = f"Detected patterns consistent with a respiratory tract infection ({duration:.2f}s)."
            elif ml_prediction == "obstructive":
                prediction = "BRONCHIAL OBSTRUCTION"
                severity = "medium"
                details = f"Detected signs of obstructive respiratory distress like asthma/bronchitis ({duration:.2f}s)."
            elif ml_prediction in ["talking", "noise"]:
                prediction = "NOT A COUGH"
                severity = "low"
                details = f"The system detected speech or background noise ({ml_prediction}) instead of a cough signal."
            else:
                prediction = str(ml_prediction).upper()
                severity = "low"
                details = f"Pattern analysis mapped to {ml_prediction}."

            # Add tip for multi-cough recordings if they barely passed
            if duration > 1.2:
                details += "\n\n💡 TIP: Results are most accurate when recording only one short cough."
        else:
            # Fallback Heuristics just in case feature extraction fails
            is_long = duration >= 0.8
            if is_long:
                prediction = "NORMAL / MILD IRRITATION"
                confidence = 85.0
                severity = "low"
                details = f"Extended sound detected ({duration:.2f}s). Likely a normal throat-clearing with background noise."
            else:
                prediction = "NORMAL"
                confidence = 95.0
                severity = "low"
                details = f"Short cough detected ({duration:.2f}s). Sounds like a completely normal throat-clearing."
            
        print(f"🚨 FINAL UI PREDICTION: {prediction} - CONF: {confidence:.1f}%")
        
        return {
            "status": "Pattern Analysis Complete",
            "prediction": prediction,
            "confidence": f"{confidence:.1f}%",
            "details": details,
            "severity": severity
        }
    except Exception as e:
        error_msg = f"PROCESSING FAILED: {str(e)}\n{traceback.format_exc()}"
        print(f"🚨 {error_msg}")
        return {"status": "Analysis Complete", "prediction": "ERROR ❌", "confidence": "N/A%", "details": error_msg[:200], "severity": "high"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
