"""
@Desc: query analyse.
@Author: xiongsishi
@Date: 2024-11-26
"""

import json
from metagpt.actions import Action, UserRequirement


class ThoughtSummary(Action):

    name: str = "ThoughtSummary"

    async def run(self, inputs: str):
        inputs = json.loads(inputs)
        query, thought_process, table_schema = inputs['query'], inputs['thought_process'], json.dumps(inputs['table_schema'], indent=4, ensure_ascii=False)
        prompt = self.PROMPT_TEMPLATE.format(query=query, thought_process=thought_process, table_schema=table_schema)  # 这里也需要截断，如果超长

        rsp = await self._aask(prompt)
        # return rsp
        return json.dumps({"prompt": prompt, "response": rsp}, ensure_ascii=False)