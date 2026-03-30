"""
视频生成工具实现
"""

import asyncio
from pathlib import Path
from typing import Optional, AsyncGenerator, Any, Dict

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent

from ..minimax_client import MiniMaxClient
from .base import save_file, send_video, send_text, send_error


async def execute_generate_video(
    client: MiniMaxClient,
    event: AstrMessageEvent,
    data_dir: Path,
    config: dict,
    prompt: str,
    duration: Optional[int] = None,
    resolution: Optional[str] = None
) -> AsyncGenerator[Any, None]:
    """
    执行视频生成
    
    Args:
        client: MiniMax 客户端
        event: 消息事件
        data_dir: 数据目录
        config: 插件配置
        prompt: 视频描述
        duration: 视频时长
        resolution: 分辨率
    """
    try:
        # 获取配置
        video_config = config.get('video_config', {})
        
        # 使用参数或配置中的默认值
        model = video_config.get('model', 'MiniMax-Hailuo-2.3')
        final_duration = duration if duration is not None else video_config.get('duration', 6)
        final_resolution = resolution or video_config.get('resolution', '720P')
        
        logger.info(f"开始生成视频，提示词: {prompt[:50]}...")
        async for msg in send_text(event, f"⏳ 视频生成中，预计需要1-3分钟，请稍候..."):
            yield msg
        
        # 创建视频生成任务
        task_id = await client.create_video_task(
            prompt=prompt,
            model=model,
            duration=final_duration,
            resolution=final_resolution
        )
        
        if not task_id:
            async for msg in send_error(event, "创建视频任务失败"):
                yield msg
            return
        
        logger.info(f"视频任务已创建，task_id: {task_id}")
        
        # 轮询查询任务状态
        max_attempts = 60  # 最多查询60次
        poll_interval = 5  # 每5秒查询一次
        
        for attempt in range(max_attempts):
            await asyncio.sleep(poll_interval)
            
            status_result = await client.query_video_task(task_id)
            status = status_result.get('status')
            
            logger.info(f"视频任务状态 (第{attempt+1}次): {status}")
            
            if status == 'Success':
                # 下载视频
                file_id = status_result.get('file_id')
                if file_id:
                    video_bytes = await client.download_video(file_id)
                    file_path = save_file(video_bytes, data_dir, 'mp4', prefix='video')
                    
                    logger.info(f"视频生成完成，文件大小: {len(video_bytes)} 字节")
                    async for msg in send_video(event, file_path):
                        yield msg
                else:
                    async for msg in send_error(event, "无法获取视频文件ID"):
                        yield msg
                break
                
            elif status == 'Failed':
                async for msg in send_error(event, "视频生成失败"):
                    yield msg
                break
        
        else:
            async for msg in send_error(event, "视频生成超时"):
                yield msg
                
    except Exception as e:
        async for msg in send_error(event, str(e)):
            yield msg
