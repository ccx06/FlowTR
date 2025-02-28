"""
@Desc: Inference on Databench benchmark.
"""
import json
import os
import jsonlines
import fire
from postprocess import response_format
from table_agent import TableReasonFlow

cur_dir = os.path.dirname(os.path.abspath(__file__))


def semeval_databench_infer(model_version, config_file, mode='test', dataset='databench_test', react_round=5, vote=False, vote_k=1):

    data_dir = os.path.join(cur_dir, f'data/{dataset}')
    result_save_dir = os.path.join(cur_dir, f'results/{dataset}/{model_version}')
    table_schema_dir = os.path.join(cur_dir, f'data/{dataset}/table_schema/{model_version}/{mode}')

    os.makedirs(result_save_dir, exist_ok=True)
    os.makedirs(table_schema_dir, exist_ok=True)
    
    data_path = os.path.join(data_dir, f'{mode}.json')
    data = json.load(open(data_path, 'r', encoding='utf8'))

    if vote and vote_k>1:
        result_file = os.path.join(result_save_dir, f'{mode}_{model_version}_votek_{vote_k}_result.jsonl')
    else:
        result_file = os.path.join(result_save_dir, f'{mode}_{model_version}_result.jsonl')
    
    print('Start!')
    print("***** Arguments Settings *****")
    print(f'model_version: {model_version}, mode: {mode}, dataset: {dataset}, vote: {vote}, vote_k: {vote_k}')
    print("***** Data Path Settings *****")
    print(f'data_dir: ', data_dir)
    print(f'table_schema_dir: ', table_schema_dir)
    print(f'result_file: ', result_file)

    table_agent_pipe = TableReasonFlow(config_file=config_file, max_react_round=react_round)

    failed_num = 0
    with jsonlines.open(result_file, 'w') as fw:
        fw._flush = True
        
        for i, d in enumerate(data):
            res_line = d
            if (mode == 'test' or mode == 'test_parta' or mode == 'test_partb' or 'test_hint' in mode or mode ==
            'test_debug') and 'attachments' not in d:
                d['attachments'] = f"DataBench/test/{d['dataset']}/all.csv"
            elif (mode == 'test_lite' or mode == 'test_lite_parta' or mode == 'test_lite_partb') and 'attachments' not in d:
                d['attachments'] = f"DataBench/test/{d['dataset']}/sample.csv"

            table_path = os.path.join(data_dir, d['attachments'])
            question = d['question']
            table_desc_file = os.path.join(table_schema_dir, d['attachments'].split('/')[2]+'.json')  
            try:
                
                if vote and vote_k > 1:
                    # voting mode
                    response, log_item =  table_agent_pipe.simple_voting(question, table_path, table_desc_file, k=vote_k)
                else:
                    response, log_item =  table_agent_pipe.execute_qa(question, table_path, table_desc_file)

                try:
                    log_item['format_response'] = response_format(question, response)
                except Exception as e:
                    print(f'Error occur! when formating answer: {e}')
            except Exception as e:
                failed_num += 1
                print(f'Failed! --- {question}')
                print(e)
                res_line['execute_status'] = 'fail'
                res_line['response'] = "fail"
                fw.write(res_line)
                print(f'write {i+1}')
                continue
            
            # write
            for name, item in log_item.items():
                if name not in res_line:
                    res_line[name] = item
            res_line['execute_status'] = 'success'
            fw.write(res_line)
            print(f'write {i+1}')

    print(f'Done!\nFailed {failed_num}\n The results write to {result_save_dir}.')



if __name__ == "__main__":
    # fire.Fire(semeval_databench_infer) # (model_version='baseline_v0_1203')
    
    # import sys
    # exp_name = sys.argv[1]
    # config_file = sys.argv[2]
    # mode = sys.argv[3]
    # dataset = sys.argv[4]
    # react_round = int(sys.argv[5])
    
    # semeval_databench_infer(model_version=exp_name, 
    #             config_file=config_file,
    #             mode=mode, 
    #             dataset=dataset, 
    #             react_round=react_round,
    #             vote=False)
    
    exp_name="test_exp1"
    config_file="agent_config/FlowTR_exp1_config.yaml"
    dataset="databench_test"
    react_round=5
    mode="test"

    semeval_databench_infer(model_version=exp_name, 
            config_file=config_file,
            mode=mode, 
            dataset=dataset, 
            react_round=react_round,
            vote=False)

