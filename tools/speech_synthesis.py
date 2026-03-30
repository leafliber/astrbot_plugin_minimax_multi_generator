"""
语音合成工具实现
"""

from pathlib import Path
from typing import Optional, AsyncGenerator, Any, Dict

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent

from ..minimax_client import MiniMaxClient
from .base import save_file, hex_to_bytes, send_file, send_error


async def execute_text_to_speech(
    client: MiniMaxClient,
    event: AstrMessageEvent,
    data_dir: Path,
    config: dict,
    text: str,
    voice_id: Optional[str] = None,
    speed: Optional[float] = None,
    emotion: Optional[str] = None
) -> AsyncGenerator[Any, None]:
    """
    执行语音合成
    
    Args:
        client: MiniMax 客户端
        event: 消息事件
        data_dir: 数据目录
        config: 插件配置
        text: 要转换的文本
        voice_id: 音色ID
        speed: 语速
        emotion: 情感表达
    """
    try:
        # 获取配置
        speech_config = config.get('speech_config', {})
        
        # 使用参数或配置中的默认值
        model = speech_config.get('model', 'speech-2.8-hd')
        final_voice_id = voice_id or speech_config.get('voice_id', 'male-qn-qingse')
        final_speed = speed if speed is not None else speech_config.get('speed', 1.0)
        vol = speech_config.get('vol', 1.0)
        pitch = speech_config.get('pitch', 0)
        audio_format = speech_config.get('audio_format', 'mp3')
        
        logger.info(f"开始语音合成，文本长度: {len(text)} 字符")
        
        # 调用 API
        result = await client.text_to_speech(
            text=text,
            model=model,
            voice_id=final_voice_id,
            speed=final_speed,
            vol=vol,
            pitch=pitch,
            emotion=emotion,
            audio_format=audio_format
        )
        
        # 提取音频数据
        if 'data' in result and 'audio' in result['data']:
            audio_hex = result['data']['audio']
            audio_bytes = hex_to_bytes(audio_hex)
            
            # 保存文件
            file_path = save_file(audio_bytes, data_dir, audio_format, prefix="speech")
            
            # 发送文件
            logger.info(f"语音合成完成，文件大小: {len(audio_bytes)} 字节")
            
            # 使用文件形式发送（因为 MP3 不是 WAV）
            async for msg in send_file(event, file_path, f"speech.{audio_format}"):
                yield msg
        else:
            async for msg in send_error(event, "API 返回数据格式错误"):
                yield msg
                
    except Exception as e:
        async for msg in send_error(event, str(e)):
            yield msg
