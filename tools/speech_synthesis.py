"""
语音合成工具
"""

from dataclasses import dataclass, field
from typing import Optional

from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger

from .base import MiniMaxTool


@dataclass
class SpeechSynthesisTool(MiniMaxTool):
    """语音合成工具"""
    
    name: str = "text_to_speech"
    description: str = "将文本转换为语音。支持多种音色、语速和情感表达。"
    parameters: dict = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "要转换为语音的文本内容"
                },
                "voice_id": {
                    "type": "string",
                    "description": "音色ID，默认为清新男声（male-qn-qingse）",
                    "default": "male-qn-qingse"
                },
                "speed": {
                    "type": "number",
                    "description": "语速，范围0.5-2.0，默认1.0",
                    "default": 1.0
                },
                "emotion": {
                    "type": "string",
                    "description": "情感表达（可选），如：happy, sad, angry等",
                    "default": None
                }
            },
            "required": ["text"]
        }
    )
    
    async def run(
        self,
        event: AstrMessageEvent,
        text: str,
        voice_id: Optional[str] = None,
        speed: Optional[float] = None,
        emotion: Optional[str] = None
    ):
        """
        执行语音合成
        
        Args:
            event: 消息事件
            text: 要转换的文本
            voice_id: 音色ID（可选，使用配置中的默认值）
            speed: 语速（可选，使用配置中的默认值）
            emotion: 情感（可选）
        """
        try:
            # 获取配置
            speech_config = self.config.get('speech_config', {})
            
            # 使用参数或配置中的默认值
            model = speech_config.get('model', 'speech-2.8-hd')
            final_voice_id = voice_id or speech_config.get('voice_id', 'male-qn-qingse')
            final_speed = speed if speed is not None else speech_config.get('speed', 1.0)
            vol = speech_config.get('vol', 1.0)
            pitch = speech_config.get('pitch', 0)
            audio_format = speech_config.get('audio_format', 'mp3')
            
            logger.info(f"开始语音合成，文本长度: {len(text)} 字符")
            
            # 调用 API
            result = await self.client.text_to_speech(
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
                audio_bytes = self.hex_to_bytes(audio_hex)
                
                # 保存文件
                file_path = self.save_file(audio_bytes, audio_format, prefix="speech")
                
                # 发送文件
                logger.info(f"语音合成完成，文件大小: {len(audio_bytes)} 字节")
                
                # 使用文件形式发送（因为 MP3 不是 WAV）
                async for msg in self.send_file(event, file_path, f"speech.{audio_format}"):
                    yield msg
            else:
                async for msg in self.send_error(event, "API 返回数据格式错误"):
                    yield msg
                    
        except Exception as e:
            async for msg in self.send_error(event, str(e)):
                yield msg
