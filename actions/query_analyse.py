"""
@Desc: column linking.
@Author: xiongsishi
@Date: 2024-11-26
"""

import json
from metagpt.actions import Action
import re
import ast


def contains_unicode_surrogate(text):

    for char in text:
        if '\uD800' <= char <= '\uDBFF':
            return char, True
    return '', False


class QueryExpansion(Action):
    """ Decompose and expand query questions. """
    name: str = "QueryExpansion"

    async def run(self, inputs: str):
        inputs = json.loads(inputs)
        query, table_desc = inputs['query'], inputs['table_desc']

        column_list = table_desc['column_list']
        table_desc = json.dumps(table_desc, ensure_ascii=False, indent=4)
        prompt = self.PROMPT_TEMPLATE.replace("{query}", query).replace("{table_schema}", table_desc)

        original_prompt = prompt

        rsp = await self._aask(prompt)
        rsp = rsp.strip()
        if rsp.startswith("```json") and rsp.endswith("```"):
            rsp = rsp.replace('```json', '').strip()
            rsp = rsp.replace('```', '')
        
        # ---- query retrieval reflection ---
        relevant_column_list = []
        try:
            query_analysis = ast.literal_eval(rsp)

        except:
            print('Exception occur! Column retrieval reflection module loading data error!')

        else:
            for query_ana in query_analysis:
                relevant_column_list.extend(query_ana['relevant_column_list'])
            relevant_column_list = list(set(relevant_column_list))
            
            for i, column_name in enumerate(relevant_column_list):
                if column_name in column_list:
                    continue
                
                # Is there a special character present
                u_char, flag = contains_unicode_surrogate(column_name)
                if flag:
                    column_name_cut = column_name.split(u_char)[0]
                    for c in column_list:
                        if column_name_cut == c[:len(column_name_cut)]:
                            relevant_column_list[i] = c
                            continue

            matched, mis_mathched = [], []
            for c in relevant_column_list:
                if c in column_list:
                    matched.append(c)
                else:
                    mis_mathched.append(c)
            if len(mis_mathched) > 0:
                print('Exception occur! Column search resulted in non-existent column names!')
                prompt += f"\n ---- \n In the previous round, your response was:\n{rsp} \nUnfortunately, the following relevant columns you retrieved DO NOT EXIST in the table schema:\n"+str(mis_mathched) + f"\n----\n\nPlease reflect and answer again (output the answer without additional explanation). \n\nResponse the user question `{query}` strictly follow the above guidelines.\n**Question**: {query}\n**Response**: "
                
                rsp = await self._aask(prompt)
                rsp = rsp.strip()
                if rsp.startswith("```json") and rsp.endswith("```"):
                    rsp = rsp.replace('```json', '').strip()
                    rsp = rsp.replace('```', '')
                
            
            elif len(matched) == 0:
                print('No relevant column names were retrieved!')
                prompt += f"\n ---- \n In the previous round, your response was:\n{rsp} \nUnfortunately, No relevant columns were retrieved.\n----\n\nPlease reflect and answer again (output the answer without additional explanation). \n\nResponse the user question `{query}` strictly follow the above guidelines.\n**Question**: {query}\n**Response**: "
                
                rsp = await self._aask(prompt)
                rsp = rsp.strip()
                if rsp.startswith("```json") and rsp.endswith("```"):
                    rsp = rsp.replace('```json', '').strip()
                    rsp = rsp.replace('```', '')
        # ------

        # return json.dumps(rsp, ensure_ascii=False)
        return json.dumps({"prompt": original_prompt, "rsp": rsp}, ensure_ascii=False)