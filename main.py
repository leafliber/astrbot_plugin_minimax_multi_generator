"""
MiniMax 多模态生成器插件主类
"""

from typing import Any, Optional

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register
from astrbot.core.utils.astrbot_path import get_astrbot_data_path

from .minimax_client import MiniMaxClient
from .tools import (
    send_error,
    execute_text_to_speech,
    execute_text_to_image,
    execute_image_to_image,
    execute_generate_video,
    execute_generate_music,
)


@register(
    "minimax_multi_generator",
    "Leafiber",
    "MiniMax 多模态生成器 - 支持语音合成、图像生成、视频生成和音乐生成",
    "1.0.0",
    "https://github.com/leafliber/astrbot_plugin_minimax_multi_generator"
)
class MiniMaxPlugin(Star):
    """MiniMax 多模态生成器插件"""
    
    def __init__(self, context: Context, config: Optional[AstrBotConfig] = None):
        """
        初始化插件
        
        Args:
            context: AstrBot 插件上下文
            config: AstrBot 用户配置（可选）
        """
        super().__init__(context)
        self.context: Context = context

        if config is not None:
            if isinstance(config, dict):
                self.config = config
            elif hasattr(config, '__dict__'):
                self.config = vars(config)
            else:
                try:
                    self.config = dict(config)
                except:
                    self.config = {}
        elif hasattr(context, 'config') and context.config is not None:
            if isinstance(context.config, dict):
                self.config = context.config
            elif hasattr(context.config, '__dict__'):
                self.config = vars(context.config)
            else:
                try:
                    self.config = dict(context.config)
                except:
                    self.config = {}
        else:
            self.config = {}
        
        # 验证必需配置
        api_key = self.config.get('api_key')
        if not api_key:
            logger.error("未配置 MiniMax API Key，插件将无法正常工作")
            return
        
        # 获取配置
        base_url = self.config.get('base_url', 'https://api.minimaxi.com')
        
        # 初始化客户端
        self.client = MiniMaxClient(api_key=api_key, base_url=base_url)
        logger.info(f"MiniMax 客户端已初始化，Base URL: {base_url}")
        
        # 获取插件数据目录（AstrBot >= 4.9.2）
        self.data_dir = get_astrbot_data_path() / "plugin_data" / self.name
        self.data_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"插件数据目录: {self.data_dir}")
        
        logger.info("MiniMax 多模态生成器插件已加载")
    
    # ==================== 语音合成工具 ====================
    
    @filter.llm_tool(name="text_to_speech")
    async def text_to_speech(
        self,
        event: AstrMessageEvent,
        text: str,
        voice_id: Optional[str] = None,
        speed: Optional[float] = None,
        emotion: Optional[str] = None
    ):
        '''将文本转换为语音。支持多种音色、语速和情感表达。

        Args:
            text(string): 要转换为语音的文本内容
            voice_id(string): 音色ID，默认为清新男声（male-qn-qingse）
            speed(number): 语速，范围0.5-2.0，默认1.0
            emotion(string): 情感表达（可选），如：happy, sad, angry等
        '''
        # 检查是否启用
        if not self.config.get('enable_speech', True):
            async for msg in send_error(event, "语音合成功能未启用，请在配置中开启"):
                yield msg
            return
        
        # 调用工具执行函数
        async for msg in execute_text_to_speech(
            client=self.client,
            event=event,
            data_dir=self.data_dir,
            config=self.config,
            text=text,
            voice_id=voice_id,
            speed=speed,
            emotion=emotion
        ):
            yield msg
    
    # ==================== 文生图工具 ====================
    
    @filter.llm_tool(name="text_to_image")
    async def text_to_image(
        self,
        event: AstrMessageEvent,
        prompt: str,
        aspect_ratio: Optional[str] = None,
        n: Optional[int] = None
    ):
        '''根据文本描述生成图片。

        Args:
            prompt(string): 图片描述，详细描述想要生成的图片内容
            aspect_ratio(string): 宽高比，可选值：1:1, 16:9, 9:16, 4:3, 3:4等
            n(number): 生成数量，1-9张，默认1张
        '''
        # 检查是否启用
        if not self.config.get('enable_image', True):
            async for msg in send_error(event, "图像生成功能未启用，请在配置中开启"):
                yield msg
            return
        
        # 调用工具执行函数
        async for msg in execute_text_to_image(
            client=self.client,
            event=event,
            data_dir=self.data_dir,
            config=self.config,
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            n=n
        ):
            yield msg
    
    # ==================== 图生图工具 ====================
    
    @filter.llm_tool(name="image_to_image")
    async def image_to_image(
        self,
        event: AstrMessageEvent,
        prompt: str,
        reference_image_url: str,
        aspect_ratio: Optional[str] = None,
        n: Optional[int] = None
    ):
        '''基于参考图片生成新图片，保持人物形象一致性。

        Args:
            prompt(string): 图片描述，描述想要生成的新图片内容
            reference_image_url(string): 参考图片的URL，需要包含清晰的人物主体
            aspect_ratio(string): 宽高比，可选值：1:1, 16:9, 9:16, 4:3, 3:4等
            n(number): 生成数量，1-9张，默认1张
        '''
        # 检查是否启用
        if not self.config.get('enable_image', True):
            async for msg in send_error(event, "图像生成功能未启用，请在配置中开启"):
                yield msg
            return
        
        # 调用工具执行函数
        async for msg in execute_image_to_image(
            client=self.client,
            event=event,
            data_dir=self.data_dir,
            config=self.config,
            prompt=prompt,
            reference_image_url=reference_image_url,
            aspect_ratio=aspect_ratio,
            n=n
        ):
            yield msg
    
    # ==================== 视频生成工具 ====================
    
    @filter.llm_tool(name="generate_video")
    async def generate_video(
        self,
        event: AstrMessageEvent,
        prompt: str,
        duration: Optional[int] = None,
        resolution: Optional[str] = None
    ):
        '''根据文本描述生成视频。

        Args:
            prompt(string): 视频描述，详细描述想要生成的视频内容
            duration(number): 视频时长，可选6或10秒
            resolution(string): 分辨率，可选：720P, 768P, 1080P
        '''
        # 检查是否启用
        if not self.config.get('enable_video', True):
            async for msg in send_error(event, "视频生成功能未启用，请在配置中开启"):
                yield msg
            return
        
        # 调用工具执行函数
        async for msg in execute_generate_video(
            client=self.client,
            event=event,
            data_dir=self.data_dir,
            config=self.config,
            prompt=prompt,
            duration=duration,
            resolution=resolution
        ):
            yield msg
    
    # ==================== 音乐生成工具 ====================
    
    @filter.llm_tool(name="generate_music")
    async def generate_music(
        self,
        event: AstrMessageEvent,
        prompt: str,
        lyrics: Optional[str] = None,
        is_instrumental: Optional[bool] = None,
        lyrics_optimizer: Optional[bool] = None
    ):
        '''根据描述和歌词生成音乐。

        Args:
            prompt(string): 音乐风格描述，如：轻快的民谣风格、摇滚风格等
            lyrics(string): 歌词内容（可选）
            is_instrumental(boolean): 是否生成纯音乐，默认False
            lyrics_optimizer(boolean): 是否自动生成歌词，默认False
        '''
        # 检查是否启用
        if not self.config.get('enable_music', True):
            async for msg in send_error(event, "音乐生成功能未启用，请在配置中开启"):
                yield msg
            return
        
        # 调用工具执行函数
        async for msg in execute_generate_music(
            client=self.client,
            event=event,
            data_dir=self.data_dir,
            config=self.config,
            prompt=prompt,
            lyrics=lyrics,
            is_instrumental=is_instrumental,
            lyrics_optimizer=lyrics_optimizer
        ):
            yield msg
    
    # ==================== 帮助命令 ====================
    
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
• "基于这张图片 https://example.com/person.jpg 生成一张在海边的照片"
• "生成一个视频：夕阳下的海滩"
• "创作一首音乐：轻快的民谣风格"

配置：
请在 WebUI 中配置 API Key 以使用本插件。
        """
        yield event.plain_result(help_text.strip())
    
    async def terminate(self):
        """插件卸载时的清理工作"""
        logger.info("MiniMax 多模态生成器插件已卸载")
