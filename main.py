from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from routes import predict


# initializing fastapi app
app = FastAPI(title="Spam & Phishing Detection API", version="1.0")

# enabling cors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: check if needs to be changed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# including routers
app.include_router(predict.router)

# root / health check
@app.get("/")
async def root():
    return {"message": "Spam & Phishing Detection API is running!"}

# running api on localhost
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
