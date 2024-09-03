#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
@Author  ：chenggl
@Date    ：2024/9/3 8:53 
@DESC     ：controller类,用来注册、删除和选择llm实例(worker)
'''
import argparse

import uvicorn
import random
from fastapi import FastAPI,Request
from loguru import logger

class Controller:

    def __init__(self):
        self.worker_info = {}

    def register_worker(self,
                        worker_addr:str,
                        model_name:str):
        logger.info(f'注册worker:{worker_addr},{model_name}')
        self.worker_info[worker_addr] = {'model_name':model_name,'burden':1}

    def remove_worker(self,
                      model_name:str):
        # 为请求分配worker
        worker_addr_list = []
        for worker_addr, model_info in self.worker_info.items():
            if model_name == model_info['model_name']:
                worker_addr_list.append(worker_addr)
        if len(worker_addr_list) ==0:
            logger.info(f'当前不存在模型:{model_name}的worker,无需删除')
            return
        else:
            for worker_addr in worker_addr_list:
                del self.worker_info[worker_addr]
            logger.info(f'删除worker:{model_name}')

    def get_worker_addr(self,model_name:str):
        #为请求分配worker
        worker_addr_list = []
        worker_burden_list = []
        for worker_addr,model_info in self.worker_info.items():
            if model_name == model_info['model_name']:
                worker_addr_list.append(worker_addr)
                worker_burden_list.append(model_info['burden'])

        assert len(worker_addr_list) >0,f'没有worker给模型: {model_name}'

        #按请求次数的倒数作为权重,根据权重随机分配worker
        worker_addr =  worker_addr_list[self.weight_choice(worker_burden_list)]
        self.worker_info[worker_addr]['burden'] +=1
        return worker_addr

    def weight_choice(self,burden_list):
        '''
        根据每个节点的请求数,进行按权重的随机选择
        :param burden_list:
        :return:
        '''
        weight_list = [ 1.0/burden for burden in burden_list]
        return  random.choices(burden_list,weights=weight_list)[0]


app = FastAPI()

@app.post('/register_worker')
async def register_worker(request:Request):
    data = await request.json()

    controller.register_worker(
        worker_addr=data['worker_addr'],
        model_name=data['model_name']
    )

@app.post('/get_worker_addr')
async def get_worker_addr(request:Request):
    data = await request.json()
    addr = controller.get_worker_addr(data['model'])
    return {'addr':addr}


@app.post('/remove_worker')
async def remove_worke(request:Request):
    data = request.json()
    controller.remove_worker(data['model_name'])


def create_controller():
    parser = argparse.ArgumentParser('controller')
    parser.add_argument('--host',type=str,default='localhost')
    parser.add_argument('--port',type=int,default=21001)

    args = parser.parse_args()
    logger.info(f'args:{args}')

    controller = Controller()
    return args,controller


if __name__ == '__main__':
    try:
        args,controller = create_controller()

        uvicorn.run(app,host=args.host,port=args.port,log_level='info')
    except Exception  as e:
        print(e)