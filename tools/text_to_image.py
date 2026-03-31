"""
文生图工具实现
"""

import base64
from pathlib import Path
from typing import Optional, AsyncGenerator, Any, Dict

import astrbot.api.message_components as Comp
from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent

from ..minimax_client import MiniMaxClient
from .base import save_file, send_image, send_error


async def execute_text_to_image(
    client: MiniMaxClient,
    event: AstrMessageEvent,
    data_dir: Path,
    config: dict,
    prompt: str,
    aspect_ratio: Optional[str] = None,
    n: Optional[int] = None
) -> AsyncGenerator[Any, None]:
    """
    执行文生图
    
    Args:
        client: MiniMax 客户端
        event: 消息事件
        data_dir: 数据目录
        config: 插件配置
        prompt: 图片描述
        aspect_ratio: 宽高比
        n: 生成数量
    """
    try:
        # 调试：打印 config 类型
        logger.info(f"config type: {type(config)}, config: {config}")
        
        # 获取配置
        image_config = config.get('image_config', {})
        
        # 使用参数或配置中的默认值
        model = image_config.get('model', 'image-01')
        final_aspect_ratio = aspect_ratio or image_config.get('aspect_ratio', '1:1')
        final_n = n if n is not None else image_config.get('n', 1)
        
        logger.info(f"开始生成图片，提示词: {prompt[:50]}...")
        
        # 调用 API
        result = await client.text_to_image(
            prompt=prompt,
            model=model,
            aspect_ratio=final_aspect_ratio,
            n=final_n
        )
        
        # 处理返回的图片
        if 'data' in result:
            images = result['data']
            logger.info(f"成功生成 {len(images)} 张图片")
            
            for idx, img_data in enumerate(images):
                if 'url' in img_data:
                    # 如果返回 URL，直接发送
                    chain = [Comp.Image.fromURL(img_data['url'])]
                    yield event.chain_result(chain)
                elif 'b64_json' in img_data:
                    # 如果返回 base64，保存后发送
                    img_bytes = base64.b64decode(img_data['b64_json'])
                    file_path = save_file(img_bytes, data_dir, 'png', prefix='image')
                    
                    async for msg in send_image(event, file_path):
                        yield msg
        else:
            async for msg in send_error(event, "API 返回数据格式错误"):
                yield msg
                
    except Exception as e:
        async for msg in send_error(event, str(e)):
            yield msg
