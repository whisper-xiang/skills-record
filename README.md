# Skills Record — 目录库

> 最后更新：2026-06-24 10:28 

收录 **Agent Skill**、**GitHub 开源项目** 与 **偶然想法**。条目来自仓库内 `skills/` 目录，或 GitHub Issues（标签 `skill-record`）。

共 **7** 条：Skill 4 · GitHub 项目 2 · 想法 1

## Agent Skill

<table>
<colgroup>
<col width="18%"><col width="8%"><col width="12%"><col width="8%"><col width="54%">
</colgroup>
<thead>
<tr><th>名称</th><th>Stars</th><th>分类</th><th>状态</th><th>简介</th></tr>
</thead>
<tbody>
<tr><td><a href="#thesis-tutor">Thesis Tutor</a></td><td>0</td><td>Cursor Skill</td><td>收藏</td><td>基于本地 Markdown 知识库的多语言论文全流程辅导 Skill，本地零成本引擎 + De…</td></tr>
<tr><td><a href="#nature-skills">nature-skills</a></td><td>22.3k</td><td>其他</td><td>收藏</td><td>Nature/CNS 风格科研技能包，含润色、绘图、reader、PPT、审稿、引用等 11 …</td></tr>
<tr><td><a href="#academic-research-skills">Academic Research Skills (ARS)</a></td><td>33.7k</td><td>Claude Skill</td><td>收藏</td><td>Claude Code 学术研究全流程技能套件，覆盖研究、写作、审稿与 10 阶段 pipel…</td></tr>
<tr><td><a href="#cnki">CNKI Research Toolkit</a></td><td>—</td><td>Cursor Skill</td><td>—</td><td>面向 Cursor / Claude Agent 的 中国知网（CNKI）文献研究 Skill…</td></tr>
</tbody>
</table>

## GitHub 项目

<table>
<colgroup>
<col width="18%"><col width="8%"><col width="12%"><col width="8%"><col width="54%">
</colgroup>
<thead>
<tr><th>名称</th><th>Stars</th><th>分类</th><th>状态</th><th>简介</th></tr>
</thead>
<tbody>
<tr><td><a href="#wiltodelta-remove-ai-watermarks">remove-ai-watermarks</a></td><td>3.5k</td><td>GitHub 项目</td><td>收藏</td><td>CLI/Python 库：去除 AI 生成图片的可见/不可见水印（Gemini 星标、Synt…</td></tr>
<tr><td><a href="#ranfeng-clipsketch-ai">ClipSketch AI</a></td><td>1.8k</td><td>GitHub 项目</td><td>收藏</td><td>AI 视频创作工作台：解析 B 站/小红书链接，帧级标记精彩瞬间，Gemini 一键生成手绘故…</td></tr>
</tbody>
</table>

## 想法

<table>
<colgroup>
<col width="20%"><col width="14%"><col width="10%"><col width="56%">
</colgroup>
<thead>
<tr><th>名称</th><th>分类</th><th>状态</th><th>简介</th></tr>
</thead>
<tbody>
<tr><td><a href="#idea-儿童动画插入工艺广告">儿童动画插入工艺广告</a></td><td>想法</td><td>灵感</td><td>在儿童动画内容中自然植入手工艺/非遗工艺类广告或品牌露出。</td></tr>
</tbody>
</table>

## Skill 详情

<a id="thesis-tutor"></a>

### Thesis Tutor

