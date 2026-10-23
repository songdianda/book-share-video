# 本地运行环境

此便携包没有绑定某台电脑的Python、音乐或项目路径。先检查已有Python 3.12+、FFmpeg/ffprobe与Chrome或Playwright Chromium；优先复用已有环境，缺失时参照 references/reuse.md，在用户许可范围内准备本地虚拟环境。

- Python：由当前机器实际探测后记录。
- 浏览器：按实际可用环境选择 --browser chrome 或默认Chromium。
- 背景音乐：由用户单独提供，或读取任务中明确选定且实际存在的音源。此包不含私人音乐。
- 历史系列：references/series-history.json 是种子历史；新作品在当前工程 style.json 中记录。跨项目继续系列时读取用户指定的系列目录。
- 视频工程：放在用户当前工作区的新版本目录，不写到技能的 engine/ 或覆盖旧工程。

不要把说明中的示例路径当成已验证路径，不自动改Shell、Hooks、密钥或系统配置。
