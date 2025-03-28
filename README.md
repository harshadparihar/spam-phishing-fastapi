# Spam & Phishing Detection API

This project is a FastAPI-based application for detecting spam messages and phishing attempts using machine learning models.

## Features

- Detects spam messages
- Identifies phishing attempts
- Uses `scikit-learn` models for classification
- RESTful API built with FastAPI

## Prerequisites

Make sure you have the following installed:

- Python 3.10 or later
- pip
- virtualenv (optional but recommended)

## Installation

### Windows Setup

```powershell
# Clone the repository
git clone https://github.com/yourusername/spam-phishing-detection.git
cd spam-phishing-detection

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Linux/Mac Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/spam-phishing-detection.git
cd spam-phishing-detection

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Running the API

Once installed, you can start the FastAPI server using either of the following methods:

### Using Uvicorn (Recommended)
```bash
uvicorn main:app --reload
```

### Using Python
```bash
python main.py
```

By default, the API runs at `http://127.0.0.1:8000`.

## Model Handling

Make sure the machine learning models (`spam_model.pkl` and `phishing_model.pkl`) are placed in the `models/` directory. If you encounter version mismatches, either retrain the models with your installed `scikit-learn` version or downgrade to match the original version.

## API Endpoints

| Method | Endpoint            | Description                  |
| ------ | ------------------- | ---------------------------- |
| POST   | `/predict/spam`     | Detects spam messages        |
| POST   | `/predict/phishing` | Identifies phishing attempts |

## Troubleshooting

- If virtual environment activation fails on Windows:
  ```powershell
  Set-ExecutionPolicy Unrestricted -Scope Process
  ```
- If you get a `ModuleNotFoundError`, ensure you have activated the virtual environment before running the API.
