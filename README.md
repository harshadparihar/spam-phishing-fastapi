# Spam & Phishing Detection API

This is a FastAPI backend for spam and phishing detection. The service stores orgs and users in MongoDB, hashes API keys before saving them, and uses bearer auth to separate org-level actions from user-level detection requests.

## What the backend actually does

- An org registers first and receives an org API key.
- That org key is used to create or refresh user API keys under the same org.
- Detection requests are sent directly to this service with a user API key.
- Per-user request counters and positive-hit counters are updated in MongoDB after each detection call.

## Tech Stack

- FastAPI
- Uvicorn
- MongoDB with Motor / PyMongo
- Pydantic v2
- scikit-learn / joblib for spam detection
- pickle for phishing detection

## Requirements

- Python 3.8+
- MongoDB instance
- `venv` or another virtual environment manager

## Environment Variables

Create a `.env` file in the project root:

```env
MONGO_URI=mongodb://localhost:27017
DB_NAME=spam_phishing_fastapi
```

The app reads these values in `config.py`.

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

## Run

Start MongoDB first, then run the API:

```sh
uvicorn main:app --host 0.0.0.0 --port 8000
```

You can also run `python main.py` locally.

## Request Flow

1. Register an org with `POST /org/register`.
2. Use the returned org key with `POST /org/users` to create or refresh a user key.
3. Send detection requests directly to this service with `Authorization: Bearer usr_...`.
4. The service loads the matching user from MongoDB, runs the model, increments that user's counters, and writes the updated document back.

## Authentication Rules

- Protected endpoints read the `Authorization` header directly.
- The header must use the `Bearer ` prefix.
- Keys starting with `org_` are treated as org keys.
- Keys starting with `usr_` are treated as user keys.
- The code hashes the raw key with SHA-256 before looking it up in MongoDB.

## API Endpoints

### Health Check

`GET /`

Response:

```json
{ "message": "Spam & Phishing Detection API is running!" }
```

### Register an Org

`POST /org/register`

Request body:

```json
{
  "email": "org@example.com",
  "userLimit": 25,
  "licenseType": "spamAndPhishingDetection"
}
```

Response includes the org ID and the raw org API key. The stored database value is hashed.

### Create or Refresh a User Key

`POST /org/users`

Headers:

```http
Authorization: Bearer org_...
```

Request body:

```json
{ "username": "alice" }
```

Behavior:

- If the user does not exist under that org, the service creates it.
- If the user already exists, the service replaces the stored user API key.
- The user record is tied to the org through `orgID`.

### Org User Summary

`GET /org/users`

Headers:

```http
Authorization: Bearer org_...
```

Returns only users for the authenticated org. The response hides each user's `apiKey` and `orgID` and adds spam/phishing percentages computed from the stored counters.

### Spam Detection

`POST /predict/spam`

Headers:

```http
Authorization: Bearer usr_...
```

Request body:

```json
{ "text": "Your message here" }
```

The endpoint strips URLs from the text before spam classification, increments `spamReqCount`, and increments `isSpamCount` when the model flags spam.

### Phishing Detection

`POST /predict/phishing`

Headers:

```http
Authorization: Bearer usr_...
```

Request body:

```json
{ "text": "Check this link https://example.com" }
```

The endpoint extracts URLs from the text, runs phishing detection on each URL, increments `phishingReqCount`, and increments `isPhishingCount` for positive results.

### Combined Spam + Phishing Detection

`POST /predict/spam-phishing`

Headers:

```http
Authorization: Bearer usr_...
```

Request body:

```json
{ "text": "Your message here including URLs" }
```

The endpoint runs spam detection on the cleaned message and phishing detection on extracted URLs, then updates both spam and phishing counters for the same user record.

## Example Response Shapes

Spam detection:

```json
{
  "spam": true,
  "spamProbability": 72.5
}
```

Phishing detection:

```json
{
  "urls": [
    {
      "url": "http://example.com",
      "phishing": true,
      "phishingProbability": 85.3
    }
  ]
}
```

Combined detection:

```json
{
  "spam": true,
  "spamProbability": 72.5,
  "urls": [
    {
      "url": "http://example.com",
      "phishing": true,
      "phishingProbability": 85.3
    }
  ]
}
```

## Data Model

MongoDB stores two collections:

- `orgs`
- `users`

The user document includes `orgID`, so users are associated with an org at the application level. The code does not define a MongoDB foreign key.

## Indexes

The app creates these indexes on startup:

- unique `email` on `orgs`
- indexed `apiKey` on `orgs`
- unique compound index on `users` for `username + orgID`
- indexed `apiKey` on `users`
- indexed `orgID` on `users`

## Model Files

Ensure the following model files are present in `bin/` before running the API:

- `bin/spam_detection_svm_model.pkl`
- `bin/tfidf_vectorizer.pkl`
- `bin/model.pkl`

## Notes

- CORS is enabled for all origins in `main.py`.
- The code stores API keys hashed, but returns the raw key only once when it is created or refreshed.
- The detection endpoints are user-key only; org keys are rejected there with HTTP 403.
