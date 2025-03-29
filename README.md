# Spam & Phishing Detection API

This is a FastAPI-based REST API for detecting spam messages and phishing URLs using machine learning models. The API loads a spam detection model (SVM with TF-IDF vectorization) and a phishing detection model, providing predictions based on input text or URLs.

## Features
- Detects spam probability for given text.
- Extracts URLs from text and evaluates them for phishing probability.
- Provides combined spam and phishing detection.
- Uses `joblib` for loading the spam detection model and `pickle` for phishing detection.

## Requirements
- Python 3.8+
- `venv` for virtual environment management
- FastAPI, Uvicorn, and required dependencies

## Setup

### Windows
```sh
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Linux / macOS
```sh
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running the API
```sh
uvicorn main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### Health Check
`GET /`
- **Response:** `{ "message": "Spam & Phishing Detection API is running!" }`

### Spam Detection
`POST /predict/spam`
- **Request Body:** `{ "text": "Your message here" }`
- **Response:** `{ "text": "processed text", "spamProbability": 72.5 }`

### Phishing Detection
`POST /predict/phishing`
- **Request Body:** `{ "url": "http://example.com" }`
- **Response:** `{ "url": "http://example.com", "phishingProbability": 85.3 }`

### Combined Spam & Phishing Detection
`POST /predict/spam-phishing`
- **Request Body:** `{ "text": "Your message here including URLs" }`
- **Response:**
```json
{
  "text": "processed text",
  "urls": [
    { "url": "http://example.com", "phishingProbability": 85.3 }
  ],
  "spamProbability": 72.5
}
```

## Model Files
Ensure the following model files are placed in the `bin/` directory before running the API:
- `bin/spam_detection_svm_model.pkl`
- `bin/tfidf_vectorizer.pkl`
- `bin/model.pkl`

## Logging
Logs are configured at the `INFO` level and provide details about model loading and API requests.

## CORS
CORS is enabled for all origins (`*`). Modify as needed in `app.add_middleware()`.
