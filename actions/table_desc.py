"""
@Desc: Generate table description.
@Date: 2024-11-26
@Author: xiongsishi@chinatelecom.cn
"""
import ast
import os
import numpy as np
import pandas as pd
import json

from metagpt.actions import Action, UserRequirement
from metagpt.roles.role import Role, RoleReactMode
from metagpt.schema import Message
from metagpt.logs import logger
import asyncio

import asyncio
import re
import subprocess
import random
import fire

from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.roles.role import Role, RoleReactMode
from metagpt.schema import Message


def retrive_column_feature(df, columns_list, category_keep_num=15):
    new_df = []
    for column in columns_list:
        col_type = df[column].dtype
        example = None

        # for boolean data
        if pd.api.types.is_bool_dtype(col_type):
            counter = df[column].value_counts()
            example = {
                "True Num": counter[True].item() if True in counter else 0,
                "False Num": counter[False].item() if False in counter else 0
            }

        # for numerical data
        elif pd.api.types.is_numeric_dtype(col_type):
            example = {
                "minimum_value": df[column].min().item() if isinstance(df[column].min(), np.int64) else df[column].min(),
                "maximum_value": df[column].max().item() if isinstance(df[column].min(), np.int64) else df[column].max(),
                "median_value": df[column].median().item() if isinstance(df[column].min(), np.int64) else df[column].median(),
                "average_value": df[column].mean().item() if isinstance(df[column].min(), np.int64) else df[column].mean(),
            }

        # for date/time data
        elif pd.api.types.is_datetime64_any_dtype(col_type):
            example = {
                "earliest_date": df[column].min().strftime('%Y-%m-%d %H:%M:%S'),
                "latest_date": df[column].max().strftime('%Y-%m-%d %H:%M:%S')
            }

        # for categorical data
        elif pd.api.types.is_object_dtype(col_type):
            value_counts = df[column].value_counts()
            if len(value_counts) <= category_keep_num:
                categories = value_counts.index.tolist()
                example = {
                    "all_categories": categories
                }
            else:
                top_categories = value_counts.nlargest(category_keep_num).index.tolist()
                example = {
                    "category_examples": top_categories,
                    "total_number_of_categories": len(value_counts),     # ?
                    "caption": f"There are many types in this column, displaying the top {category_keep_num} most common types"
                }

        new_df.append({
            "column_name": column,
            "dtype": str(col_type),
            "example": example
        })

    result_df = pd.DataFrame(new_df)
    return result_df


def get_table_schema(df):
    columns_list = df.columns.tolist()
    if len(columns_list) <= 20:
        result_df = retrive_column_feature(df, columns_list, category_keep_num=10) #5 10  # 对测试集，是不是可以调大一点
    elif len(columns_list) <= 50:
        result_df = retrive_column_feature(df, columns_list, category_keep_num=6)  # 3 6
    else:
        result_df = retrive_column_feature(df, columns_list, category_keep_num=4)  # 2 4

    return result_df.to_dict('records')


