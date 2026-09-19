from app.agents.base import Agent
from app.models.schemas import CampaignRequest, Artifact

researcher=Agent("researcher","You are a rigorous research agent. Separate supplied evidence from assumptions; never fabricate citations.")
strategist=Agent("strategist","You are a principal content strategist. Produce audience, intent, narrative, funnel and channel plans.")
writer=Agent("writer","You write useful, original, non-deceptive marketing content. Do not invent facts, quotes or customer claims.")
seo=Agent("seo","You improve search intent coverage naturally. Avoid keyword stuffing and misleading claims.")
brand=Agent("brand","You enforce brand voice, required terminology, banned phrases, and consistency.")
critic=Agent("critic","You are a demanding editorial evaluator checking factual grounding, specificity, structure, brand fit and channel fit.")

async def execute(req: CampaignRequest):
    evidence="\n".join(f"- {x}" for x in req.research_context) or "No external evidence supplied; avoid unsupported factual claims."
    research=await researcher.run(f"TOPIC: {req.topic}\nGOAL: {req.goal}\nEVIDENCE:\n{evidence}")
    plan=await strategist.run(f"TOPIC: {req.topic}\nAUDIENCE: {req.brand.audience}\nKEYWORDS: {req.keywords}\nRESEARCH:\n{research}")
    artifacts=[]
    for channel in req.channels:
        draft=await writer.run(f"TOPIC: {req.topic}\nCHANNEL: {channel}\nVOICE: {req.brand.voice}\nPLAN:\n{plan}\nEVIDENCE:\n{evidence}")
        optimized=await seo.run(f"TOPIC: {req.topic}\nCHANNEL: {channel}\nKEYWORDS: {req.keywords}\nDRAFT:\n{draft}")
        final=await brand.run(f"TOPIC: {req.topic}\nVOICE: {req.brand.voice}\nBANNED: {req.brand.banned_phrases}\nREQUIRED: {req.brand.required_terms}\nCONTENT:\n{optimized}")
        critique=await critic.run(f"TOPIC: {req.topic}\nCHANNEL: {channel}\nCONTENT:\n{final}")
        artifacts.append(Artifact(channel=channel,title=f"{req.topic} — {channel}",content=final,score=0.85,metadata={"editorial_review":critique}))
    return artifacts, req.research_context
