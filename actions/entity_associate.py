"""
@Desc: Associate entity in user query with category value in table column.
@Author: xiongsishi
@Date: 2025-01-15
"""

import ast
import json

from metagpt.actions import Action
from metagpt.logs import logger
import pandas as pd


def longest_common_subsequence(text1: str, text2: str) -> int:
    m, n = len(text1), len(text2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if text1[i - 1] == text2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    
    return dp[m][n]


class RetrieveJudge(Action):
    """[Currently only supports **single table**] Determine whether column value reading is necessary. """
    name: str = "RetrieveJudge"

    async def run(self, inputs: str):
        inputs = json.loads(inputs)
        query, analysis, table_schema = inputs['query'], inputs['analysis'], inputs['table_desc']

        table_schema = json.dumps(table_schema, ensure_ascii=False, indent=4)

        prompt = self.PROMPT_TEMPLATE.replace("{query}", query).replace("{table_schema}", table_schema).replace("{analysis}", str(analysis))

        rsp = await self._aask(prompt)
        rsp = rsp.strip()
        if rsp.startswith('**Response**:'):
            rsp = rsp.split('**Response**:')[-1].strip()
        
        if rsp.startswith("```json") and rsp.endswith("```"):
            rsp = rsp.replace('```json', '').strip()
            rsp = rsp.replace('```', '')
        final_rsp = {}
        final_rsp['retrieved_contents'] = rsp
        final_rsp['query'] = query 
        final_rsp['analysis'] = analysis
        final_rsp['table_schema'] = table_schema

        return json.dumps(final_rsp, ensure_ascii=False)


class EntityLinking(Action):
    """[Currently only supports **single table**] Retrieve category values for certain columns from a table. """
    name: str = "EntityLinking"

    async def run(self, inputs: str):
        inputs = json.loads(inputs)

        if 'not required' in inputs['retrieved_contents'].lower():
            return json.dumps("", ensure_ascii=False)
        
        try:
            retrieved_contents = ast.literal_eval(inputs['retrieved_contents'])
        except:
            retrieved_contents = json.loads(inputs['retrieved_contents'])
        
        column_values = {}
        table_schema = json.loads(inputs['table_schema'])
        for r in retrieved_contents:
            for entity, col in r.items():
                if entity in table_schema['column_list']:
                    continue
                if col in table_schema['column_list']:
                    logger.info(f'{self.name}: Retrieve all values of `{col}` column')
                    file_path = table_schema['file_path']
                    if file_path.endswith('csv'):
                        df = pd.read_csv(file_path, encoding='utf8')
                    elif file_path.endswith('xlsx'):
                        df = pd.read_excel(file_path)
                    column_ele_list = list(df[col].value_counts().keys())

                    # 最长公共子序列
                    candidates = []
                    text1 = entity.lower().replace(' ', '')
                    for ele in column_ele_list:
                        text2 = ele.lower().replace(' ', '')
                        long_com = longest_common_subsequence(text1, text2)
                        if long_com > 1 and long_com/len(text1) > 0.6:
                            candidates.append((ele, long_com))
                    candidates.sort(key=lambda x:x[1], reverse=True)
                    candidates = candidates[:10]
                    if len(candidates) > 0:
                        column_values[col] = [c[0] for c in candidates]
                    # else:
                    #     column_values[col] = column_ele_list
        if len(column_values) == 0:
            return json.dumps("", ensure_ascii=False)
            
        query, analysis, column_values = inputs['query'], json.dumps(inputs['analysis'], indent=4, ensure_ascii=False), json.dumps(column_values, indent=4, ensure_ascii=False)
        prompt = self.PROMPT_TEMPLATE.replace("{query}", query).replace("{column_values}", column_values).replace("{analysis}", str(analysis))

        rsp = await self._aask(prompt)
        rsp = rsp.strip()
        if rsp.startswith("```json") and rsp.endswith("```"):
            rsp = rsp.replace('```json', '').strip()
            rsp = rsp.replace('```', '')
        
        return json.dumps(rsp, ensure_ascii=False)