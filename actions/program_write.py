
"""
Created Date: 2024-11-26
Author: xiongsishi@chinatelecom.cn
"""
import ast
import json
import re

import fire
import subprocess
from metagpt.actions import Action
from metagpt.logs import logger


def parse_code(rsp):
    pattern = r"```python(.*)```"
    match = re.search(pattern, rsp, re.DOTALL)
    code_text = match.group(1) if match else rsp
    return code_text


class SimpleWriteCode(Action):
    """ Generate efficient and robust Python code based on the user's query, analysis, and data file path """
    name: str = "SimpleWriteCode"

    async def run(self, instruction: str):

        instruction = json.loads(instruction)
        prompt = self.PROMPT_TEMPLATE.replace("{refined_table_desc}", str(json.dumps(instruction['table_desc'], ensure_ascii=False, indent=4))).replace("{query}", instruction['query']).replace("{query_analysis}", instruction['query_analysis'])        
        if 'last_turn_error' in instruction:
            prompt = prompt + '\n' + instruction['last_turn_error']
        
        if 'entity_info' in instruction:
            entity_info = instruction['entity_info']
            prompt = prompt + '\n\n' + f'(Pay attention to Additional Information!!!:\nThe correspondence between entities in user queries (`key` field) and table content (`value` field): \n{entity_info}\n\nIf string matching is required, you can refer to the above content to generate more accurate code.)'

        rsp = await self._aask(prompt)
        rsp = rsp.strip()
        if rsp.startswith("```json") and rsp.endswith("```"):
            rsp = rsp.replace('```json', '').strip()
            rsp = rsp.replace('```', '')

        # check of output format
        try:
            format_rsp = json.loads(rsp)
        except Exception as e:
            logger.info(f'{self.name}: error! The generated response does not comply with JSON syntax: \n{e}\nReflection and try again!')
            json_error_fix_request = f"""---- \
In the previous round, the response you output was:

{rsp}

Unfortunately, this response failed to load by `json.loads()`, indicating that your response did not follow the JSON format requirements. The error type is:
{e}
----

Please check for errors in your response and answer again strictly following the above guidelines. Output the correct answer after reflection without additional explanation. 

**User Query**: {instruction['query']}
**Query Decoupling**: {instruction['query_analysis']}
**Response**: """
            prompt = prompt + '\n\n' + json_error_fix_request
            rsp = await self._aask(prompt)
            rsp = rsp.strip()
            if rsp.startswith("```json") and rsp.endswith("```"):
                rsp = rsp.replace('```json', '').strip()
                rsp = rsp.replace('```', '')

        # return json.dumps(rsp, ensure_ascii=False)
        return json.dumps({"prompt": prompt, "rsp": rsp}, ensure_ascii=False)


class SimpleRunCode(Action):
    name: str = "SimpleRunCode"

    async def run(self, inputs: str):
        try:
            code_rsp = json.loads(inputs)['rsp']
            code_gen_prompt = json.loads(inputs)['prompt']
            try:
                code_instructions = json.loads(code_rsp)
            except Exception as e:
                logger.warning(f'code_rsp load warning: {e}. Try to use ast.literal_eval() func.')
                
                try:
                    code_instructions = ast.literal_eval(code_rsp)
                except Exception as e:
                    logger.warning(f'code_rsp load warning: {e}.')
                    code_results = {
                        "prompt": code_gen_prompt,
                        "code_rsp": '',
                        "code": '',
                        "response": '', 
                        # "file": ci.get('file', '')
                        "execute_state": 'fail',
                        "error": f"Code loading failed!\n{e}"
                    }
                    return json.dumps(code_results, ensure_ascii=False)

            code_text = code_instructions['code']

        except Exception as e:
            logger.warning(f'code_rsp load warning: {e}.')
            code_results = {
                "prompt": code_gen_prompt,
                "code_rsp": '',
                "code": '',
                "response": '', 
                "execute_state": 'fail',
                "error": f"Code loading failed!\n{e}"
            }
            return json.dumps(code_results, ensure_ascii=False)

        try:
            result = subprocess.run(["python3", "-c", code_text], capture_output=True, text=True, check=True, timeout=60)
            code_result = result.stdout.strip()
            execute_state = result.returncode
            code_results = {
                "prompt": code_gen_prompt,
                "code_rsp": code_rsp,
                "code": code_text,
                "response": code_result,
                # "file": ci.get('file', '')
                "execute_state": execute_state
            }
        except subprocess.CalledProcessError as error:
            code_results = {
                "prompt": code_gen_prompt,
                "code_rsp": code_rsp,
                "code": code_text,
                "response": '',   
                "execute_state": 'fail',
                "error": error.stderr
            }
        except subprocess.TimeoutExpired as error:
            code_results = {
                "prompt": code_gen_prompt,
                "code_rsp": code_rsp,
                "code": code_text,
                "response": '',  
                "execute_state": 'fail',
                "error": "TimeoutExpired Exception"
            }
        except Exception as error:
            code_results = {
                "prompt": code_gen_prompt,
                "code_rsp": code_rsp,
                "code": code_text,
                "response": '', 
                "execute_state": 'fail',
                "error": error
            }

        return json.dumps(code_results, ensure_ascii=False)
