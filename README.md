# Video/Audio Summarizer using Hugging Face

This Flask application transcribes video/audio files and generates summaries using Hugging Face's models.

## Features

- Upload and process video/audio files (mp3, mp4, wav, m4a)
- Automatic transcription using Whisper
- Summary generation using BART
- Action items extraction
- Database storage for meeting records and summaries

## Setup

1. Clone the repository:
```bash
git clone https://github.com/prince19998/video_summarize_using_huggingface.git
cd video_summarize_using_huggingface
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your configuration:
```
SECRET_KEY=your-secret-key-here
HF_API_TOKEN=your-huggingface-api-token
DATABASE_URL=sqlite:///meetings.db
```

5. Initialize the database:
```bash
flask init-db
```

6. Run the application:
```bash
python app.py
```

## Usage

1. Open your browser and navigate to `http://localhost:5000`
2. Upload a video or audio file
3. Wait for processing
4. View the transcription, summary, and action items

## Requirements

- Python 3.7+
- Flask
- Hugging Face API token
- Other dependencies listed in requirements.txt

## License

MIT License 