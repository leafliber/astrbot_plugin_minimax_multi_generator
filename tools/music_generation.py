"""
音乐生成工具实现
"""

from pathlib import Path
from typing import Optional, AsyncGenerator, Any, Dict

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent

from ..minimax_client import MiniMaxClient
from .base import save_file, hex_to_bytes, send_file, send_error


async def execute_generate_music(
    client: MiniMaxClient,
    event: AstrMessageEvent,
    data_dir: Path,
    config: dict,
    prompt: str,
    lyrics: Optional[str] = None,
    is_instrumental: Optional[bool] = None,
    lyrics_optimizer: Optional[bool] = None
) -> AsyncGenerator[Any, None]:
    """
    执行音乐生成
    
    Args:
        client: MiniMax 客户端
        event: 消息事件
        data_dir: 数据目录
        config: 插件配置
        prompt: 音乐风格描述
        lyrics: 歌词内容
        is_instrumental: 是否生成纯音乐
        lyrics_optimizer: 是否自动生成歌词
    """
    try:
        # 获取配置
        music_config = config.get('music_config', {})
        
        # 使用参数或配置中的默认值
        model = music_config.get('model', 'music-2.5+')
        final_is_instrumental = is_instrumental if is_instrumental is not None else music_config.get('is_instrumental', False)
        final_lyrics_optimizer = lyrics_optimizer if lyrics_optimizer is not None else music_config.get('lyrics_optimizer', False)
        
        logger.info(f"开始生成音乐，提示词: {prompt[:50]}...")
        
        # 调用 API
        result = await client.generate_music(
            prompt=prompt,
            model=model,
            lyrics=lyrics,
            is_instrumental=final_is_instrumental,
            lyrics_optimizer=final_lyrics_optimizer
        )
        
        # 提取音频数据
        if 'data' in result and 'audio' in result['data']:
            audio_hex = result['data']['audio']
            audio_bytes = hex_to_bytes(audio_hex)
            
            # 保存文件
            file_path = save_file(audio_bytes, data_dir, 'mp3', prefix='music')
            
            # 发送文件
            logger.info(f"音乐生成完成，文件大小: {len(audio_bytes)} 字节")
            
            async for msg in send_file(event, file_path, "music.mp3"):
                yield msg
        else:
            async for msg in send_error(event, "API 返回数据格式错误"):
                yield msg
                
    except Exception as e:
        async for msg in send_error(event, str(e)):
            yield msg
