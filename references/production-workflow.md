# 制作与验证手册

## 路径与已有环境

`SKILL_ROOT` 表示当前读取的技能目录，不是当前项目；`PROJECT` 是用户工作区中的全新版本目录。本机 Python 等路径见技能目录的 `LOCAL-RUNTIME.md`。先用已有环境，不安装全局依赖。换机器时按 [复用说明](reuse.md) 准备本地环境。

下面命令的示例路径须替换成真实绝对路径。渲染器把技能的 `engine/` 挂载到本地预览源的 `/engine/`；工程不用复制引擎或字体。

## 统一时间线与新建工程

先在工作区写一份本片时间线 JSON，再运行：

```bash
python /path/to/book-share-video/scripts/new_book.py /absolute/workspace/videos/book-slug-v1 --timeline /absolute/workspace/drafts/book-slug-timeline.json
```

默认60秒、30fps、1080×1920，目标目录存在就拒绝，不带覆盖开关。可用 `--width` / `--height` 指定其他偶数画幅；改变画幅后重新设计场景，不能只缩放主体和字幕。

最小输入结构（完整项目自行补充真实字幕与全部分镜）：

```json
{
  "title": "书名",
  "author": "作者",
  "end": 60,
  "fps": 30,
  "voice": "none",
  "sections": [{"id":0,"a":0,"b":60,"title":"本片的叙事任务"}],
  "segments": [{"a":0.6,"b":5.6,"text":"已核对并按本片创作的开场文案。","kind":"interpretation"}]
}
```

新建器检查章节连续覆盖时长、字幕不重叠且在片内、归因类型等；生成 `timeline.json`、`timeline.js`、`segments.json`、`captions.srt`、HTML、JS、预览控制、配置及文档骨架。它不审核事实、不代写原创画面，也不判定最终视觉风格。

填写 `sources.md`、`storyboard.md`、`style.json` 后，按内容重写 `film.js`。`visual-utils.js` 提供 Path2D、测量缩字、中文换行和稳定字幕；这些工具可复用，上一片固定对象和8镜结构不必复用。现有 `new_film.py` 保持旧横屏接口，不能把它当作新的系列默认生成器。

修改字幕时以 `timeline.json` 为唯一来源同步派生文件，再核对 SRT；派生文件若含用户手动改动，先比较差异，避免覆盖。不要重新运行新建器覆盖工程。

## 背景音乐

已有本系列已处理的60秒 `audio/score.wav` 时，可在确认时长和处理记录后复制到新工程，比较PCM哈希证明同源。不要重复淡入淡出。使用原音源时，60秒默认命令为：

```bash
ffmpeg -v error -n -i /absolute/user-music.m4a -vn -af 'atrim=0:60,asetpts=PTS-STARTPTS,afade=t=in:st=0:d=1.5,afade=t=out:st=58.5:d=1.5' -ar 48000 -ac 2 -c:a pcm_s16le /absolute/project/audio/score.wav
```

原音乐短于目标长度，先决定自然循环或调整段落，再淡出；不能默认接受尾部无音乐。目标长度改变时同步调整截取长度和淡出开始时间。记录原音源、实际过滤链、输出时长与PCM哈希到项目 `audio/music.json`。输出已存在时保留原文件，用新版本路径。

无配音模式不用程序合成的替代配乐，也不额外叠加音效，除非用户要求。

## 画面验证与预览

```bash
node --check /absolute/project/film.js
node --check /absolute/project/visual-utils.js
node --check /absolute/project/timeline.js
python /path/to/book-share-video/engine/render.py /absolute/project --browser chrome --sheet 2 8 15 19 24 32 40 49 56 58
python /path/to/book-share-video/engine/render.py /absolute/project --browser chrome --det
python /path/to/book-share-video/engine/render.py /absolute/project --serve --port 0
```

示例时刻用于常见60秒分镜，须改成真正覆盖本片每镜、关键动作结束和转场的时刻。实际打开 `review/sheet.jpg`，必要时用 `--stills` 或 `--motion START END COUNT` 看变化。只生成拼图没有打开查看不能算视觉验收。

预览服务打印URL；加 `?preview` 用音频控件的 `currentTime` 驱动画面。`?play` 是引擎画面播放，不等于带音乐同步预览。不要直接双击HTML。浏览器未安装时先报告缺失；普通沙箱无法绑定本地端口或启动Chrome时请求所需执行权限，不把环境失败归因于文案或浏览器版本。

## 导出与合片

```bash
python /path/to/book-share-video/engine/render.py /absolute/project --browser chrome --jobs 2
ffmpeg -v error -n -i /absolute/project/renders/raw.mp4 -i /absolute/project/audio/score.wav -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 192k -ar 48000 -t 60 -movflags +faststart /absolute/project/renders/final.mp4
ffmpeg -v error -xerror -i /absolute/project/renders/final.mp4 -f null -
ffprobe -v error -show_entries format=duration,size:stream=codec_type,codec_name,width,height,r_frame_rate,nb_frames,sample_rate,channels -of json /absolute/project/renders/final.mp4
```

已有 `raw.mp4` / `final.mp4` 时保留旧版或改用新工程。并行渲染默认2个worker；跟随已有进程等待结束，不因一次观察超时重复启动。上述 `-t 60` 是本系列默认，实际时长变化时同步修改，不能用截断掩盖镜头与音乐长度不一致。

## 检查记录

`validation.json` 至少记录：

- 书名/作者、时长、画幅、帧率/帧数；默认应为60秒、1080×1920、30fps、1800帧，AAC双声道48kHz。
- `timeline.json` 与其他字幕文件的一致性；扣除字显/淡入淡出后的阅读速率。普通中文约5–6字/秒可作检查线索，复杂内容更慢，不能仅凭字数证明易读。
- JS语法、`--det`和全片解码的真实输出；实际看过的关键帧时刻及发现/修复的问题。
- 最终文件及其源码SHA256，音乐过滤链和PCM哈希；批量片确认同源音乐。
- `manual_full_playback`、`manual_full_listening`分别填true/false，不把技术解码当作人工试听或全程观看。
- `style.json` 的实际视觉体系与比较对象。工程交付后可标为`delivered`，用户明确认可才标`approved`。

未做的项写 `not_checked`，不提前填 `passed`。最后链接当前真实成片和工程，说明必要的验证边界，不报告未发生的平台验证或公开发布。
