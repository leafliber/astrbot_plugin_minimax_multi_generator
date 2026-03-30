# MiniMax 多模态生成器

一个 AstrBot 插件，集成 MiniMax 多模态 API 功能，支持语音合成、图像生成、视频生成和音乐生成。

## 功能特性

### 🎙️ 语音合成
- 文本转语音，支持多种音色
- 可调节语速、音量、音调
- 支持情感表达
- 支持流式输出

### 🖼️ 图像生成
- **文生图**：根据文本描述生成图片
- **图生图**：基于参考图生成保持人物形象一致性的新图片
- 支持多种宽高比和分辨率
- 可选择不同模型和风格

### 🎬 视频生成
- 文生视频，支持多种分辨率
- 可配置视频时长（6s/10s）
- 异步生成，自动轮询任务状态
- 支持运镜控制指令

### 🎵 音乐生成
- 根据描述和歌词生成音乐
- 支持纯音乐模式
- 可自动生成歌词
- 支持多种音频格式

## 安装

1. 将插件放置在 `AstrBot/data/plugins/` 目录下
2. 在 AstrBot WebUI 中配置 API Key
3. 根据需要启用或禁用各功能

## 配置

### 必需配置

- `api_key`: MiniMax API Key（在 [MiniMax 开放平台](https://platform.minimaxi.com) 获取）

### 可选配置

- `base_url`: API 地址（默认国内站 `https://api.minimaxi.com`，可选国际站 `https://api.minimax.io`）
- `enable_speech`: 是否启用语音合成（默认 true）
- `enable_image`: 是否启用图像生成（默认 true）
- `enable_video`: 是否启用视频生成（默认 true）
- `enable_music`: 是否启用音乐生成（默认 true）

### 各功能详细配置

请参考 WebUI 中的配置说明。

## 可用工具

插件提供以下 LLM 工具：

### 🎙️ text_to_speech - 语音合成
将文本转换为语音。

**参数：**
- `text` (必需): 要转换的文本
- `voice_id` (可选): 音色ID，默认清新男声
- `speed` (可选): 语速，范围0.5-2.0
- `emotion` (可选): 情感表达

### 🖼️ text_to_image - 文生图
根据文本描述生成图片。

**参数：**
- `prompt` (必需): 图片描述
- `aspect_ratio` (可选): 宽高比（1:1, 16:9, 9:16等）
- `n` (可选): 生成数量，1-9张

### 🖼️ image_to_image - 图生图
基于参考图片生成新图片，保持人物一致性。

**参数：**
- `prompt` (必需): 图片描述
- `reference_image_url` (必需): 参考图片URL
- `aspect_ratio` (可选): 宽高比
- `n` (可选): 生成数量

### 🎬 generate_video - 视频生成
根据文本描述生成视频。

**参数：**
- `prompt` (必需): 视频描述
- `duration` (可选): 时长（6或10秒）
- `resolution` (可选): 分辨率（720P, 768P, 1080P）

### 🎵 generate_music - 音乐生成
根据描述和歌词生成音乐。

**参数：**
- `prompt` (必需): 音乐风格描述
- `lyrics` (可选): 歌词
- `is_instrumental` (可选): 是否纯音乐
- `lyrics_optimizer` (可选): 是否自动生成歌词

## 使用方法

插件会自动注册为 LLM 工具，用户可以通过对话方式调用：

- "用语音合成功能说：你好世界"
- "生成一张图片：一只可爱的猫咪"
- "基于这张图片 https://example.com/person.jpg 生成一张在海边的照片"
- "生成一个视频：夕阳下的海滩"
- "创作一首音乐：轻快的民谣风格"

## 支持的平台

- OneBot V11 (QQ)
- Telegram
- Discord
- 其他 AstrBot 支持的平台

## 注意事项

1. **API Key**: 使用本插件需要 MiniMax API Key，可在 [MiniMax 开放平台](https://platform.minimaxi.com) 获取
2. **费用**: 各功能可能产生费用，请查看 MiniMax 官方定价
3. **视频生成**: 需要较长时间（通常1-3分钟），请耐心等待
4. **文件存储**: 生成的文件会存储在插件 data 目录中，建议定期清理
5. **图生图**: 需要提供可访问的图片 URL，确保图片包含清晰的人物主体
6. **平台兼容**: 使用 AstrBot 原生消息组件，自动适配所有支持的平台

## 技术实现

- **API 认证**: 使用 Bearer Token 认证，无需 Group ID
- **异步处理**: 所有 API 调用使用 aiohttp 异步执行
- **文件管理**: 自动保存生成文件，使用时间戳+UUID命名避免冲突
- **错误处理**: 完善的异常捕获和用户友好提示
- **消息发送**: 使用 AstrBot 原生消息组件，支持图片、视频、文件等多媒体类型

## 文件结构

```
astrbot_plugin_minimax_multi_generator/
├── main.py                 # 主插件类
├── metadata.yaml           # 插件元数据
├── _conf_schema.json       # 配置 Schema
├── requirements.txt        # Python 依赖
├── README.md              # 说明文档
├── minimax_client.py      # API 客户端
└── tools/                 # 工具模块
    ├── __init__.py
    ├── base.py            # 工具基类
    ├── speech_synthesis.py
    ├── text_to_image.py
    ├── image_to_image.py
    ├── video_generation.py
    └── music_generation.py
```

## 许可证

MIT License

## 反馈与支持

如有问题或建议，请提交 Issue 到项目仓库。
