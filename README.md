## Flow-of-Table-Reasoning for SemEval-2025 Task 8
Official implementation of **Flow-of-Table-Reasoning (FlowTR)** framework, developed for SemEval-2025 Task8: Question-Answering over Tabular Data.

## Environment
Our framework is built on the [MetaGPT](https://github.com/geekan/MetaGPT) library.
```
Python 3.9 or later, but less than 3.12
metagpt >= 0.8.1
openai == 1.6.1
vllm (optional)
```


## Data Prepare
- For DataBench_test dataset, We converted each table data into a CSV file and organized the QA Excel file into JSON, refer to `data/databench_test/DataBench/test/`, `data/databench_test/test.json` and `data/databench_test/test_lite.json`.

 
- Train & dev dataset download [link](https://huggingface.co/datasets/cardiffnlp/databench)


## Model Deployment
We deploy the LLMs with OpenAI-style API and vLLM locally. Refer to `vllm_service/run_qwen2_5_service_8000.sh`

## Important codes
1. `data/`: Data storage directory.
2. `agent_config/` : Store LLM and prompt configuration files.
3. `prompts/`: Prompt templates storage directory.
4. `roles/*.py` : Role definition codes. For examples, *table reader* for generating table description, *programmer* to write codes, etc.
5. `actions/*.py` : Action (that roles need to use) definition codes.
6. `table_agent.py` : Main function entrance. Flow-of-Table-Reasoning definition.
7. `databench_inder.py` : Developed for running DataBench dataset.


## Quick Start
### 1. Configure model interfaces and prompt templates.
- Create the config file in `agent_config/`. Example: `agent_config/example.yaml`
    
- Set the LLMs and prompt templates you prefer in the config file.
    -  LLM config (Refer to `agent_config/qwen2_5_32b_api_example.yaml`):

        For close-sourced api, usage:
        ```
        llm:
        api_type: "openai"  # or azure / ollama / groq etc.
        model: "gpt-4-turbo"  # or gpt-3.5-turbo
        base_url: "https://api.openai.com/v1"  # or forward url / other llm url
        api_key: "YOUR_API_KEY"
        ```

        For the model employed as described in [Model Deployment](#model_dep), usage:
        ```
        llm:
        api_type: open_llm
        base_url: "http://{ip}:{port}/v1"
        model: "{model}"
        temperature: 0
        calc_usage: false
        api_key: your_api_key
        ```

    - Prompt config
        Example prompts: `prompts/*.txt`

### 2. RUN
- Main program entrance: `table_agent.py`.

    Run table_agent.py with your table, query and agent config file.
    ```
    python table_agent.py
    ```

- Run on DataBench: `databench_infer.py`
    ```
    python databench_infer.py
    ```

## Reference
```
@inproceedings{hong2024metagpt,
      title={Meta{GPT}: Meta Programming for A Multi-Agent Collaborative Framework},
      author={Sirui Hong and Mingchen Zhuge and Jonathan Chen and Xiawu Zheng and Yuheng Cheng and Jinlin Wang and Ceyao Zhang and Zili Wang and Steven Ka Shing Yau and Zijuan Lin and Liyang Zhou and Chenyu Ran and Lingfeng Xiao and Chenglin Wu and J{\"u}rgen Schmidhuber},
      booktitle={The Twelfth International Conference on Learning Representations},
      year={2024},
      url={https://openreview.net/forum?id=VtmBAGCN7o}
}

@inproceedings{oses-etal-2024-databench,
    title = "Question Answering over Tabular Data with DataBench: A Large-Scale Empirical Evaluation of LLMs",
    author = "Jorge Osés Grijalba and Luis Alfonso Ureña-López and
    Eugenio Martínez Cámara and Jose Camacho-Collados",
    booktitle = "Proceedings of LREC-COLING 2024",
    year = "2024",
    address = "Turin, Italy"
}
```