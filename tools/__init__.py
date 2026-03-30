"""
MiniMax 多模态生成器工具模块
"""

from .base import MiniMaxTool
from .speech_synthesis import SpeechSynthesisTool
from .text_to_image import TextToImageTool
from .image_to_image import ImageToImageTool
from .video_generation import VideoGenerationTool
from .music_generation import MusicGenerationTool

__all__ = [
    'MiniMaxTool',
    'SpeechSynthesisTool',
    'TextToImageTool',
    'ImageToImageTool',
    'VideoGenerationTool',
    'MusicGenerationTool',
]
