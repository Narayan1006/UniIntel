"""
FastAPI Server for Unilog Product Data Enrichment Pipeline
Runs on port 8082. Exposes: health, status, run, upload, products, downloads.
"""
import sys
import json
import threading
from pathlib import Path
from fastapi import FastAPI, BackgroundTasks, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

from run_pipeline import run_pipeline
from config import OUTPUT_CSV, REVIEW_CSV, METRICS_JSON, ROOT

app = FastAPI(
    title="Unilog Product Intelligence API",
    version="1.0.0",
    description="API for Unilog Product Data Enrichment Pipeline",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline_state = {
    "is_running":  False,
    "progress":    "idle",
    "stage":       0,
    "stage_label": "",
    "total_rows":  0,
    "metrics":     None,
    "error":       None,
    "filename":    "",
}

STAGE_LABELS = [
    "Initialising…",
    "Ingesting & cleaning data…",
    "Resolving brand names…",
    "Looking up distributor source URLs…",
    "AI taxonomy classification…",
    "Extracting product attributes…",
    "Generating 5-format descriptions…",
    "Computing trust scores…",
    "Exporting 252-column CSV…",
]


def _bg_run_pipeline(input_path=None):
    global pipeline_state
    pipeline_state["is_running"] = True
    pipeline_state["progress"]   = "running"
    pipeline_state["error"]      = None
    pipeline_state["stage"]      = 0
    pipeline_state["metrics"]    = None

    def on_stage(n):
        pipeline_state["stage"]       = n
        pipeline_state["stage_label"] = STAGE_LABELS[n] if n < len(STAGE_LABELS) else ""

    try:
        _, metrics = run_pipeline(input_csv=input_path, on_stage=on_stage)
        pipeline_state["metrics"]  = metrics
        pipeline_state["progress"] = "completed"
        pipeline_state["stage"]    = 7
        pipeline_state["stage_label"] = "Done"
    except Exception as e:
        pipeline_state["progress"] = "failed"
        pipeline_state["error"]    = str(e)
    finally:
        pipeline_state["is_running"] = False


# ─── Health ──────────────────────────────────────────────────────────────────
@app.get("/api/v1/enrichment/health")
def health():
    return {"status": "UP", "version": "1.0.0"}


# ─── Status ──────────────────────────────────────────────────────────────────
@app.get("/api/v1/enrichment/status")
def get_status():
    metrics = pipeline_state.get("metrics")
    if metrics is None and METRICS_JSON.exists():
        with open(METRICS_JSON, "r", encoding="utf-8") as f:
            metrics = json.load(f)
    return {
        "is_running":  pipeline_state["is_running"],
        "progress":    pipeline_state["progress"],
        "stage":       pipeline_state["stage"],
        "stage_label": pipeline_state["stage_label"],
        "total_rows":  pipeline_state["total_rows"],
        "filename":    pipeline_state["filename"],
        "error":       pipeline_state["error"],
        "metrics":     metrics,
    }


# ─── Trigger (default input CSV) ─────────────────────────────────────────────
@app.post("/api/v1/enrichment/run")
def trigger_pipeline(background_tasks: BackgroundTasks):
    if pipeline_state["is_running"]:
        return {"status": "already_running"}
    background_tasks.add_task(_bg_run_pipeline)
    return {"status": "started", "message": "Pipeline started with default input CSV."}


# ─── Upload CSV + Run ─────────────────────────────────────────────────────────
@app.post("/api/v1/enrichment/upload")
async def upload_and_run(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if pipeline_state["is_running"]:
        raise HTTPException(status_code=409, detail="Pipeline already running. Please wait.")

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted.")

    upload_dir  = ROOT / "pipeline" / "output"
    upload_dir.mkdir(parents=True, exist_ok=True)
    upload_path = upload_dir / "uploaded_input.csv"

    contents = await file.read()
    lines    = contents.decode("utf-8", errors="replace").strip().splitlines()
    if len(lines) < 2:
        raise HTTPException(status_code=400, detail="CSV appears empty or has no data rows.")

    with open(upload_path, "wb") as f:
        f.write(contents)

    row_count = len(lines) - 1
    pipeline_state["total_rows"] = row_count
    pipeline_state["filename"]   = file.filename

    background_tasks.add_task(_bg_run_pipeline, input_path=upload_path)

    return {
        "status":   "started",
        "filename": file.filename,
        "rows":     row_count,
        "message":  f"Uploaded {file.filename} ({row_count} rows). Pipeline started.",
    }


# ─── Products ────────────────────────────────────────────────────────────────
@app.get("/api/v1/enrichment/products")
def get_products(limit: int = 50, offset: int = 0):
    if not OUTPUT_CSV.exists():
        raise HTTPException(status_code=404, detail="No enriched output yet.")
    df    = pd.read_csv(OUTPUT_CSV, dtype=str).fillna("")
    total = len(df)
    sub   = df.iloc[offset: offset + limit].to_dict(orient="records")
    return {"total": total, "offset": offset, "limit": limit, "products": sub}


# ─── Downloads ───────────────────────────────────────────────────────────────
@app.get("/api/v1/enrichment/download/delivery-csv")
def download_delivery_csv():
    if not OUTPUT_CSV.exists():
        raise HTTPException(status_code=404, detail="No output yet.")
    return FileResponse(path=OUTPUT_CSV, filename="Unilog_Enriched_Delivery_Format.csv", media_type="text/csv")


@app.get("/api/v1/enrichment/download/review-queue")
def download_review_queue():
    if not REVIEW_CSV.exists():
        raise HTTPException(status_code=404, detail="No review queue yet.")
    return FileResponse(path=REVIEW_CSV, filename="Unilog_Human_Review_Queue.csv", media_type="text/csv")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8082, reload=False)
