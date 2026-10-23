# Book Share Video · 图书分享视频 Skill

把一本书的观点、读书笔记或参考文案，制作成风格多样、可以本地修改与导出的读书分享动画。适用于 Codex 中的单条或批量图书短视频创作。

本技能整理了从出处核对、原创解读、视觉分镜、动画绘制、字幕与音乐到 MP4 导出的完整方法，使用 **Concept Reel Canvas + Playwright + FFmpeg**。生成器负责建立工程骨架；每条视频的文案、主体、画面和动作仍需由创作者或智能体按书籍内容完成。

## 默认成片规格

| 项目 | 默认值 |
| --- | --- |
| 时长与画幅 | 约 60 秒，1080×1920，9:16 竖屏 |
| 帧率 | 30fps |
| 声音 | 无旁白，仅用户提供的背景音乐 |
| 音乐处理 | 首尾各 1.5 秒淡入淡出 |
| 画面文字 | 保留主标题、书名作者、主要文案与字幕；不加装饰性页眉、来源页脚和“生活示意”等说明性小字 |
| 风格 | 每本书围绕内容重新设计，对照近作避免重复 |

用户可另行指定时长、横屏、配音或复用某种风格。书籍来源与原创解读的边界写在工程文档中。

## 风格怎样保持多样

多样性需要落实到 **主体与隐喻、材质、空间构图、动作、文字角色、运镜与转场**。仅换配色、字体或增加颗粒，不算新的视觉体系。通常至少改变两个核心维度，并在 `style.json` 写明与最接近旧作的实际差异。

技能提供 15 套历史视觉摘要作为比较材料：植物生活插画、夜航剪影、剧场叙事、纸页世界、明亮手绘几何、纸层生活照顾、现代几何拼贴、日程手账、水墨水彩自然长卷、木刻篆刻、旧胶片乡村剪影、机械迷宫、玻璃与流动光带、日晷建筑光影、织物刺绣。

它们是参考，不是只能轮换的模板，也不表示生成器已自动实现全部效果。新作品可继续探索其他视觉体系。每条视频先制作最能体现风格且最难解释的一镜，查看真实画面和动作后再完成全片。详见 [风格多样性](references/style-diversity.md) 与 [系列风格摘要](references/series-history.json)。

## 安装与调用

### 安装技能

需要 Git 和可使用技能的 Codex。任选一个位置克隆完整仓库，不要只复制 `SKILL.md`：

```bash
# 当前用户的多个项目可用
mkdir -p ~/.agents/skills
git clone https://github.com/songdianda/book-share-video.git ~/.agents/skills/book-share-video
```

也可在目标项目中克隆到 `.agents/skills/book-share-video/`，仅供该项目使用。已有同名安装时先检查和备份，不覆盖自定义内容，也不要重复安装。技能未出现时可重启 Codex，或提供 `SKILL.md` 的绝对路径。技能安装和渲染运行环境是两件事。

### 在 Codex 聊天里调用

```text
使用 $book-share-video，以《书名》（作者）制作一条约60秒竖屏图书分享视频。
无配音，使用我提供的背景音乐，首尾各1.5秒淡入淡出。
风格与近作不同，不加说明性小字。
```

继续系列时提供旧项目目录，便于对照各片的 `style.json`。没有可访问历史时，只能与当前项目和技能种子历史比较。`$book-share-video` 是聊天中的技能提及，不是 Shell 命令。

## 准备本地运行环境

需要 **Python 3.12+、FFmpeg 与 ffprobe、Chrome 或 Playwright Chromium**；JavaScript 语法检查还需要 Node.js。Python 依赖包括 Playwright、NumPy、SciPy、Pillow，按仓库锁文件安装到本地虚拟环境。先复用已有环境，不自动安装全局依赖或修改系统配置。

```bash
cd ~/.agents/skills/book-share-video
python3.12 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r requirements.lock
.venv/bin/python engine/get_fonts.py
.venv/bin/python engine/get_fonts.py --check
.venv/bin/python scripts/check_env.py --browser chrome --json
```

已有 Chrome 可用 `--browser chrome`。没有可用浏览器时，可单独运行 `.venv/bin/python -m playwright install chromium` 下载浏览器，随后使用渲染器默认 Chromium；不需要为此执行系统级 `--with-deps`。公开仓库保留其余字体与全部 OFL 许可证；受本次 GitHub 网页单文件 25 MB 上传限制，未收录较大的 `engine/fonts/NotoSerifSC-VF.ttf`。首次安装须先运行上面的 `engine/get_fonts.py`，从官方 Google Fonts 补齐缺失字体，再运行字体及环境检查。该脚本只下载缺失或无效的字体与许可证，不重复下载有效文件。详情见 [复用说明](references/reuse.md)。`LOCAL-RUNTIME.md` 是环境记录模板，不代表当前机器已经通过检查。

本仓库不要求图像生成、配音或云视频 API；默认动画在本地用 Canvas 绘制。来源查询可能需要联网，首次安装依赖或补齐字体与浏览器也需要网络。

## 完整制作流程

