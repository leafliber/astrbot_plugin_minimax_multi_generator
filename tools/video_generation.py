"""
视频生成工具
"""

import asyncio
from dataclasses import dataclass, field
from typing import Optional

from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger

from .base import MiniMaxTool


@dataclass
class VideoGenerationTool(MiniMaxTool):
    """视频生成工具"""
    
    name: str = "generate_video"
    description: str = "根据文本描述生成视频。支持多种分辨率和时长。生成时间较长，请耐心等待。"
    parameters: dict = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "视频的文本描述，详细描述想要的视频内容和场景"
                },
                "duration": {
                    "type": "integer",
                    "description": "视频时长（秒），可选6或10",
                    "default": 6,
                    "enum": [6, 10]
                },
                "resolution": {
                    "type": "string",
                    "description": "视频分辨率",
                    "default": "720P",
                    "enum": ["720P", "768P", "1080P"]
                }
            },
            "required": ["prompt"]
        }
    )
    
    async def run(
        self,
        event: AstrMessageEvent,
        prompt: str,
        duration: Optional[int] = None,
        resolution: Optional[str] = None
    ):
        """
        执行视频生成
        
        Args:
            event: 消息事件
            prompt: 视频描述
            duration: 视频时长（可选，使用配置中的默认值）
            resolution: 分辨率（可选，使用配置中的默认值）
        """
        try:
            # 获取配置
            video_config = self.config.get('video_config', {})
            
            # 使用参数或配置中的默认值
            model = video_config.get('model', 'MiniMax-Hailuo-2.3')
            final_duration = duration if duration is not None else video_config.get('duration', 6)
            final_resolution = resolution or video_config.get('resolution', '720P')
            poll_interval = video_config.get('poll_interval', 5)
            max_poll_attempts = video_config.get('max_poll_attempts', 60)
            
            logger.info(f"开始生成视频，提示词: {prompt[:50]}...")
            
            # 先发送提示消息
            yield event.plain_result(f"🎬 开始生成视频，预计需要 1-3 分钟，请稍候...")
            
            # 创建视频生成任务
            task_id = await self.client.create_video_task(
                prompt=prompt,
                model=model,
                duration=final_duration,
                resolution=final_resolution
            )
            
            logger.info(f"视频任务已创建，task_id: {task_id}")
            
            # 轮询查询任务状态
            attempt = 0
            file_id = None
            
            while attempt < max_poll_attempts:
                attempt += 1
                
                # 查询任务状态
                status_result = await self.client.query_video_task(task_id)
                
                # 检查状态
                status = status_result.get('status')
                
                if status == 'success':
                    # 任务成功，获取 file_id
                    file_id = status_result.get('file_id')
                    logger.info(f"视频生成完成，file_id: {file_id}")
                    break
                elif status == 'failed':
                    # 任务失败
                    error_msg = status_result.get('error', '未知错误')
                    async for msg in self.send_error(event, f"视频生成失败: {error_msg}"):
                        yield msg
                    return
                else:
                    # 任务进行中
                    logger.info(f"视频生成中... (尝试 {attempt}/{max_poll_attempts})")
                    await asyncio.sleep(poll_interval)
            
            # 检查是否超时
            if file_id is None:
                async for msg in self.send_error(event, "视频生成超时，请稍后重试"):
                    yield msg
                return
            
            # 下载视频
            logger.info("正在下载视频...")
            video_data = await self.client.download_file(file_id)
            
            # 保存文件
            file_path = self.save_file(video_data, "mp4", prefix="video")
            
            # 发送视频
            logger.info(f"视频已生成，文件大小: {len(video_data)} 字节")
            async for msg in self.send_video(event, file_path):
                yield msg
                    
        except Exception as e:
            async for msg in self.send_error(event, str(e)):
                yield msg
