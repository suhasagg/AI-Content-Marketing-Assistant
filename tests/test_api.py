from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)
def test_health(): assert c.get('/health').json()['status']=='ok'
def test_generate():
 r=c.post('/v1/campaigns/generate',json={"topic":"Agentic AI platforms","brand":{"name":"Acme"},"channels":["blog"]})
 assert r.status_code==200 and len(r.json()['artifacts'])==1
