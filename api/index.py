# api/index.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import statistics

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

TELEMETRY_FILE = "q-vercel-latency.json"

def load_telemetry():
    with open(TELEMETRY_FILE, "r") as f:
        return json.load(f)

def calculate_metrics(records, threshold_ms):
    latencies = [r["latency_ms"] for r in records]
    uptimes = [r["uptime_pct"] for r in records]
    
    if not latencies:
        return {
            "avg_latency": 0,
            "p95_latency": 0,
            "avg_uptime": 0,
            "breaches": 0
        }
    
    avg_latency = statistics.mean(latencies)
    
    sorted_latencies = sorted(latencies)
    p95_index = int(0.95 * len(sorted_latencies))
    if p95_index >= len(sorted_latencies):
        p95_index = len(sorted_latencies) - 1
    p95_latency = sorted_latencies[p95_index]
    
    avg_uptime = statistics.mean(uptimes)
    breaches = sum(1 for lat in latencies if lat > threshold_ms)
    
    return {
        "avg_latency": avg_latency,
        "p95_latency": p95_latency,
        "avg_uptime": avg_uptime,
        "breaches": breaches
    }

@app.post("/")
@app.post("/latency")
async def analytics_endpoint(request: Request):
    data = await request.json()
    regions = data.get("regions", [])
    threshold_ms = data.get("threshold_ms", 180)

    telemetry = load_telemetry()
    result = {}

    for region in regions:
        records = [r for r in telemetry if r["region"] == region]
        if records:
            result[region] = calculate_metrics(records, threshold_ms)

    return JSONResponse(content=result)

@app.get("/")
async def read_root():
    return {"message": "Latency Analytics Endpoint"}
