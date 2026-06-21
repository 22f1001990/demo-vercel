# api/index.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import numpy as np
import os

app = FastAPI()

# Enable CORS for POST from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RequestData(BaseModel):
    regions: list[str]
    threshold_ms: int

# Load telemetry data (in real use, this could be from a URL or env var)
BASE_DIR = os.path.dirname(__file__)
DATA_FILE = os.path.join(os.path.dirname(BASE_DIR), "q-vercel-latency.json")

with open(DATA_FILE) as f:
    TELEMETRY_DATA = json.load(f)
    #print(TELEMETRY_DATA)
#@app.get("/trial")
#def trail():
#    return {"message":" Trial run works 1234"}
#def latency_info():
#    return {"message": "Use POST /latency with JSON data"}
@app.options("/latency")
async def latency_options():
    return Response(status_code=200)
@app.post("/latency")
async def analyze_latency(data: RequestData):
    results = {}
    
    for region in data.regions:
        region_data = [r for r in TELEMETRY_DATA if r.get("region") == region]
        latencies = [r["latency_ms"] for r in region_data if "latency_ms" in r]
        uptimes = [r["uptime_pct"] for r in region_data]
        
        print(region_data, latencies,uptimes)        
        if not latencies:
            results[region] = {"error": "No data for region"}
            continue
            
        # Calculate metrics
        avg_latency = np.mean(latencies)
        p95_latency = np.percentile(latencies, 95)
        avg_uptime = np.mean(uptimes)
        breaches = sum(1 for lat in latencies if lat > data.threshold_ms)
        
        results[region] = {
            "avg_latency": round(avg_latency, 2),
            "p95_latency": round(p95_latency, 2),
            "avg_uptime": round(avg_uptime, 2),
            "breaches": breaches
        }
    
    return results

@app.get("/")
def read_root():
    return {"message": "Hello, World! yogesh 1234"}
