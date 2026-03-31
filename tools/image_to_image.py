"""
图生图工具实现
"""

from pathlib import Path
from typing import Optional, AsyncGenerator, Any

import astrbot.api.message_components as Comp
from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent

from ..minimax_client import MiniMaxClient
from .base import send_error


async def execute_image_to_image(
    client: MiniMaxClient,
    event: AstrMessageEvent,
    data_dir: Path,
    config: dict,
    prompt: str,
    reference_image_url: str,
    aspect_ratio: Optional[str] = None,
    n: Optional[int] = None
) -> AsyncGenerator[Any, None]:
    """
    执行图生图
    
    Args:
        client: MiniMax 客户端
        event: 消息事件
        data_dir: 数据目录
        config: 插件配置
        prompt: 图片描述
        reference_image_url: 参考图片URL
        aspect_ratio: 宽高比
        n: 生成数量
    """
    try:
        # 获取配置
        image_config = config.get('image_config', {})
        
        # 使用参数或配置中的默认值
        model = image_config.get('model', 'image-01')
        final_aspect_ratio = aspect_ratio or image_config.get('aspect_ratio', '1:1')
        final_n = n if n is not None else image_config.get('n', 1)
        
        logger.info(f"开始图生图，提示词: {prompt[:50]}...")
        
        # 调用 API
        result = await client.image_to_image(
            prompt=prompt,
            reference_image_url=reference_image_url,
            model=model,
            aspect_ratio=final_aspect_ratio,
            n=final_n
        )
        
        # 处理返回的图片（同文生图）
        if 'data' in result:
            data = result['data']
            
            # MiniMax API 返回格式: {"data": {"image_urls": ["url1", "url2"]}}
            if 'image_urls' in data:
                image_urls = data['image_urls']
                logger.info(f"成功生成 {len(image_urls)} 张图片")
                
                for url in image_urls:
                    chain = [Comp.Image.fromURL(url)]
                    yield event.chain_result(chain)
            else:
                async for msg in send_error(event, "API 返回数据格式错误：缺少 image_urls"):
                    yield msg
        else:
            async for msg in send_error(event, "API 返回数据格式错误"):
                yield msg
                
    except Exception as e:
        async for msg in send_error(event, str(e)):
            yield msg
