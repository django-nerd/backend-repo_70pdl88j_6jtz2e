import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from database import db, create_document, get_documents
from schemas import Feedback

app = FastAPI(title="Reviews CRM API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Reviews CRM Backend is running"}

@app.get("/test")
def test_database():
    """Verify database connectivity and list collections"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"

    return response

# ---------------------------
# Review + Feedback Endpoints
# ---------------------------

class FeedbackOut(Feedback):
    id: Optional[str] = None

@app.post("/api/feedback", response_model=dict)
async def create_feedback(payload: Feedback):
    """Store feedback in CRM for ratings below threshold."""
    try:
        inserted_id = create_document("feedback", payload)
        return {"success": True, "id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/feedback", response_model=List[FeedbackOut])
async def list_feedback(limit: int = 100):
    """List recent feedback entries for CRM view."""
    try:
        docs = get_documents("feedback", {}, limit)
        # Normalize ObjectId to string and map to pydantic-friendly dict
        result = []
        for d in docs:
            d["id"] = str(d.pop("_id", ""))
            result.append(FeedbackOut(**d))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --------------
# Run with uvicorn
# --------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