1. **核对书籍与观点**：优先作者或出版社原文、官方试读；记录实际阅读范围、版本、链接和核验日期。区分原句、转述、原创解读和生活例子，不把网传文案冒充原文。
2. **选定视觉方案**：围绕一个清楚的观点选择主体和动作，比较历史，在 `style.json` 中记录材质、构图、动作和内容关系。
3. **整理时间线**：60 秒可从约 200–280 字、6–9 镜起步，按实际阅读时间调整，不为凑字数或镜头数牺牲节奏。
4. **创建新工程**：用 `scripts/new_book.py` 从时间线创建全新版本目录；目标目录已存在会拒绝覆盖。源码与成片保存在用户工作区。
5. **完成动画与音乐**：按分镜重写 `film.js`，确保对象可辨认、动作有起点与落点；字幕从统一时间线派生。处理用户音乐，记录过滤链和 PCM 哈希，已淡入淡出的音源不重复处理。
6. **检查真实画面**：检查 JS 语法，打开覆盖每镜与关键转场的实际关键帧，运行 `--det` 验证乱序 seek 的确定性；发现问题后复核受影响部分。
7. **渲染交付**：导出画面、合入音乐，检查全片解码、时长、分辨率、帧率、字幕一致性，填写真实的 `validation.json`，交付 MP4 与工程。

关键命令如下；将示例绝对路径换成实际路径，在已准备好的 Python 环境下执行：

```bash
python scripts/new_book.py /absolute/workspace/videos/book-slug-v1 --timeline /absolute/workspace/drafts/timeline.json
node --check /absolute/workspace/videos/book-slug-v1/film.js
python engine/render.py /absolute/workspace/videos/book-slug-v1 --browser chrome --sheet 2 8 15 24 32 40 49 58
python engine/render.py /absolute/workspace/videos/book-slug-v1 --browser chrome --det
python engine/render.py /absolute/workspace/videos/book-slug-v1 --serve --port 0
python engine/render.py /absolute/workspace/videos/book-slug-v1 --browser chrome --jobs 2
```

以上关键帧时刻只是示例，需要覆盖本片真实分镜。通过本地服务打开预览 URL 并加 `?preview` 可随音乐预览；不要直接双击 HTML。完整时间线格式、音乐与最终合片命令见 [制作与验证手册](references/production-workflow.md)。

## 工程与交付文件

| 文件 | 内容 |
| --- | --- |
| `renders/final.mp4` | 最终可播放成片 |
| `index.html`、`film.js`、`visual-utils.js`、`preview.js` | 可继续修改的动画与预览源码 |
| `timeline.json`、`timeline.js`、`segments.json`、`captions.srt` | 统一时间线及字幕派生文件 |
| `sources.md`、`storyboard.md`、`style.json` | 来源、分镜、视觉决策与风格比较 |
| `audio/score.wav`、`audio/music.json` | 已处理音乐及其来源与处理记录 |
| `validation.json` | 实际完成的检查与未检查项 |

`new_book.py` 不会自动提供这些最终成果：音乐、事实核验、完整分镜和成片需要在制作流程中完成。新增 Python 工具改动可运行 `python -m unittest discover -s tests -v`；技能本身不保证任何新视频已经通过验证。

## 验证边界与使用范围

- 关键帧视觉检查、确定性检查、完整技术解码、完整人工播放和全程试听分别记录；技术解码通过不代表人工看完或听完。
- 不伪造书中引文、页码或“已阅读全书”的声明；只有公开试读时如实说明范围，不制作无依据的医疗或心理疗效承诺。
- 默认不发布视频、不修改系统配置、Hooks、密钥或用户旧工程。人物按视角绘制完整五官与肢体；Canvas 材质近似不冒充真实三维或布料模拟。
- 仓库不包含私人音乐、完整书稿、个人历史成片、凭据、虚拟环境或某台机器的绝对路径。背景音乐和受保护书籍材料由使用者另行提供，并确认相应使用与公开传播权限。

## 目录与进一步说明

`SKILL.md` 为技能入口；`assets/portrait/` 为竖屏骨架；`scripts/` 为新建、环境检查与音频工具；`engine/` 为 Canvas 引擎、渲染器与字体；`references/` 为内容、风格和复用说明；`examples/` 为继承学习示例；`tests/` 为工具测试。

## 来源与许可

- 本版本基于 [Jogzh/concept-reel](https://github.com/Jogzh/concept-reel)，继承自 Dave-cc 的 `vibe-knowledge-film`，保留 Canvas API、渲染工具及来源说明。代码适用 [MIT 许可证](LICENSE)；新增修改不替代上游署名。
- 视觉风格分类参考 [Vincentwei1021/mg-styles-15](https://github.com/Vincentwei1021/mg-styles-15)，本仓库重新编写适配方法，不复制其品牌、剧情或第三方素材。
- 字体来自 Google Fonts：Noto Serif SC、Noto Sans SC、Cormorant Garamond、Lora、JetBrains Mono、Courier Prime，各自适用 SIL Open Font License 1.1，详见 `engine/fonts/OFL-*.txt`。
- MIT 不覆盖被上游排除的第三方参考片内容、字体、书籍和音乐。排除的复刻工程未随本版本提供，其他示例的来源边界见 [examples/README.md](examples/README.md)。完整说明见 [NOTICE.md](NOTICE.md)。
