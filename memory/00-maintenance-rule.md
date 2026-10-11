---
type: rule
topic: 记忆维护纪律
last_updated: 2026-10-11
---

# 记忆维护纪律（长期遵守）

本文件是本记忆库的**唯一规则源**。任何 agent 读写记忆前先读这里。

## 硬性纪律

1. **`MEMORY.md` 只做索引**——每个主题一行（编号 / 主题 / 文件 / 一句话）。
   **正文一律写进 `memory/` 子文件**，索引里不堆正文。
2. **软上限 150 行或 20KB**，**永远不要逼近 200 行 / 25KB 的加载上限**。
   接近软上限就拆分或精简，不要等撞线。
3. **每个子文件只保存一个明确主题**。一个文件混两件事就拆开。
4. **写入前先检索现有记忆**——能更新旧记录，就**不要重复新增**。
5. **新结论推翻旧结论时，直接修正旧记录**，不保留互相矛盾的两个版本。
6. **Git / 代码 / 项目文档中已明确存在且容易重新获得的内容，不重复抄进记忆**。
   记忆只放：结论、判断、踩坑经验、以及"重新获得成本高"的东西。
7. **密码、密钥、Cookie、Token、私钥等一切秘密，永不写入记忆。**
8. **按类型分类**（若实现支持）：`user`（用户偏好）/ `feedback`（用户反馈）/
   `project`（项目事实）/ `reference`（外部资料指针）。
   **不为了凑分类而创建空目录或空文件。**

## 目录约定

```
E:\AIQuantEval\
├── MEMORY.md                      # 索引 + 当前状态板（唯一入口）
└── memory\
    ├── 00-maintenance-rule.md     # 本文件
    ├── 01-project-map.md
    ├── 02-environment.md
    ├── 03-quantization-findings.md  # 指针页 → aiVault
    ├── 04-pitfalls.md
    └── 05-open-questions.md
```

> 本项目当前**未启用**按类型分目录（`user/feedback/project/reference`），
> 因为 DSH 实现不提供记忆类型机制，强行建空目录违反纪律 8。
> 各文件的 `type:` frontmatter 字段承担同样的分类作用。

## 🔑 双库分工（重要，防止知识分叉）

> 这套约定是**跨项目通用**的，完整论述已沉淀在 aiVault：
> `E:\Document\Ethan'vault\aiVault\wiki\concepts\Dual_Store_Knowledge_vs_Project_Memory.md`
> （本节是它在**本项目**的落地实例，通用原则以 aiVault 那页为准。）

本机上有**两个独立的库**，职责必须分清：

| 库 | 位置 | 存什么 | 不存什么 |
| :--- | :--- | :--- | :--- |
| **aiVault**（知识真源） | `E:\Document\Ethan'vault\aiVault` | 知识正文：机理、原理、方案对比、实测数据、来源快照 | 项目进度 |
| **项目记忆库**（本库） | `E:\AIQuantEval` | **进度**：做了什么、接下来做什么、踩过的坑、未验证项 | 知识正文（只放指针） |

**规则**：

1. **知识写 aiVault，进度写本库。** 本库**不复制** aiVault 的正文，
   只放结论摘要（1–2 行）+ 指向 aiVault 对应页面的路径。
2. 一旦发现同一知识在两边都有完整正文，**以 aiVault 为准**，删掉本库的副本。
3. aiVault 有自己的规则（`aiVault/AGENTS.md`）：改完必须更新其 INDEX/LOG 并跑
   `push_ai`。**本库的规则不能替代它**，往 aiVault 写入时以 `AGENTS.md` 为准。
4. 本库与 aiVault **各自独立 git**，推送互不影响。

### 📂 aiVault 内部该落哪个目录（内容按类型分流）

写知识前先按下表选目录。**权威定义在 `aiVault/prompts/ingest.md` §4 的模板**，
本表只是速查；冲突时以 ingest.md 为准。