**分类** Cursor Skill · **记录日期** 2026-06-23 · **Stars** 0 · **状态** 收藏 · **标签** 论文, 学术写作, 多语言, 开题, 答辩, DeepSeek, Python · **仓库** [https://gitee.com/xiaoruoyu1206/thesis-tutor](https://gitee.com/xiaoruoyu1206/thesis-tutor) · **Issue** [#6](https://github.com/whisper-xiang/skills-record/issues/6)

#### 简介

Thesis Tutor（v4.1.0）是一款智能论文辅导系统，帮助学生从选题到定稿的全流程写作。支持 7 种语言、15 个学科、190+ 知识文档；采用正则意图匹配 + 本地 Markdown 知识库实现零成本快速响应，可选配置 DeepSeek API Key 启用 AI 深度分析。

#### 使用方法

**触发场景**：论文选题、开题报告、文献综述、研究方法、各章节写作、格式引用、修改润色、降重、学术英语、答辩准备等；支持中/英/日/韩/法/德/西 7 种语言。

**典型流程**：

1. 将仓库克隆到 Cursor skills 目录（或引用 `SKILL.md`）
2. 直接提问论文相关问题，系统自动识别意图（选题、大纲、开题、写作、修改、答辩等 15+ 类）
3. 可选：`Configure API Key: <YOUR_API_KEY>` 启用 DeepSeek 深度分析
4. 可选：`Switch language to English` 或说明专业领域切换学科上下文

**示例提示词**：

```
如何选择一个好的论文题目？
开题报告怎么写？
如何降低查重率？
Switch language to English
我的专业是计算机科学
```

**内置命令**：

| 命令 | 功能 |
|------|------|
| `Configure API Key: <KEY>` | 设置 DeepSeek API Key |
| `Remove API Key` | 移除 API Key |
| `Check API Status` | 检查 API 连接 |
| `Switch language to xx` | 切换语言 |
| `Help` | 显示帮助 |

#### 使用效果

- 本地引擎可离线使用；AI 引擎需 DeepSeek API Key 与网络
- Gitee 仓库当前 0 Star；MIT License
- 与 `thesis-defense-pptx`（答辩 PPT 生成）、`Academic Research Skills`（Claude 学术研究全流程）互补：本 Skill 侧重选题到定稿的辅导问答与本地知识库

---

<a id="nature-skills"></a>

### nature-skills

**分类** 其他 · **记录日期** 2026-06-23 · **Stars** 22.3k · **状态** 收藏 · **标签** Nature, 论文, 科研绘图, 学术写作, Codex, Cursor · **仓库** [https://github.com/Yuan1z0825/nature-skills](https://github.com/Yuan1z0825/nature-skills) · **Issue** [#5](https://github.com/whisper-xiang/skills-record/issues/5)

#### 简介

面向 Nature / 高影响力期刊的科研技能包集合，由袁一哲创立。围绕 `SKILL.md` 组织，涵盖学术写作润色、科研绘图、文献检索、论文转 PPT、审稿回复、专利起草等 11 个子技能。主打 Codex 安装，也可适配 Claude Code、Cursor 等 agent（需保留完整目录结构与 `skills/_shared/`）。

#### 使用方法

**适用场景**：Nature 风格英文润色、投稿级科研图、全文 Markdown 对照阅读、论文转 PPT、预投稿评审、CNS 引用检索、Data Availability 声明、审稿意见回复、论文转专利等。

**子技能一览**：

| 技能 | 成熟度 | 用途 |
|------|--------|------|
| `nature-figure` | Stable | 投稿级 Python/R 科研图，内置 figures4papers demo |
| `nature-polishing` | Stable | 学术文本润色/重构/翻译为 Nature 风格英文 |
| `nature-writing` | Draft | 起草 Nature 风格手稿章节 |
| `nature-reviewer` | Draft | 模拟 Nature 风格三份 reviewer reports |
| `nature-citation` | Beta | CNS 系列支撑文献检索，导出 ENW/RIS/Zotero RDF |
| `nature-data` | Draft | Data Availability statement、仓储方案、FAIR 检查 |
| `nature-reader` | Beta | 全文 Markdown reader（来源锚点、图文对应、中英对照） |
| `nature-response` | Beta | 逐点回复审稿人 response letter |
| `nature-paper2ppt` | Beta | 论文生成中文 PPTX 文献汇报 |
| `nature-paper-to-patent` | Beta | 论文/技术报告转中国发明专利草稿 |
| `nature-academic-search` | Beta | 多源文献检索、引用核验、参考文献管理 |

**典型触发示例**：

```text
把这篇论文做成中英文对照的完整 Markdown reader。
把这篇论文做成中文PPT。
Nature style 润色这段学术文本。
```

**设计原则**：优先一手来源（Nature 已发表内容/官方指南）、显式规则、感知章节上下文、输出可直接使用的产物、技能目录自包含可扩展。

#### 使用效果

- **作者**：袁一哲（Yuan1z0825）
- **影响力**：约一个半月获 2 万+ star；曾被 Google DeepMind Science-skills 借鉴引用体系与设计思路
- **姊妹/参考**：DeepMind [Science-skills](https://github.com/google-deepmind/science-skills)（若存在）
- **与 ARS 对比**：nature-skills 聚焦 Nature/CNS 风格表达与绘图；academic-research-skills 覆盖更完整 pipeline。可互补使用
- **待尝试**：在 Cursor 中手动部署 `nature-reader` 或 `nature-figure`

---

<a id="academic-research-skills"></a>

### Academic Research Skills (ARS)

**分类** Claude Skill · **记录日期** 2026-06-23 · **Stars** 33.7k · **状态** 收藏 · **标签** 学术, 论文, 文献综述, 同行评审, Claude Code · **仓库** [https://github.com/imbad0202/academic-research-skills](https://github.com/imbad0202/academic-research-skills) · **Issue** [#4](https://github.com/whisper-xiang/skills-record/issues/4)

#### 简介

面向 Claude Code 的学术研究全流程技能套件（v3.13.0），覆盖「研究 → 写作 → 审稿 → 修订 → 定稿」完整 pipeline。核心理念是 **AI 作副驾驶而非代写**：处理文献检索、引用格式化、数据核验、逻辑一致性检查等繁琐工作，人类负责定义问题、选择方法、解读数据与核心论证。

包含 4 个子 skill、27 种模式，多 Agent 协作，内置 Stage 2.5 / 4.5 学术诚信闸门（虚构引用、统计错误、主张-引用对齐等）。

#### 使用方法

**适用场景**：写学术论文、做系统性文献综述、模拟同行评审、全流程 pipeline 编排、修订回复审稿意见。

**四大子 skill**：

| 子 skill | 能力 | 典型触发 |
|----------|------|----------|
| Deep Research | 13 Agent 研究团队，8 种模式 | 「Research the impact of AI on higher education」 |
| Academic Paper | 12 Agent 写作团队，11 种模式 | 「Write a paper on X」「Guide me through writing a paper」 |
| Academic Paper Reviewer | 7 Agent 多视角评审，6 种模式 | 「Review this paper」 |
| Academic Pipeline | 10 阶段全流程调度器 | 「I want to write a complete research paper」 |

**常用 Slash 命令**（Claude Code）：

```
/ars-plan              # 苏格拉底式规划论文结构
/ars-lit-review "主题"  # 文献综述快速测试
/ars-3w                # 三向扫描论文对比
/ars-rebuttal-audit    # 审计回复审稿意见草稿
```

**Pipeline 阶段概览**：RESEARCH → WRITE → 诚信闸门(2.5) → REVIEW → REVISE → 诚信闸门(4.5) → FINALIZE → Process Summary

**支持语言**：英文、繁体中文（默认）；苏格拉底/规划模式支持意图检测，可用其他语言。

**引用格式**：APA 7.0（默认）、Chicago、MLA、IEEE、Vancouver

**论文结构**：IMRaD、主题综述、理论分析、案例研究、政策简报、会议论文

#### 使用效果

- **作者**：Cheng-I Wu（吳政宜）
- **许可**：CC BY-NC 4.0（非商业使用）
- **费用参考**：完整 pipeline 约 $4–6 / 篇 15k 字论文（见 PERFORMANCE.md）
- **与 humanizer 的区别**：目标是提升写作质量、风格校准，而非隐藏 AI 协作痕迹
- **配套生态**：Experiment Agent（实验阶段）、Teaching Skills（教学侧姐妹项目）
- **待尝试**：评估是否在 Cursor 中通过 symlink 方式可用；对比现有 `thesis-defense-pptx` 等论文相关 skill 的分工

---

<a id="cnki"></a>

### CNKI Research Toolkit

**分类** Cursor Skill · **文档** [skills/cnki/README.md](skills/cnki/README.md)

#### 简介

面向 Cursor / Claude Agent 的 **中国知网（CNKI）文献研究 Skill**。将原先分散的 10 个子 Skill 合并为单一工作流，通过 **Chrome DevTools MCP** 在真实浏览器中完成检索、解析、下载、导出与期刊分析。

#### 使用方法

在对话中直接用自然语言描述任务即可，Agent 会加载本 Skill 并路由到对应章节。

### 触发示例

```text
在知网搜一下「大语言模型 教育应用」
用高级检索：主题=Transformer，来源类别=CSSCI，2020–2025
把当前结果页论文列表列出来
翻到第 3 页，按被引排序
打开第 2 篇的摘要和关键词
下载这篇 PDF
把本页结果全部导入 Zotero
查一下《计算机学报》是不是北大核心，影响因子多少
看计算机学报 2025 年 01 期目录，并下载原版目录
```

### 参数提示（argument-hint）

```text
[CNKI task: search/download/export/journal/index/toc + query or URL]
```

#### 使用效果

本 Skill 覆盖知网文献研究的完整链路，Agent 根据用户意图自动路由到对应模块：

| 用户意图 | 模块 | 典型工具调用数 |
|----------|------|----------------|
| 关键词检索论文 | 基础检索 | 2（导航 + 脚本） |
| 作者/期刊/年份/核心库筛选 | 高级检索 | 2 |
| 解析当前结果页列表 | 结果解析 | 1 |
| 翻页 / 排序 | 分页与排序 | 1 |
| 单篇元数据与摘要 | 论文详情提取 | 2–3 |
| 下载 PDF / CAJ | 文献下载 | 1–2 |
| 导出 Zotero / RIS / GB 引用 | 导出与 Zotero 集成 | 2（批量更优） |
| 按刊名/ISSN/CN 找期刊 | 期刊检索 | 2 |
| 查收录库与影响因子 | 期刊收录查询 | 3–5 |
| 浏览某期目录 / 原版目录 PDF | 期刊目录浏览 | 1+ |

**设计原则**：尽量少用 `wait_for` 与点击链接；优先 `navigate_page` 直达 URL；单次 `evaluate_script` 内完成等待与提取，降低 MCP 调用次数。


## GitHub 项目详情

<a id="wiltodelta-remove-ai-watermarks"></a>

### remove-ai-watermarks

**分类** GitHub 项目 · **记录日期** 2026-06-24 · **Stars** 3.5k · **状态** 收藏 · **标签** AI, 水印, 图像处理, CLI, Python, Gemini, SynthID, C2PA, 元数据 · **仓库** [https://github.com/wiltodelta/remove-ai-watermarks](https://github.com/wiltodelta/remove-ai-watermarks) · **Issue** [#8](https://github.com/whisper-xiang/skills-record/issues/8)

#### 简介

Remove-AI-Watermarks 是面向 AI 生成图像的 watermark 与 provenance 清理工具，提供 CLI 与 Python 库。支持去除 Google Gemini / Nano Banana 可见星标、SynthID 等不可见水印，以及 C2PA、EXIF、IPTC「Made with AI」等元数据。覆盖 Gemini、DALL-E、Stable Diffusion、FLUX、豆包/即梦、Samsung Galaxy AI 等多平台输出。

在线试用（无需本地 GPU）：https://raiw.cc

#### 使用方法

```bash
# Homebrew（macOS/Linux，核心 CLI）
brew install wiltodelta/tap/remove-ai-watermarks

# pipx / uv 安装完整 CLI
pipx install git+https://github.com/wiltodelta/remove-ai-watermarks.git

# 不可见水印 / diffusion 管线需 GPU 扩展
pip install "remove-ai-watermarks[gpu]"

# 可见水印示例
remove-ai-watermarks visible input.png -o clean.png

# 元数据剥离
remove-ai-watermarks metadata input.jpg -o clean.jpg --remove
```

#### 使用效果

- **可见水印**：Gemini 星标、豆包「豆包AI生成」、即梦「★ 即梦AI」、Samsung Galaxy AI 角标等，CPU 反向 alpha 混合，约 0.05s/张
- **不可见水印**：SynthID、StableSignature、TreeRing 等，基于 SDXL diffusion 重生成（需 GPU 或 raiw.cc 云端）
- **元数据剥离**：C2PA、EXIF、PNG text、XMP DigitalSourceType；支持 PNG/JPEG/AVIF/MP4 等
- **通用擦除**：`erase --region` 指定区域 inpaint；可选 LaMa 后端
- **检测与溯源**：`identify` 聚合 C2PA、TC260 AIGC 标签、可见/不可见水印信号
- **批量处理**、三阶段 NCC 检测、可选 Analog Humanizer 胶片颗粒后处理

- 清理**自己生成**的 AI 图片上的平台水印与「Made with AI」元数据标签
- 批量处理 Gemini / SD / 豆包等输出，本地 CPU 去可见水印
- 有 GPU 时需去除 SynthID 等不可见水印；无 GPU 可用 raiw.cc 云端

**注意**：项目声明仅用于合法用途；不针对图库付费预览水印等他人版权内容。部分司法辖区对移除 AI 标识有限制，使用需自行合规。

Apache-2.0。Stars ~3.5k，forks 311。与 ClipSketch AI 同属 AI 图像工具链，但侧重水印/元数据清理而非创作。

---

<a id="ranfeng-clipsketch-ai"></a>

### ClipSketch AI

**分类** GitHub 项目 · **记录日期** 2026-06-23 · **Stars** 1.8k · **状态** 收藏 · **标签** 视频, AI, Gemini, 手绘, 故事板, 小红书, Bilibili, 二创 · **仓库** [https://github.com/RanFeng/clipsketch-ai](https://github.com/RanFeng/clipsketch-ai) · **Issue** [#7](https://github.com/whisper-xiang/skills-record/issues/7)

#### 简介

ClipSketch AI（剪辑·素描）是面向视频创作者、社交媒体运营者和二创爱好者的 AI 驱动内容创作工作台。它可解析 Bilibili 与小红书分享链接，支持帧级精准标记精彩瞬间，并借助 Google Gemini 多模态模型将标记帧转化为手绘风格故事板，同时自动生成适配小红书等平台的种草文案。

在线体验：https://clipsketch-ai.vercel.app

#### 使用方法

```bash
git clone https://github.com/RanFeng/clipsketch-ai.git
cd clipsketch-ai
npm install
# .env.local 填入 GEMINI_API_KEY=your_api_key_here
npm run dev
# 访问 http://localhost:3000
```

Docker：

```bash
docker run -d --restart=always --name clipsketch-ai -p 3000:3000 earisty/clipsketch-ai:latest
```

#### 使用效果

- **多源视频导入**：支持 B 站、小红书分享链接（含短链与混合文案），竖屏/宽屏自适应播放
- **帧级标记系统**：毫秒级打点（快捷键 `T`），可导出 TXT 时间轴或 ZIP 标记帧包
- **AI 艺术工作室**：Gemini 生成连贯手绘故事板；3 种风格种草文案；自定义角色融合；竖屏封面生成；分镜批量精修
- **全平台响应式**：PC / iPad / 手机均可操作，移动端自动切换上下布局
- **Docker 一键部署**：`earisty/clipsketch-ai:latest` 镜像

- 从 B 站/小红书视频提取高光帧，快速产出二创素材与分镜
- 需要将视频内容转化为手绘故事板 + 社交媒体文案的内容运营
- 有 Gemini API Key，希望本地或 Docker 自托管 AI 视频创作工具

**技术栈**：React 19、TypeScript、Tailwind CSS、Google GenAI SDK、IndexedDB 本地持久化。

**注意**：AI 绘图需 API Key 有权访问 `gemini-3-pro-image-preview`；外部视频播放依赖特定代理与 `referrerPolicy` 策略。

MIT 许可。Stars ~1.8k，forks 233。适合与论文/学术类 skill 无关，但适合短视频二创与社媒运营场景。


## 想法详情

<a id="idea-儿童动画插入工艺广告"></a>

### 儿童动画插入工艺广告

**分类** 想法 · **记录日期** 2026-06-24 · **状态** 灵感 · **标签** 儿童, 动画, 广告, 工艺, 内容变现 · **Issue** [#9](https://github.com/whisper-xiang/skills-record/issues/9)

#### 简介

在儿童向动画里插入「工艺」类广告——可能是手工艺、非遗、匠人品牌等，与画面/剧情做融合而非硬切贴片。

#### 使用方法

- 明确目标平台（短视频 / 长视频 / 独立 IP）
- 梳理「工艺广告」形态：剧情植入、角色道具、片尾工坊探访等
- 评估儿童内容与商业广告的合规与尺度

#### 使用效果

（用户口述标题，未补充具体场景。）

待深化：广告是甲方定制还是自有 IP 变现；「工艺」具体指哪类品类。
