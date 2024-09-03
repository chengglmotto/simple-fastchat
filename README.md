## simple-fastchat
### 简介
简化版的fastchat，演示fastchat的模型管理核心代码结构
### 模块
其中controller.py为注册中心，提供模型实例注册、发现(负载均衡)、删除功能；
model_worker.py为模型实例,提供模型实例加载并注册,以及供调用，启动时需提供model_path和model_name
server.py为对外提供的llm对话服务端,每次对话会去获取worker，然后进行调用
