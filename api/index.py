# api/index.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import statistics

# Create FastAPI app
app = FastAPI()

# ⭐ KEY FIX: Add CORS middleware THIS WAY
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow ANY origin
    allow_credentials=False,  # Must be False when allow_origins is "*"
    allow_methods=["*"],  # Allow all methods (GET, POST, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Load the sample telemetry data
TELEMETRY_FILE = "q-vercel-latency.json"

def load_telemetry():
    with open(TELEMETRY_FILE, "r") as f:
        return json.load(f)

def calculate_metrics(records, threshold_ms):
    latencies = records.get("latencies", [])
    uptimes = records.get("uptimes", [])
    
    if not latencies:
        return {
            "avg_latency": 0,
            "p95_latency": 0,
            "avg_uptime": 0,
            "breaches": 0
        }
    
    avg_latency = statistics.mean(latencies)
    
    # Calculate p95 (95th percentile)
    sorted_latencies = sorted(latencies)
    p95_index = int(0.95 * len(sorted_latencies))
    if p95_index >= len(sorted_latencies):
        p95_index = len(sorted_latencies) - 1
    p95_latency = sorted_latencies[p95_index]
    
    avg_uptime = statistics.mean(uptimes) if uptimes else 0
    
    # Count breaches (latencies above threshold)
    breaches = sum(1 for lat in latencies if lat > threshold_ms)
    
    return {
        "avg_latency": avg_latency,
        "p95_latency": p95_latency,
        "avg_uptime": avg_uptime,
        "breaches": breaches
    }

# POST endpoint - accepts both / and /latency
@app.post("/")
@app.post("/latency")
async def analytics_endpoint(request: Request):
    data = await request.json()
    regions = data.get("regions", [])
    threshold_ms = data.get("threshold_ms", 180)

    telemetry = load_telemetry()
    result = {}

    for region in regions:
        if region in telemetry:
            result[region] = calculate_metrics(telemetry[region], threshold_ms)

    return JSONResponse(content=result)

@app.get("/")
async def read_root():
    return {"message": "Latency Analytics Endpoint"}
