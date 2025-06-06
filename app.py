from flask import Flask, render_template, request, jsonify
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import requests
from models import db, Meeting, Summary
from config import Config
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Create upload folder
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'mp3', 'mp4', 'wav', 'm4a'}

def transcribe_audio(filepath):
    """Transcribe audio using Hugging Face API"""
    if not app.config['HF_API_TOKEN']:
        raise Exception("Hugging Face API token not found. Please set HF_API_TOKEN in your .env file.")
        
    API_URL = "https://api-inference.huggingface.co/models/openai/whisper-base"  # Using base model instead of large-v3
    headers = {"Authorization": f"Bearer {app.config['HF_API_TOKEN']}"}
    
    try:
        with open(filepath, "rb") as f:
            response = requests.post(API_URL, headers=headers, data=f)
        
        if response.status_code == 200:
            return response.json().get("text", "")
        elif response.status_code == 401:
            raise Exception("Invalid Hugging Face API token. Please check your token in the .env file.")
        else:
            raise Exception(f"Transcription failed: {response.status_code} - {response.text}")
    except Exception as e:
        raise Exception(f"Transcription error: {str(e)}")

def generate_summary(text):
    """Generate summary using Hugging Face API"""
    if not app.config['HF_API_TOKEN']:
        raise Exception("Hugging Face API token not found. Please set HF_API_TOKEN in your .env file.")
        
    try:
        # First summarize the content
        summary = query_hf_api(
            model=app.config['SUMMARIZATION_MODEL'],
            inputs=text,
            parameters={"max_length": 150, "min_length": 30}
        )
        
        # Then extract action items
        action_prompt = f"Extract action items from this text: {summary}"
        action_items = query_hf_api(
            model=app.config['SUMMARIZATION_MODEL'],
            inputs=action_prompt,
            parameters={"max_length": 100, "min_length": 10}
        )
        
        return {
            "key_points": [summary],
            "action_items": [action_items]
        }
    except Exception as e:
        raise Exception(f"Summary generation failed: {str(e)}")

def query_hf_api(model, inputs, parameters):
    """Query Hugging Face API for text generation"""
    API_URL = f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Authorization": f"Bearer {app.config['HF_API_TOKEN']}"}
    
    try:
        payload = {
            "inputs": inputs,
            "parameters": parameters
        }
        
        response = requests.post(API_URL, headers=headers, json=payload)
        
        if response.status_code == 200:
            return response.json()[0]['summary_text']
        elif response.status_code == 401:
            raise Exception("Invalid Hugging Face API token. Please check your token in the .env file.")
        else:
            raise Exception(f"API request failed: {response.text}")
    except Exception as e:
        raise Exception(f"API query error: {str(e)}")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template('index.html', error="No file uploaded")
        
        file = request.files['file']
        if file.filename == '':
            return render_template('index.html', error="No file selected")
        
        if not allowed_file(file.filename):
            return render_template('index.html', error="Unsupported file type")
        
        try:
            # Save file temporarily
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Create meeting record
            meeting = Meeting(
                filename=filename,
                upload_time=datetime.utcnow(),
                status="processing"
            )
            db.session.add(meeting)
            db.session.commit()
            
            # Transcribe and summarize
            transcript = transcribe_audio(filepath)
            summary = generate_summary(transcript)
            
            # Save results
            summary_record = Summary(
                meeting_id=meeting.id,
                key_points="\n".join(summary.get("key_points", [])),
                action_items="\n".join(summary.get("action_items", [])),
                generated_at=datetime.utcnow()
            )
            db.session.add(summary_record)
            meeting.status = "completed"
            db.session.commit()
            
            # Clean up
            os.remove(filepath)
            
            return render_template('index.html', 
                               key_points=summary.get("key_points", []),
                               action_items=summary.get("action_items", []))
            
        except Exception as e:
            if 'meeting' in locals():
                meeting.status = "failed"
                db.session.commit()
            return render_template('index.html', error=str(e))
    
    return render_template('index.html')

@app.cli.command("init-db")
def init_db():
    """Initialize the database."""
    with app.app_context():
        db.create_all()
    print("Database initialized.")

if __name__ == '__main__':
    app.run(debug=True)