def get_refined_table_schema(table_schema, relevant_column_list):
    """ Simplify the table based on relevant columns and obtain more detailed information for relevant columns. """
    refined_table_schema = {
        "file_path": table_schema['file_path'],
        "table_name": table_schema.get('table_name', ''),
        "table_description": table_schema.get('table_description', ''),
        "number_of_rows": table_schema.get('number_of_rows', ''),
        "column_list": [],
        "cell_example": [],
        "column_description": [],
    }

    # step 1: Read information about relevant columns from table schema.
    try:
        # table_schema = json.loads(table_schema)
        column_list = table_schema['column_list']
        for column_name in relevant_column_list:  
            if column_name in column_list:  # 如果不在，是不是应该提供全部的列名了
                refined_table_schema['column_list'].append(column_name)
            else:
                print(f'Wrong column name!! {column_name} not in the table.')
        for column_desc in table_schema['column_description']:
            if column_desc['column_name'] in relevant_column_list:
                refined_table_schema['column_description'].append(column_desc)
        
        # step 2: Update detailed information about the relevant columns -- column_description
        file_name = table_schema['file_path']
        if file_name.endswith('csv'):
            df = pd.read_csv(file_name, encoding='utf8')
        elif file_name.endswith('xlsx'):
            df = pd.read_excel(file_name)
        
        new_column_description = refined_table_schema['column_description']
        for i, each_column_desc in enumerate(refined_table_schema['column_description']):
            if each_column_desc['dtype'] != 'object':
                continue
            column = each_column_desc['column_name']
            value_counts = df[column].value_counts()
            category_max_count = 50  # 100
            if len(str(value_counts.index.tolist()[0]).split(' ')) > 50 \
                or len(str(value_counts.index.tolist()[random.sample(range(len(value_counts)), k=1)[0]]).split(' ')) > 25:   # 50
                category_max_count = 20
            elif len(str(value_counts.index.tolist()[0]).split(' ')) > 20 \
                or len(str(value_counts.index.tolist()[random.sample(range(len(value_counts)), k=1)[0]]).split(' ')) > 10:   # 20
                category_max_count = 50

            if len(value_counts) <= category_max_count:
                categories = value_counts.index.tolist()
                new_column_description[i]['all_categories'] = categories
                new_column_description[i]['total_number_of_categories'] = len(categories)
                if 'category_examples' in new_column_description[i]:
                    del new_column_description[i]['category_examples']
                if 'example' in new_column_description[i]:
                    del new_column_description[i]['example']

            else:
                top_categories = value_counts.nlargest(category_max_count).index.tolist()
                new_column_description[i]['category_examples'] = top_categories
                new_column_description[i]['total_number_of_categories'] = len(value_counts)
                new_column_description[i]['caption'] = f"There are many types in this column, displaying the top {category_max_count} most common types"
                if 'all_categories' in new_column_description[i]:
                    del new_column_description[i]['all_categories']
                if 'example' in new_column_description[i]:
                    del new_column_description[i]['example']

            refined_table_schema['column_description'] = new_column_description
            # refined_table_schema['cell_example'] need update
            # refined_table_schema['cell_example'] = df[:10][refined_table_schema['column_list']].to_dict('records') if len(df)>20 else df[:][refined_table_schema['column_list']].to_dict('records'),
            refined_table_schema['cell_example'] = df.sample(10)[refined_table_schema['column_list']].to_dict('records') if len(df)>20 else df[:][refined_table_schema['column_list']].to_dict('records'),

    except Exception as e:
        print(f'Table Schema Refine Error!!\n {e}')
        # Read the table and retrieve it again
        file_name = table_schema['file_path']
        if file_name.endswith('csv'):
            df = pd.read_csv(file_name, encoding='utf8')
        elif file_name.endswith('xlsx'):
            df = pd.read_excel(file_name)
        columns_list = [c for c in df.columns.tolist() if c in relevant_column_list]
        # Update column_list, cell_example
        refined_table_schema['column_list'] = columns_list
        # refined_table_schema['cell_example'] = df[:10][refined_table_schema['column_list']].to_dict('records') if len(df)>20 else df[:][refined_table_schema['column_list']].to_dict('records'),
        refined_table_schema['cell_example'] = df.sample(10)[refined_table_schema['column_list']].to_dict('records') if len(df)>20 else df[:][refined_table_schema['column_list']].to_dict('records'),

        result_df = retrive_column_feature(df, columns_list, category_keep_num=100)
        for idx, c in result_df.iterrows():
            refined_table_schema['column_description'].append({
                'column_name': c['column_name'],
                'dtype': c['dtype']
            })
            for k, v in c['example'].items():
                refined_table_schema['column_description'][idx][k] = v
        
    return refined_table_schema


def save_dicts_to_json(data, desc_save_path):

    json_str = json.dumps(data, ensure_ascii=False, indent=4)

    with open(desc_save_path, 'w') as f:
        f.write(json_str)
    print(f"Saved {desc_save_path}")



