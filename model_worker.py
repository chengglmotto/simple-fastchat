#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
@Author  ：chenggl
@Date    ：2024/9/3 8:52 
@DESC     ：llm实例
'''

import argparse
import asyncio
from typing import Optional

import requests
import uvicorn
import torch
from loguru import logger
from transformers import AutoTokenizer,AutoModelForCausalLM
from fastapi import FastAPI,Request

def load_model(model_path:str) -> None:
    logger.info(f'从{model_path}加载模型')

    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.bfloat16,
        device_map='auto'
    )

    logger.info(f'model device:{model.device}')
    return tokenizer,model

def generate(model,tokenizer,params:dict):
    input_ids = tokenizer.apply_chat_template(
        params['messages'],
        add_generation_prompt=True,
        return_tensors='pt',
    ).to(model.device)

    terminators = [tokenizer.eos_token_id,tokenizer.convert_tokens_to_ids('<|eot_id|>')]
    outputs = model.generate(
        input_ids,
        max_new_tokens =256,
        eos_token_id=terminators,
        do_sample=True,
        temperature=0.6,
        top_p=0.9
    )

    response = outputs[0][input_ids.shape[-1]:]
    return tokenizer.decode(response,skip_special_tokens=True)

class Worker:

    def __init__(
            self,
            controller_addr:str,
            worker_addr:str,
            model_path:str,
            model_name:Optional[str]=None):
        self.controller_addr = controller_addr
        self.worker_addr = worker_addr
        self.tokenizer,self.model = load_model(model_path)
        self.model_name = model_name

    def register_to_controller(self) -> None:
        logger.info('注册到controller')

        url = self.controller_addr+'/register_worker'
        data = {
            'worker_addr':self.worker_addr,
            'model_name':self.model_name
        }

        response = requests.post(url,json=data)
        assert response.status_code == 200

    def generate_gate(self,params:dict):
        return generate(self.model,self.tokenizer,params)

app = FastAPI()

@app.post('/worker_generate')
async def api_generate(request:Request):
    params = await request.json()
    output = await asyncio.to_thread(worker.generate_gate,params)
    return {'output':output}

def create_worker():
    parser = argparse.ArgumentParser('worker')
    parser.add_argument('model_path',type=str,help='Path to the model')
    parser.add_argument('model_name',type=str)
    parser.add_argument('--host',type=str,default='localhost')
    parser.add_argument('--port',type=int,default=21002)
    parser.add_argument('--controller_addr',type=str,default='http://localhost:21001')

    args = parser.parse_args()
    logger.info(f'args:{args}')

    args.worker_addr = f'http://{args.host}:{args.host}'
    worker = Worker(worker_addr=args.worker_addr,controller_addr=args.controller_addr)
    return args,worker

if __name__ == '__main__':
    args,worker = create_worker()

    uvicorn.run(app,host=args.host,port=args.port,log_level='info')