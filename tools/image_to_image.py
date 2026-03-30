"""
图生图工具
"""

import aiohttp
from dataclasses import dataclass, field
from typing import Optional, List

from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger

from .base import MiniMaxTool


@dataclass
class ImageToImageTool(MiniMaxTool):
    """图生图工具"""
    
    name: str = "image_to_image"
    description: str = "基于参考图片生成新图片，保持人物形象一致性。适用于为同一角色生成不同情境下的图片。"
    parameters: dict = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "图片的文本描述，描述想要的场景和动作"
                },
                "reference_image_url": {
                    "type": "string",
                    "description": "参考图片的 URL（需要包含清晰的人物主体）"
                },
                "aspect_ratio": {
                    "type": "string",
                    "description": "图片宽高比，如：1:1, 16:9, 4:3, 9:16等",
                    "default": "1:1",
                    "enum": ["1:1", "16:9", "4:3", "3:2", "2:3", "3:4", "9:16", "21:9"]
                },
                "n": {
                    "type": "integer",
                    "description": "生成图片数量，范围1-9",
                    "default": 1,
                    "minimum": 1,
                    "maximum": 9
                }
            },
            "required": ["prompt", "reference_image_url"]
        }
    )
    
    async def _download_image(self, url: str) -> bytes:
        """
        下载图片
        
        Args:
            url: 图片 URL
            
        Returns:
            图片二进制数据
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    raise Exception(f"下载图片失败: {response.status}")
    
    async def run(
        self,
        event: AstrMessageEvent,
        prompt: str,
        reference_image_url: str,
        aspect_ratio: Optional[str] = None,
        n: Optional[int] = None
    ):
        """
        执行图生图
        
        Args:
            event: 消息事件
            prompt: 图片描述
            reference_image_url: 参考图片 URL
            aspect_ratio: 宽高比（可选，使用配置中的默认值）
            n: 生成数量（可选，使用配置中的默认值）
        """
        try:
            # 获取配置
            image_config = self.config.get('image_config', {})
            
            # 使用参数或配置中的默认值
            model = image_config.get('model', 'image-01')
            final_aspect_ratio = aspect_ratio or image_config.get('aspect_ratio', '1:1')
            final_n = n if n is not None else image_config.get('n', 1)
            response_format = image_config.get('response_format', 'url')
            
            logger.info(f"开始图生图，提示词: {prompt[:50]}...")
            logger.info(f"参考图片: {reference_image_url}")
            
            # 调用 API
            result = await self.client.generate_image(
                prompt=prompt,
                model=model,
                aspect_ratio=final_aspect_ratio,
                n=final_n,
                response_format=response_format,
                subject_reference=[
                    {
                        "type": "character",
                        "image_file": reference_image_url
                    }
                ]
            )
            
            # 提取图片数据
            if 'data' in result:
                image_urls = result['data'].get('image_urls', [])
                
                if not image_urls:
                    async for msg in self.send_error(event, "未生成任何图片"):
                        yield msg
                        return
                
                # 下载并发送图片
                success_count = 0
                for idx, url in enumerate(image_urls):
                    try:
                        # 下载图片
                        image_data = await self._download_image(url)
                        
                        # 保存文件
                        file_path = self.save_file(image_data, "jpg", prefix=f"i2i_{idx}")
                        
                        # 发送图片
                        async for msg in self.send_image(event, file_path):
                            yield msg
                        
                        success_count += 1
                    except Exception as e:
                        logger.error(f"处理第 {idx + 1} 张图片失败: {e}")
                
                # 发送完成提示
                if success_count > 0:
                    logger.info(f"图生图完成，成功: {success_count}/{len(image_urls)}")
                    if success_count < len(image_urls):
                        yield event.plain_result(f"✅ 成功生成 {success_count} 张图片（共 {len(image_urls)} 张）")
                else:
                    async for msg in self.send_error(event, "所有图片生成失败"):
                        yield msg
            else:
                async for msg in self.send_error(event, "API 返回数据格式错误"):
                    yield msg
                    
        except Exception as e:
            async for msg in self.send_error(event, str(e)):
                yield msg
