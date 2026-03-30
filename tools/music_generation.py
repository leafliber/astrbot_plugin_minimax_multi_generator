"""
音乐生成工具
"""

from dataclasses import dataclass, field
from typing import Optional

from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger

from .base import MiniMaxTool


@dataclass
class MusicGenerationTool(MiniMaxTool):
    """音乐生成工具"""
    
    name: str = "generate_music"
    description: str = "根据描述和歌词生成音乐。支持纯音乐模式和自动生成歌词。"
    parameters: dict = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "音乐风格和情绪描述，如：轻快的民谣、忧郁的钢琴曲、激昂的摇滚等"
                },
                "lyrics": {
                    "type": "string",
                    "description": "歌词内容（可选）。如果不提供且未启用纯音乐模式，系统可能会自动生成歌词",
                    "default": None
                },
                "is_instrumental": {
                    "type": "boolean",
                    "description": "是否生成纯音乐（无人声）",
                    "default": false
                },
                "lyrics_optimizer": {
                    "type": "boolean",
                    "description": "是否自动生成歌词（当 lyrics 为空时）",
                    "default": false
                }
            },
            "required": ["prompt"]
        }
    )
    
    async def run(
        self,
        event: AstrMessageEvent,
        prompt: str,
        lyrics: Optional[str] = None,
        is_instrumental: bool = False,
        lyrics_optimizer: bool = False
    ):
        """
        执行音乐生成
        
        Args:
            event: 消息事件
            prompt: 音乐描述
            lyrics: 歌词（可选）
            is_instrumental: 是否纯音乐
            lyrics_optimizer: 是否自动生成歌词
        """
        try:
            # 获取配置
            music_config = self.config.get('music_config', {})
            
            # 使用参数或配置中的默认值
            model = music_config.get('model', 'music-2.5+')
            audio_format = music_config.get('audio_format', 'mp3')
            
            logger.info(f"开始生成音乐，描述: {prompt[:50]}...")
            if lyrics:
                logger.info(f"歌词长度: {len(lyrics)} 字符")
            
            # 发送提示消息
            yield event.plain_result("🎵 正在生成音乐，请稍候...")
            
            # 调用 API
            result = await self.client.generate_music(
                prompt=prompt,
                lyrics=lyrics,
                model=model,
                is_instrumental=is_instrumental,
                lyrics_optimizer=lyrics_optimizer,
                audio_format=audio_format
            )
            
            # 提取音频数据
            if 'data' in result and 'audio' in result['data']:
                audio_hex = result['data']['audio']
                audio_bytes = self.hex_to_bytes(audio_hex)
                
                # 获取额外信息
                extra_info = result.get('extra_info', {})
                duration = extra_info.get('music_duration', 0) / 1000  # 转换为秒
                sample_rate = extra_info.get('music_sample_rate', 44100)
                
                # 保存文件
                file_path = self.save_file(audio_bytes, audio_format, prefix="music")
                
                # 发送文件
                logger.info(f"音乐生成完成，时长: {duration:.1f}s，文件大小: {len(audio_bytes)} 字节")
                
                # 发送音乐文件
                filename = f"music_{int(duration)}s.{audio_format}"
                async for msg in self.send_file(event, file_path, filename):
                    yield msg
                
                # 发送额外信息
                if duration > 0:
                    info_msg = f"✅ 音乐已生成\n时长: {duration:.1f} 秒\n采样率: {sample_rate} Hz"
                    yield event.plain_result(info_msg)
            else:
                async for msg in self.send_error(event, "API 返回数据格式错误"):
                    yield msg
                    
        except Exception as e:
            async for msg in self.send_error(event, str(e)):
                yield msg
