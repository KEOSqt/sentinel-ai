from fastapi import FastAPI

app = FastAPI(
    title="SentinelAI",
    description="AI-powered cybersecurity analysis platform",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "name": "SentinelAI",
        "status": "running",
        "version": "0.1.0",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}