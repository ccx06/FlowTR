export CUDA_VISIBLE_DEVICES=0,1,2,3

python -m vllm.entrypoints.openai.api_server \
    --model "model_path" \
    --api-key "your_api_key" \
    --served-model-name "openchat" \
    --max_model_len 20176 \
    --tensor-parallel-size 4 \
    --port 8000 \
    --enable-auto-tool-choice \
    --tool-call-parser hermes 1
