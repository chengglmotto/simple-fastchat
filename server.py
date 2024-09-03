#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
@Author  ：chenggl
@Date    ：2024/9/3 8:53 
@DESC     ：应对客户询问
'''
import argparse
import asyncio

import aiohttp
import uvicorn
from fastapi import FastAPI,Request
from loguru import logger

app = FastAPI()
app_settting = {}

async def fetch_remote(url,payload):
     async with aiohttp.ClientSession() as session:
         async with session.post(url,json=payload) as response:
             return await response.json()

async def generate_completion(payload,worker_addr:str):
    return await fetch_remote(worker_addr+'/worker_generate',payload)

async def get_worker_addr(model_name:str) -> str:
    controller_addr = app_settting['controller_addr']
    res = await fetch_remote(
        controller_addr+'/get_worker_addr',{'model':model_name}
    )
    return res['addr']

@app.post('/v1/chat/completions')
async def create_chat_completion(request:Request):
    data = await request.json()

    worker_addr = await get_worker_addr(data['model'])
    response = asyncio.create_task(generate_completion(data,worker_addr))
    await response
    return response.result()


def create_openai_api_server():
    parser = argparse.ArgumentParser('server')
    parser.add_argument('--host',type=str,default='localhost')
    parser.add_argument('--port',type=int,default=8000)
    parser.add_argument('--controller_addr',type=int,default='http://localhost:21001')
    args = parser.parse_args()

    logger.info(f'args:{args}')

    app_settting['controller_addr'] = args.controller_addr
    return args

if __name__ == '__main__':
    args = create_openai_api_server()

    uvicorn.run(app,host=args.host,port=args.host,log_level='info')