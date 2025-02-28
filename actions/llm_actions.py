"""
@Desc: General llm inference.
@Author: xiongsishi
@Date: 2024-11-27.
"""
import json
from metagpt.actions import Action


class LLMGenerate(Action):

    name: str = "ThoughtGenerator"

    async def run(self, prompt: str):

        rsp = await self._aask(prompt)
        rsp = rsp.strip()
        if rsp.startswith("```json") and rsp.endswith("```"):
            rsp = rsp.replace('```json', '').strip()
            rsp = rsp.replace('```', '')
        return json.dumps(rsp, ensure_ascii=False)