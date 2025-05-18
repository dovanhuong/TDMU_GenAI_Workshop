#!/bin/bash
python -m vllm.entrypoints.openai.api_server \
    --model /home/tonydev/projects/ESTEC_prj/9.Mistral-7b-instruct-v0.2/model_trained \
    --tokenizer /home/tonydev/projects/ESTEC_prj/9.Mistral-7b-instruct-v0.2/model_trained \
    --served-model-name mistral \
    --max-model-len 4096

