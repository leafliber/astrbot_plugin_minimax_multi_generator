"""
MiniMax 工具基类
封装文件保存和消息发送逻辑
"""

import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import astrbot.api.message_components as Comp
from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent
from astrbot.api.star import FunctionTool

from ..minimax_client import MiniMaxClient


@dataclass
class MiniMaxTool(FunctionTool):
    """
    MiniMax 工具基类
    
    提供:
    - 文件保存功能
    - 消息发送功能
    - hex 编码转换
    """
    
    client: MiniMaxClient = field(default=None)
    config: dict = field(default_factory=dict)
    data_dir: Path = field(default=None)
    
    def __post_init__(self):
        """初始化后处理"""
        if self.data_dir is None:
            raise ValueError("data_dir 不能为空")
    
    def save_file(self, data: bytes, extension: str, prefix: str = "minimax") -> str:
        """
        保存文件到 data 目录
        
        Args:
            data: 文件二进制数据
            extension: 文件扩展名（不含点）
            prefix: 文件名前缀
            
        Returns:
            文件绝对路径
        """
        # 确保目录存在
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 生成文件名：前缀_时间戳_UUID.扩展名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{prefix}_{timestamp}_{unique_id}.{extension}"
        
        file_path = self.data_dir / filename
        
        # 保存文件
        with open(file_path, 'wb') as f:
            f.write(data)
        
        logger.info(f"文件已保存: {file_path}")
        return str(file_path)
    
    def hex_to_bytes(self, hex_string: str) -> bytes:
        """
        将 hex 编码的字符串转换为 bytes
        
        Args:
            hex_string: hex 编码的字符串
            
        Returns:
            字节数据
        """
        try:
            return bytes.fromhex(hex_string)
        except ValueError as e:
            logger.error(f"hex 解码失败: {e}")
            raise ValueError(f"无效的 hex 编码: {e}")
    
    async def send_image(self, event: AstrMessageEvent, file_path: str):
        """
        发送图片消息
        
        Args:
            event: 消息事件
            file_path: 图片文件路径
        """
        chain = [Comp.Image.fromFileSystem(file_path)]
        yield event.chain_result(chain)
    
    async def send_video(self, event: AstrMessageEvent, file_path: str):
        """
        发送视频消息
        
        Args:
            event: 消息事件
            file_path: 视频文件路径
        """
        chain = [Comp.Video.fromFileSystem(file_path)]
        yield event.chain_result(chain)
    
    async def send_file(
        self, 
        event: AstrMessageEvent, 
        file_path: str, 
        filename: Optional[str] = None
    ):
        """
        发送文件消息
        
        Args:
            event: 消息事件
            file_path: 文件路径
            filename: 显示的文件名（可选）
        """
        if filename is None:
            filename = os.path.basename(file_path)
        
        chain = [Comp.File(file=file_path, name=filename)]
        yield event.chain_result(chain)
    
    async def send_text(self, event: AstrMessageEvent, text: str):
        """
        发送文本消息
        
        Args:
            event: 消息事件
            text: 文本内容
        """
        yield event.plain_result(text)
    
    async def send_error(self, event: AstrMessageEvent, error_message: str):
        """
        发送错误消息
        
        Args:
            event: 消息事件
            error_message: 错误信息
        """
        logger.error(f"工具执行错误: {error_message}")
        yield event.plain_result(f"❌ 错误: {error_message}")