class TableDesc(Action):
    """ Generate table descriptions. 
    Identify the purpose of the table and pinpoint the precise and detailed column information and cell values necessary for the query.
    
    Returns example:
        [add TODO]
    
    """
    name: str = "TableDesc"

    async def run(self, table_item):
        table_item = ast.literal_eval(table_item)
        # table_item = json.loads(table_item)
        table_path, desc_save_path = table_item['table_file'], table_item['desc_save_path']
        df = None
        if table_path.endswith('csv'):
            df = pd.read_csv(table_path, encoding='utf8')
        elif table_path.endswith('xlsx'):
            df = pd.read_excel(table_path)
        print('1. Read table schema....')
        table_schema = get_table_schema(df)
        print('2. Request LLM...')
        table_name = table_path.split('/')[-2][4:]  # for competition
        prompt = self.PROMPT_TEMPLATE.replace('{table_name}',table_name).replace('{table_schema}', json.dumps(table_schema, indent=4))  # for competition

        # print(prompt)
        try:
            rsp = await self._aask(prompt)
            rsp = rsp.strip()
            if rsp.startswith("```json") and rsp.endswith("```"):
                rsp = rsp.replace('```json', '').strip()
                rsp = rsp.replace('```', '')

        except Exception as e:   # openai.BadRequestError
            print(f'An error occurred while generating the table description!!\n{e}')
            # reduce tokens
            new_table_schema = []
            for column in table_schema:
                if column['dtype'] == 'object':
                    if 'category_examples' in column['example'] and len(str(column['example']['category_examples']).split(' ')) <= 30:
                            continue

                    if 'all_categories' in column['example']:
                        if len(str(column['example']['all_categories']).split(' ')) <= 30:
                            continue

                        column['example']['category_examples'] = column['example']['all_categories']
                        del column['example']['all_categories']

                    column['example']['category_examples'] = column['example']['category_examples'][:2]
                    column['example']['caption'] = 'There are many types in this column, displaying the top 2 most common types'
                new_table_schema.append(column)
            table_schema = new_table_schema
            del new_table_schema
            table_name = table_path.split('/')[-2][4:]  # for competition
            prompt = self.PROMPT_TEMPLATE.replace('{table_name}',table_name).replace('{table_schema}', str(table_schema)) 
            rsp = await self._aask(prompt)

        try:
            column_num = len(df.columns.tolist())
            cell_example_len = sum([len(str(v).split()) for v in df.sample(1).to_dict('records')[0].values()])
            if column_num <= 20 and cell_example_len <= 300:
                cell_chosen_num = 10
            elif column_num <= 50 and cell_example_len <= 500:
                cell_chosen_num = 5
            else:
                cell_chosen_num = 2


            column_description = []

            ana_res = json.loads(rsp)
            if isinstance(ana_res, list):
                ana_res = ana_res[0]

            for column in table_schema:
                for gen_column in ana_res.get('Column_Description', ''):
                    if gen_column['column_name'] == column['column_name']:
                        column['specific_meaning'] = gen_column['specific_meaning']
                        continue
                column_description.append(column)       


            table_desc = {'file_path': table_path,
                    # 'table_content': os.path.basename(table_path),  # for general
                    'table_name': table_path.split('/')[-2],    # for competition
                    'table_description': ana_res.get('Table_Description', ''),
                    'number_of_rows': len(df),
                    'column_list': df.columns.tolist(),
                    # 'cell_example': df.to_dict('records') if len(df) <= 20 and column_num <= 10 else df[:cell_chosen_num].to_dict('records'),
                    'cell_example': df.to_dict('records') if len(df) <= 20 and column_num <= 10 else df.sample(cell_chosen_num).to_dict('records'),
                    'column_description': column_description
                    # 'key_features': ana_res.get('Key_Features', '')
                    }

        except Exception as e:
            print(f'Error (Tabel describe): {e}')
            table_desc =  {'file_path': table_path,
                    'number_of_rows': len(df),
                    'column_list': df.columns.tolist(),
                    'cell_example': df.to_dict('records') if len(df) <= 20 and column_num <= 10 else df.sample(cell_chosen_num).to_dict('records'),
                    'column_description': column_description if len(column_description) > 0 else table_schema,
                    'description': rsp}

        
        if desc_save_path is not None and len(desc_save_path) > 0:
            save_dicts_to_json(table_desc, desc_save_path)
        
        return json.dumps(table_desc, ensure_ascii=False)


