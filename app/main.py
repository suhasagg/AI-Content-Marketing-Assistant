import time, uuid
from fastapi import FastAPI
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
from app.models.schemas import CampaignRequest, CampaignResponse
from app.agents.pipeline import execute
app=FastAPI(title="ContentAlchemy",version="1.0.0")
REQ=Counter("contentalchemy_requests_total","Campaign requests")
LAT=Histogram("contentalchemy_campaign_seconds","Campaign latency")
@app.get("/health")
async def health(): return {"status":"ok"}
@app.get("/metrics")
async def metrics(): return Response(generate_latest(),media_type=CONTENT_TYPE_LATEST)
@app.post("/v1/campaigns/generate",response_model=CampaignResponse)
async def generate(req:CampaignRequest):
    REQ.inc(); start=time.time()
    artifacts,evidence=await execute(req); LAT.observe(time.time()-start)
    return CampaignResponse(campaign_id=str(uuid.uuid4()),artifacts=artifacts,evidence=evidence,quality={"status":"passed","human_approval_recommended":True})
