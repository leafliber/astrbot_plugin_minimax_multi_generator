"""
MiniMax 多模态生成器插件主类
"""

from pathlib import Path
from typing import Optional

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register

from .minimax_client import MiniMaxClient
from .tools import (
    SpeechSynthesisTool,
    TextToImageTool,
    ImageToImageTool,
    VideoGenerationTool,
    MusicGenerationTool,
)


@register(
    "astrbot_plugin_minimax_multi_generator",
    "Leafiber",
    "MiniMax 多模态生成器 - 支持语音合成、图像生成、视频生成和音乐生成",
    "1.0.0",
    "https://github.com/Leafliber/astrbot_plugin_minimax_multi_generator"
)
class MiniMaxPlugin(Star):
    """MiniMax 多模态生成器插件"""
    
    def __init__(self, context: Context, config: AstrBotConfig):
        """
        初始化插件
        
        Args:
            context: AstrBot 上下文
            config: 插件配置
        """
        super().__init__(context)
        self.config = config
        
        # 验证必需配置
        api_key = config.get('api_key')
        if not api_key:
            logger.error("未配置 MiniMax API Key，插件将无法正常工作")
            return
        
        # 获取配置
        base_url = config.get('base_url', 'https://api.minimaxi.com')
        
        # 初始化客户端
        self.client = MiniMaxClient(api_key=api_key, base_url=base_url)
        logger.info(f"MiniMax 客户端已初始化，Base URL: {base_url}")
        
        # 获取 data 目录
        self.data_dir = Path(context.get_data_dir())
        logger.info(f"插件数据目录: {self.data_dir}")
        
        # 注册启用的工具
        self._register_tools()
        
        logger.info("MiniMax 多模态生成器插件已加载")
    
    def _register_tools(self):
        """根据配置注册启用的工具"""
        
        # 语音合成工具
        if self.config.get('enable_speech', True):
            try:
                tool = SpeechSynthesisTool(
                    client=self.client,
                    config=dict(self.config),
                    data_dir=self.data_dir
                )
                self.context.add_llm_tools(tool)
                logger.info("语音合成工具已注册")
            except Exception as e:
                logger.error(f"注册语音合成工具失败: {e}")
        
        # 图像生成工具
        if self.config.get('enable_image', True):
            try:
                # 文生图工具
                text_to_image_tool = TextToImageTool(
                    client=self.client,
                    config=dict(self.config),
                    data_dir=self.data_dir
                )
                self.context.add_llm_tools(text_to_image_tool)
                logger.info("文生图工具已注册")
                
                # 图生图工具
                image_to_image_tool = ImageToImageTool(
                    client=self.client,
                    config=dict(self.config),
                    data_dir=self.data_dir
                )
                self.context.add_llm_tools(image_to_image_tool)
                logger.info("图生图工具已注册")
            except Exception as e:
                logger.error(f"注册图像生成工具失败: {e}")
        
        # 视频生成工具
        if self.config.get('enable_video', True):
            try:
                tool = VideoGenerationTool(
                    client=self.client,
                    config=dict(self.config),
                    data_dir=self.data_dir
                )
                self.context.add_llm_tools(tool)
                logger.info("视频生成工具已注册")
            except Exception as e:
                logger.error(f"注册视频生成工具失败: {e}")
        
        # 音乐生成工具
        if self.config.get('enable_music', True):
            try:
                tool = MusicGenerationTool(
                    client=self.client,
                    config=dict(self.config),
                    data_dir=self.data_dir
                )
                self.context.add_llm_tools(tool)
                logger.info("音乐生成工具已注册")
            except Exception as e:
                logger.error(f"注册音乐生成工具失败: {e}")
    
    @filter.command("minimax_help")
    async def show_help(self, event: AstrMessageEvent):
        """显示帮助信息"""
        help_text = """
🎬 MiniMax 多模态生成器

可用功能：
• 语音合成：将文本转换为语音
• 文生图：根据文本描述生成图片
• 图生图：基于参考图生成新图片
• 视频生成：根据文本描述生成视频
• 音乐生成：根据描述和歌词生成音乐

使用方法：
直接与 AI 对话，AI 会自动调用相应的工具。

示例：
• "用语音合成说：你好世界"
• "生成一张图片：一只可爱的猫咪"
• "创作一首音乐：轻快的民谣风格"

配置：
请在 WebUI 中配置 API Key 以使用本插件。
        """
        yield event.plain_result(help_text.strip())
    
    async def terminate(self):
        """插件卸载时的清理工作"""
        logger.info("MiniMax 多模态生成器插件已卸载")
