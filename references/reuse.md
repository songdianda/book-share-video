# 调用与跨项目复用

## 已安装的这台机器

技能名称是 `book-share-video`。在 Codex 的聊天输入框里写：

```text
使用 $book-share-video，以《书名》（作者）制作一条图书分享视频。
沿用原背景音乐，风格与近作不同。
```

会采用本系列默认规格；也可以明确指定时长、画幅、配音或风格。`$book-share-video` 是技能提及，不是普通 Shell 命令。自然语言明确要求“使用 book-share-video”也能提供调用意图。

当前安装位置及Python路径见 `LOCAL-RUNTIME.md`。换一个项目时无需再复制这套引擎；让Codex读取已安装技能，将视频源码和成片写在新项目的 `videos/<book-slug>-v1/` 等新目录即可。若菜单没有显示升级内容，可重启Codex或直接提供 `SKILL.md` 绝对路径。

## 复制到另一台机器或只给一个项目使用

克隆本公开仓库，或下载仓库 ZIP 后解压并将目录命名为 `book-share-video/`，里面应有 `SKILL.md`、`engine/`、`scripts/`、`assets/`、`references/` 等。不要只复制 `SKILL.md`。

- 只用于某项目：将整个目录放到该项目的 `.agents/skills/book-share-video/`。
- 用于当前用户的多个项目：放到 `~/.agents/skills/book-share-video/`。
- 本机已有同名旧安装时先备份并检查位置，避免同时安装两个同名技能。不要覆盖用户自定义修改。

这些本地发现位置与技能调用方式参照 [OpenAI 官方技能文档](https://learn.chatgpt.com/docs/build-skills)，核对日期2026-10-23。已有环境中识别的旧 `~/.codex/skills/book-share-video` 安装可继续使用，不为本次升级制造重复安装。

公开仓库包含引擎、工具、模板及其余开源字体与全部字体许可证；受本次 GitHub 网页单文件 25 MB 上传限制，未收录较大的 `engine/fonts/NotoSerifSC-VF.ttf`，首次安装须从官方 Google Fonts 补齐。仓库不包含私人音乐、书稿、历史MP4、`.venv`、密钥或本机安装路径。原音乐需要单独提供。复制到另一台机器后不能声称原音乐已自动可用。

## 准备运行环境

先检查已有Python（本包锁定依赖需要3.12+，本机使用3.12验证）、FFmpeg/ffprobe、Chrome或Playwright Chromium。技能文件本身不等于已经安装全部运行依赖。已有工具可直接复用；缺失时先说明所需操作，尤其全局安装或系统配置变更须获授权。

Python依赖可在该技能目录或工具目录的本地虚拟环境中按锁文件安装：

```bash
python3 -m venv /absolute/tool-runtime/.venv
/absolute/tool-runtime/.venv/bin/python -m pip install --require-hashes -r /absolute/book-share-video/requirements.lock
/absolute/tool-runtime/.venv/bin/python /absolute/book-share-video/engine/get_fonts.py
/absolute/tool-runtime/.venv/bin/python /absolute/book-share-video/engine/get_fonts.py --check
/absolute/tool-runtime/.venv/bin/python /absolute/book-share-video/scripts/check_env.py --browser chrome --json
```

有Chrome时可用`--browser chrome`，不额外下载Chromium；没有可用浏览器且用户同意本地下载时再执行虚拟环境的`python -m playwright install chromium`。不要自动运行系统级包管理器或`--with-deps`改系统。首次使用公开仓库时，先运行上面的 `engine/get_fonts.py` 补齐缺失字体，再做 `--check` 和环境检查。下载源为官方 Google Fonts；脚本会跳过已有效的文件。所有字体齐全后可用 `engine/get_fonts.py --check` 离线校验，此选项不下载文件。

在新环境更新该副本的 `LOCAL-RUNTIME.md`，记录实际Python、浏览器选择、可选音乐路径。不要把旧机器路径复制成新机器已验证配置。

## 系列风格如何延续

技能自带15种已用视觉体系的种子历史；每条新视频还在自己的 `style.json` 记录实际画法、比较对象与差异。跨项目继续一组系列时，给出原系列工程目录或把这些风格摘要汇总到用户指定的共享目录，后续读取它们再选型。

没有共享历史时只能依据可访问的种子和当前项目比较，不能承诺“与所有历史作品绝不重复”。不要为了记历史自动改写已安装技能或用户的其他项目。只记录本次项目，必要时告知本次查阅的历史范围。
