"""
MiniMax 工具模块
提供各种生成工具的实现
"""

from .base import (
    save_file,
    hex_to_bytes,
    send_image,
    send_video,
    send_file,
    send_text,
    send_error,
)

from .speech_synthesis import execute_text_to_speech
from .text_to_image import execute_text_to_image
from .image_to_image import execute_image_to_image
from .video_generation import execute_generate_video
from .music_generation import execute_generate_music

__all__ = [
    # 辅助函数
    'save_file',
    'hex_to_bytes',
    'send_image',
    'send_video',
    'send_file',
    'send_text',
    'send_error',
    # 工具执行函数
    'execute_text_to_speech',
    'execute_text_to_image',
    'execute_image_to_image',
    'execute_generate_video',
    'execute_generate_music',
]
