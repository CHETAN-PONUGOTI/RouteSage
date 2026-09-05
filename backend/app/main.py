from fastapi import FastAPI

app = FastAPI(title="Safiri Route Intelligence API")


@app.get("/health")
def health_check():
    return {"status": "ok"}
