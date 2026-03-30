"""
MiniMax API 客户端
封装所有 MiniMax 多模态 API 调用
"""

import aiohttp
import asyncio
from typing import Optional, Dict, Any, List
from astrbot.api import logger


class MiniMaxClient:
    """MiniMax API 客户端"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.minimaxi.com"):
        """
        初始化客户端
        
        Args:
            api_key: MiniMax API Key
            base_url: API 基础地址（默认国内站）
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def _request(
        self, 
        method: str, 
        endpoint: str, 
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        return_binary: bool = False
    ) -> Any:
        """
        发送 HTTP 请求
        
        Args:
            method: HTTP 方法（GET, POST 等）
            endpoint: API 端点
            json_data: JSON 请求体
            params: URL 参数
            return_binary: 是否返回二进制数据
            
        Returns:
            API 响应数据
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method, 
                    url, 
                    headers=self.headers,
                    json=json_data,
                    params=params
                ) as response:
                    if return_binary:
                        if response.status == 200:
                            return await response.read()
                        else:
                            error_text = await response.text()
                            raise Exception(f"API 请求失败: {response.status} - {error_text}")
                    else:
                        result = await response.json()
                        
                        # 检查响应状态
                        if 'base_resp' in result:
                            status_code = result['base_resp'].get('status_code', -1)
                            status_msg = result['base_resp'].get('status_msg', 'Unknown error')
                            if status_code != 0:
                                raise Exception(f"API 错误: {status_msg} (code: {status_code})")
                        
                        return result
                        
        except aiohttp.ClientError as e:
            logger.error(f"网络请求错误: {e}")
            raise Exception(f"网络请求失败: {e}")
        except Exception as e:
            logger.error(f"API 调用异常: {e}")
            raise
    
    # ==================== 语音合成 API ====================
    
    async def text_to_speech(
        self,
        text: str,
        model: str = "speech-2.8-hd",
        voice_id: str = "male-qn-qingse",
        speed: float = 1.0,
        vol: float = 1.0,
        pitch: int = 0,
        emotion: Optional[str] = None,
        audio_format: str = "mp3",
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        文本转语音
        
        Args:
            text: 要转换的文本
            model: 语音合成模型
            voice_id: 音色 ID
            speed: 语速（0.5-2.0）
            vol: 音量（0.1-10.0）
            pitch: 音调（-12 到 12）
            emotion: 情感（可选）
            audio_format: 音频格式（mp3, pcm, flac, wav）
            stream: 是否流式输出
            
        Returns:
            包含音频数据的响应
        """
        payload = {
            "model": model,
            "text": text,
            "stream": stream,
            "voice_setting": {
                "voice_id": voice_id,
                "speed": speed,
                "vol": vol,
                "pitch": pitch,
            },
            "audio_setting": {
                "format": audio_format,
            }
        }
        
        if emotion:
            payload["voice_setting"]["emotion"] = emotion
        
        # 添加其他可选参数
        payload.update(kwargs)
        
        return await self._request("POST", "/v1/t2a_v2", json_data=payload)
    
    # ==================== 图像生成 API ====================
    
    async def generate_image(
        self,
        prompt: str,
        model: str = "image-01",
        aspect_ratio: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        n: int = 1,
        response_format: str = "url",
        seed: Optional[int] = None,
        prompt_optimizer: bool = False,
        aigc_watermark: bool = False,
        subject_reference: Optional[List[Dict]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        图像生成（文生图或图生图）
        
        Args:
            prompt: 图像描述
            model: 图像生成模型
            aspect_ratio: 宽高比
            width: 宽度（像素）
            height: 高度（像素）
            n: 生成数量
            response_format: 返回格式（url 或 base64）
            seed: 随机种子
            prompt_optimizer: 是否优化 prompt
            aigc_watermark: 是否添加水印
            subject_reference: 主体参考（用于图生图）
            
        Returns:
            包含图像 URL 或 base64 的响应
        """
        payload = {
            "model": model,
            "prompt": prompt,
            "n": n,
            "response_format": response_format,
            "prompt_optimizer": prompt_optimizer,
            "aigc_watermark": aigc_watermark,
        }
        
        if aspect_ratio:
            payload["aspect_ratio"] = aspect_ratio
        
        if width and height:
            payload["width"] = width
            payload["height"] = height
        
        if seed is not None:
            payload["seed"] = seed
        
        if subject_reference:
            payload["subject_reference"] = subject_reference
        
        # 添加其他可选参数
        payload.update(kwargs)
        
        return await self._request("POST", "/v1/image_generation", json_data=payload)
    
    async def text_to_image(
        self,
        prompt: str,
        model: str = "image-01",
        aspect_ratio: Optional[str] = None,
        n: int = 1,
        **kwargs
    ) -> Dict[str, Any]:
        """
        文生图便捷方法
        
        Args:
            prompt: 图像描述
            model: 图像生成模型
            aspect_ratio: 宽高比
            n: 生成数量
            
        Returns:
            包含图像 URL 或 base64 的响应
        """
        return await self.generate_image(
            prompt=prompt,
            model=model,
            aspect_ratio=aspect_ratio,
            n=n,
            **kwargs
        )
    
    async def image_to_image(
        self,
        prompt: str,
        reference_image_url: str,
        model: str = "image-01",
        aspect_ratio: Optional[str] = None,
        n: int = 1,
        **kwargs
    ) -> Dict[str, Any]:
        """
        图生图便捷方法
        
        Args:
            prompt: 图像描述
            reference_image_url: 参考图片 URL
            model: 图像生成模型
            aspect_ratio: 宽高比
            n: 生成数量
            
        Returns:
            包含图像 URL 或 base64 的响应
        """
        subject_reference = [{
            "type": "character",
            "image_file": reference_image_url
        }]
        
        return await self.generate_image(
            prompt=prompt,
            model=model,
            aspect_ratio=aspect_ratio,
            n=n,
            subject_reference=subject_reference,
            **kwargs
        )
    
    # ==================== 视频生成 API ====================
    
    async def create_video_task(
        self,
        prompt: str,
        model: str = "MiniMax-Hailuo-2.3",
        duration: int = 6,
        resolution: str = "720P",
        prompt_optimizer: bool = True,
        aigc_watermark: bool = False,
        **kwargs
    ) -> str:
        """
        创建视频生成任务
        
        Args:
            prompt: 视频描述
            model: 视频生成模型
            duration: 视频时长（秒）
            resolution: 分辨率
            prompt_optimizer: 是否优化 prompt
            aigc_watermark: 是否添加水印
            
        Returns:
            任务 ID
        """
        payload = {
            "model": model,
            "prompt": prompt,
            "duration": duration,
            "resolution": resolution,
            "prompt_optimizer": prompt_optimizer,
            "aigc_watermark": aigc_watermark,
        }
        
        # 添加其他可选参数
        payload.update(kwargs)
        
        result = await self._request("POST", "/v1/video_generation", json_data=payload)
        return result.get("task_id")
    
    async def query_video_task(self, task_id: str) -> Dict[str, Any]:
        """
        查询视频生成任务状态
        
        Args:
            task_id: 任务 ID
            
        Returns:
            任务状态信息
        """
        params = {"task_id": task_id}
        return await self._request("GET", "/v1/video_generation/query", params=params)
    
    async def download_video(self, file_id: str) -> bytes:
        """
        下载生成的视频（download_file 的别名）
        
        Args:
            file_id: 文件 ID
            
        Returns:
            视频二进制数据
        """
        return await self.download_file(file_id)
    
    async def download_file(self, file_id: str) -> bytes:
        """
        下载文件（用于下载生成的视频）
        
        Args:
            file_id: 文件 ID
            
        Returns:
            文件二进制数据
        """
        endpoint = f"/v1/files/{file_id}"
        return await self._request("GET", endpoint, return_binary=True)
    
    # ==================== 音乐生成 API ====================
    
    async def generate_music(
        self,
        prompt: str,
        lyrics: Optional[str] = None,
        model: str = "music-2.5+",
        is_instrumental: bool = False,
        lyrics_optimizer: bool = False,
        audio_format: str = "mp3",
        **kwargs
    ) -> Dict[str, Any]:
        """
        音乐生成
        
        Args:
            prompt: 音乐描述
            lyrics: 歌词
            model: 音乐生成模型
            is_instrumental: 是否生成纯音乐
            lyrics_optimizer: 是否自动生成歌词
            audio_format: 音频格式
            
        Returns:
            包含音频数据的响应
        """
        payload = {
            "model": model,
            "prompt": prompt,
            "is_instrumental": is_instrumental,
            "lyrics_optimizer": lyrics_optimizer,
        }
        
        if lyrics:
            payload["lyrics"] = lyrics
        
        if "audio_setting" not in kwargs:
            payload["audio_setting"] = {
                "format": audio_format
            }
        
        # 添加其他可选参数
        payload.update(kwargs)
        
        return await self._request("POST", "/v1/music_generation", json_data=payload)
