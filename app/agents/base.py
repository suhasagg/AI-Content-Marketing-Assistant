from app.services.llm import LLMGateway
class Agent:
    def __init__(self, name:str, system:str): self.name,self.system,self.llm=name,system,LLMGateway()
    async def run(self,prompt:str)->str: return await self.llm.generate(self.system,prompt)
