import requests
from flask import current_app
import json

class AIService:
    def __init__(self):
        self.api_key = current_app.config['SILICONFLOW_API_KEY']
        self.api_url = current_app.config['SILICONFLOW_API_URL']
        self.model = current_app.config['SILICONFLOW_MODEL']

    def get_chat_response(self, messages):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "stream": False,
            "max_tokens": 1000
        }
        
        try:
            current_app.logger.info(f"发送到硅基流动API的请求: {json.dumps(data, ensure_ascii=False)}")
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=30  # 设置超时时间
            )
            
            current_app.logger.info(f"硅基流动API响应状态码: {response.status_code}")
            current_app.logger.info(f"硅基流动API响应内容: {response.text}")
            
            response.raise_for_status()
            result = response.json()
            
            if 'choices' not in result or not result['choices']:
                raise ValueError("API响应中没有choices字段")
                
            if 'message' not in result['choices'][0]:
                raise ValueError("API响应中没有message字段")
                
            if 'content' not in result['choices'][0]['message']:
                raise ValueError("API响应中没有content字段")
                
            return result['choices'][0]['message']['content']
            
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"API请求错误: {str(e)}")
            if hasattr(e.response, 'text'):
                current_app.logger.error(f"API错误响应: {e.response.text}")
            return "抱歉，我现在无法回答。请稍后再试。"
            
        except (KeyError, json.JSONDecodeError, ValueError) as e:
            current_app.logger.error(f"API响应解析错误: {str(e)}")
            return "抱歉，处理响应时出现错误。"
            
        except Exception as e:
            current_app.logger.error(f"未预期的错误: {str(e)}")
            return "抱歉，发生了未知错误。" 