| 内容类型 | 落到 | 格式 | 模板 |
| :--- | :--- | :--- | :--- |
| 芯片 / 框架 / 工具（含可运行代码、编译命令） | `wiki/entities/` | `.qmd` | ingest.md §4.2 |
| 原理 / 算法 / 机制（纯文字推导） | `wiki/concepts/` | `.md` | §4.3 |
| **多方案实测对比**（精度/速度/体积数据表） | `wiki/comparisons/` | `.qmd` | §4.4 |
| 领域全景 / 技术路线 / 专题 MOC | `wiki/overview/` | `.md` | §4.5 |
| 原始来源快照（抓取物、**含本地实验记录**） | `raw/YYYYMMDD-来源/` | `.md` | §4.1 |
| 全局索引 / 时间线日志 | `INDEX.md` / `LOG.md`（根目录） | 固定 | AGENTS.md §6 |

**本项目的落点约定**（沿用已建页面）：

- 量化机理与修复方案 → `wiki/concepts/YOLO_Head_Quantization_Collapse.md`
- 量化策略选型对比 → `wiki/comparisons/RKNN_Quantization_Strategy_vs.qmd`
- RKNN 工具链限制 → `wiki/entities/RKNN_Toolkit2.qmd`
- 实验原始数据 → `raw/20261011-local/yolov8n_rknn_int8_collapse.md`

**分流判据（易混）**：

- 「**为什么**会这样」（机理）→ `concepts/`
- 「**该选哪个 / 差多少**」（实测数据对比）→ `comparisons/`
- 「**这个工具能干什么、怎么调**」→ `entities/`
- 「**数据从哪来、怎么复现**」→ `raw/`

> 一次分析常同时产出多种：如本次既写了概念页（机理）、又写了对比页（选型）、
> 还补了 raw 快照（数据）——**按类型拆开放不同目录，不要全塞进一个页面**。
>
> 图片等附件也有归属（`AGENTS.md` §8「附件本地化」）：下载到固定目录供引用。

## 关于本记忆库的性质（重要，勿误解）

- 本记忆库是**人工维护的普通 Markdown 文件**，**不是** DSH 内置的自动记忆功能。
- DSH 当前安装（2026-09-29 版）**不含** Auto Memory：全量搜索 `app.asar` 中
  `MEMORY.md`、`auto-memory`、`memoryDir` 等关键字均为 **0 命中**。
- 因此这些文件**不会被自动加载**，只在人或 agent 主动读取时生效。
- 若日后 DSH 提供了自动记忆功能，应把本库内容迁移过去，而不是两套并存。

## 📤 推送纪律（每次做完都要执行）

**本库任何改动完成后，必须立即推送 GitHub**，不要攒着、不要留半成品。

```bat
E:\AIQuantEval\push_ai.bat
```

其内容等价于：

```bat
git add .
git commit -m "update notes"
git push origin main
```

**要点**：

- 推送是**收尾动作**，不推送就等于没做完。
- 改动落在两个库时**要各自推送**：
  - 知识改动 → 跑 `E:\Document\Ethan'vault\aiVault\push_ai.bat`
  - 进度改动 → 跑 `E:\AIQuantEval\push_ai.bat`
- `push_ai.bat` 结尾有 `pause`，**在自动化/非交互环境下会卡住**；
  此时改用等效的三条 git 命令。
- ⚠️ 本库的 `git add .` 会连带未跟踪文件（如 `.onnx`/图集等大文件）。
  若出现这类文件，先补 `.gitignore`，别直接把大文件推上去。

## 自我检查（每次写入后）

- [ ] 索引里没有正文？
- [ ] `MEMORY.md` 行数 / 体积在软上限内？
- [ ] 这个主题已有文件、我是在更新而不是新增？
- [ ] 有没有留下与旧结论矛盾的段落？
- [ ] 有没有抄 git/README 已有的易得内容？
- [ ] 有没有写入任何秘密？
- [ ] **改动是否已 `push_ai` 推送？**
