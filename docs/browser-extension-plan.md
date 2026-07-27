# BOSS 岗位采集浏览器扩展开发方案

## 1. 项目目标

为 Job Market Reality Check 增加浏览器端采集入口。

用户在 BOSS 直聘网页版浏览岗位时，打开扩展侧边栏，点击“采集当前岗位”，即可读取当前职位详情、预览结构化字段、去重保存并导出数据。

采集结果应兼容现有 Python 数据清洗、技能审计、统计分析和 HTML 看板流程。

---

## 2. 技术选型

| 模块 | 技术选择 |
|---|---|
| 扩展框架 | WXT |
| 开发语言 | TypeScript |
| 用户界面 | 原生 HTML / CSS |
| 目标浏览器 | Google Chrome、Microsoft Edge |
| 页面采集 | DOM 解析 |
| 页面变化监听 | MutationObserver |
| 本地存储 | chrome.storage.local |
| 数据导出 | JSONL、CSV |
| 扩展规范 | Manifest V3 |
| OCR | 第一版暂不加入 |

第一版优先读取网页 DOM，不使用 PaddleOCR。

OCR 仅作为未来的备用能力，用于处理截图、Canvas 页面或无法直接读取文本的特殊页面。

---

## 3. 第一版功能范围

第一版只实现以下功能：

1. 判断当前页面是否为支持的 BOSS 岗位页面。
2. 自动识别当前正在查看的岗位。
3. 提取岗位名称、公司、薪资、城市、经验、学历和职位描述。
4. 在扩展侧边栏显示采集预览。
5. 用户点击按钮后保存当前岗位。
6. 根据岗位 ID 或“公司 + 岗位名称”进行去重。
7. 查看本次已经采集的岗位数量。
8. 导出 JSONL。
9. 导出 CSV。
10. 在 Chrome 和 Edge 中测试同一套扩展。

第一版暂不实现：

- 自动翻页
- 自动遍历全部搜索结果
- 绕过登录、验证或网站风控
- 自动沟通或自动投递
- 云端数据库
- 用户账号系统
- 全网页 OCR
- 插件内直接运行全部 Python 分析
- 自动采集用户没有主动查看的岗位

---

## 4. 数据流程

```text
用户点击左侧岗位
        ↓
BOSS 右侧详情区域更新
        ↓
MutationObserver 检测 DOM 变化
        ↓
content script 提取当前岗位
        ↓
侧边栏显示结构化预览
        ↓
用户点击“采集当前岗位”
        ↓
chrome.storage.local 保存并去重
        ↓
导出 JSONL / CSV
        ↓
进入现有 Python 分析管线
        ↓
字段清洗、技能审计、岗位分析、HTML 看板
```

---

## 5. 扩展内部架构

```text
extension/
├── entrypoints/
│   ├── background.ts
│   ├── boss.content.ts
│   └── sidepanel/
│       ├── index.html
│       ├── main.ts
│       └── style.css
├── lib/
│   ├── selectors.ts
│   ├── extract-job.ts
│   ├── normalize-job.ts
│   ├── storage.ts
│   ├── export-jsonl.ts
│   └── export-csv.ts
├── types/
│   └── job.ts
├── public/
│   └── icons/
├── tests/
├── package.json
├── tsconfig.json
└── wxt.config.ts
```

### 模块职责

#### `boss.content.ts`

- 运行在 BOSS 网页中
- 监听页面岗位切换
- 调用 DOM 提取函数
- 把岗位信息发送给侧边栏和后台

#### `background.ts`

- 处理扩展后台消息
- 保存岗位
- 岗位去重
- 管理导出操作

#### `sidepanel/`

- 显示当前岗位预览
- 显示字段缺失或解析异常
- 提供采集、删除和导出按钮
- 显示本次已采集岗位数量

#### `extract-job.ts`

- 从当前页面 DOM 提取岗位信息
- 保留原始正文
- DOM 规则失败时使用可见文本回退

#### `storage.ts`

- 封装 `chrome.storage.local`
- 新增、读取、删除和清空岗位
- 避免业务代码直接操作底层存储

---

## 6. 目标数据结构

插件输出应尽量兼容现有 Python 管线：

```json
{
  "job_id": "岗位唯一标识",
  "job_title": "岗位名称",
  "salary": "薪资",
  "city": "城市",
  "experience": "经验要求",
  "education": "学历要求",
  "company_short_name": "公司简称",
  "company_full_name": "公司全称",
  "company_size": "公司规模",
  "industry": "行业",
  "job_description": "职位描述",
  "source_url": "岗位页面链接",
  "collected_at": "采集时间",
  "collector": "browser-extension",
  "status": "success"
}
```

提取不到的字段使用空字符串或 `null`，不得因为单个字段缺失导致整个采集过程崩溃。

---

## 7. 开发顺序

### 阶段一：创建 WXT 空扩展

目标：

- 扩展能够在 Chrome 中加载
- 扩展能够在 Edge 中加载
- Side Panel 能够正常打开

### 阶段二：读取当前岗位名称

目标：

- Content Script 能注入 BOSS 页面
- 能读取右侧当前岗位名称
- 岗位切换后能够自动更新

验收标准：

```text
点击不同岗位
→ 侧边栏岗位名称同步变化
```

### 阶段三：解析全部核心字段

依次增加：

- 岗位名称
- 薪资
- 公司名称
- 城市
- 工作经验
- 学历
- 职位描述
- 当前链接
- 岗位 ID

同时保留原始文本，便于规则出错时审计。

### 阶段四：加入侧边栏预览

侧边栏展示：

- 当前岗位
- 公司
- 薪资
- 城市
- 学历
- 职位描述摘要
- 缺失字段提示
- 采集按钮

### 阶段五：去重与本地保存

去重优先级：

1. 岗位 ID
2. 规范化链接
3. 公司名称 + 岗位名称 + 城市

保存位置：

```text
chrome.storage.local
```

### 阶段六：导出数据

支持：

- JSONL
- CSV

JSONL 应作为主要格式，以便兼容嵌套字段和现有 Python 管线。

CSV 用于人工查看和 Excel 分析。

### 阶段七：Chrome 与 Edge 兼容测试

Chrome：

```text
chrome://extensions
```

Edge：

```text
edge://extensions
```

两者都使用“加载已解压的扩展程序”加载构建目录。

测试内容：

- 页面注入
- 岗位切换监听
- 侧边栏
- 本地保存
- 去重
- JSONL 导出
- CSV 导出

### 阶段八：对接 Python 管线

第一版采用文件导出方式：

```text
浏览器插件导出 JSONL
→ Python 读取 JSONL
→ 清洗
→ 技能审计
→ 分析
→ 可视化
```

后续可以增加本地 API：

```text
浏览器扩展
→ localhost FastAPI
→ Python 分析管线
→ 自动更新看板
```

---

## 8. MutationObserver 设计

BOSS 网页属于动态单页应用。

用户点击左侧不同岗位后，右侧详情内容可能更新，但页面不会完整刷新。

插件应监听岗位详情区域：

```text
DOM 发生变化
→ 等待页面内容稳定
→ 重新提取岗位
→ 比较岗位 ID
→ 更新侧边栏预览
```

需要增加防抖机制，避免一次页面更新触发大量重复解析。

建议防抖时间：

```text
300 至 800 毫秒
```

---

## 9. DOM 提取策略

按以下优先级提取：

1. 稳定 DOM 容器和属性
2. 岗位详情区域中的标题和字段
3. 根据“职位描述”“任职要求”等文本锚点定位
4. 当前详情区域的可见文本
5. 保存原始文本等待人工复核

不要只依赖单个 CSS class。

网站更新后，class 名可能发生变化，因此提取器需要支持多套选择器和文本回退。

---

## 10. 隐私与安全

插件不得：

- 上传浏览器 Cookie
- 导出登录凭据
- 读取与岗位采集无关的页面内容
- 提交招聘者私人信息到公开仓库
- 自动执行沟通或投递
- 绕过网站验证和访问限制

公开仓库只保留：

- 扩展代码
- 脱敏演示数据
- 脱敏截图
- 测试
- 开发文档

---

## 11. 第一版完成标准

满足以下条件即可视为采集插件 MVP 完成：

- Chrome 可加载
- Edge 可加载
- 能识别当前岗位
- 切换岗位后能自动更新
- 能预览主要字段
- 能一键采集
- 能去重
- 能导出 JSONL
- 能导出 CSV
- 至少使用 10 条岗位进行人工核对
- 核心字段提取错误不会导致插件崩溃
- README 中有安装说明和演示截图

达到以上标准后停止增加功能，优先开始投递简历。

---

## 12. 后续版本

### v0.2

- 编辑采集结果
- 字段完整度评分
- 解析失败提示
- 采集历史管理
- 导入已有 JSONL

### v0.3

- 本地 FastAPI 对接
- 一键运行 Python 分析
- 插件内查看岗位匹配等级
- 技能缺口提示

### 未来可选

- PaddleOCR 截图导入
- 多招聘网站适配器
- 脱敏规则
- 插件配置页面
- 浏览器商店发布

OCR 不属于第一版必要功能。

---

## 13. 当前仓库整理建议

当前阶段不要立即移动现有 Python 脚本。

原因：

- 现有脚本可能依赖相对路径
- 插件开发和 Python 管线重构同时进行，容易引入路径错误
- 当前首要任务是验证浏览器端采集是否可行
- 数据协议固定后再统一迁移更稳妥

建议先新增：

```text
job-market-reality-check/
├── extension/                   # Chrome / Edge 扩展
├── demo/                        # 脱敏演示数据
├── docs/                        # 架构、截图和开发方案
│   └── browser-extension-plan.md
├── tests/                       # Python及后续扩展测试
├── output/                      # 本地输出，Git忽略
├── collect_all_boss_jobs.py
├── extract_current_boss_job.py
├── clean_boss_jobs.py
├── analyze_boss_jobs.py
├── audit_boss_skills.py
├── visualize_boss_jobs_v11.py
├── README.md
├── base_science_environment.yml
└── .gitignore
```

以下 Python 脚本暂时保留在根目录：

```text
collect_all_boss_jobs.py
extract_current_boss_job.py
clean_boss_jobs.py
analyze_boss_jobs.py
audit_boss_skills.py
visualize_boss_jobs_v11.py
```

等浏览器插件采集成功、数据协议稳定后，再迁移为：

```text
pipeline/
├── collect/
├── clean/
├── analyze/
├── audit/
└── visualize/
```

---

## 14. Git 与隐私边界

以下内容不得提交：

```text
.chrome-human-profile/
.playwright-profile/
output/
BOSS链接.xlsx
base_science_conda_packages.txt
base_science_pip_packages.txt
```

新增目录中可提交：

```text
extension/
demo/
docs/
tests/
```

其中：

- `demo/` 只放脱敏或虚构数据
- `docs/` 只放脱敏截图和公开文档
- `tests/` 不得引用真实岗位链接或招聘者信息
- `extension/` 不得包含 Cookie、Token 或本地账号信息

---

## 15. 推荐实施节奏

### 第 1 天

- 初始化 WXT 项目
- Chrome 加载扩展
- Edge 加载扩展
- Side Panel 能打开

### 第 2 天

- Content Script 注入
- 识别当前岗位名称
- MutationObserver 监听岗位切换
- 侧边栏实时更新岗位名称

### 第 3 天

- 解析主要字段
- 处理字段缺失
- 保存原始文本
- 完成预览界面

### 第 4 天

- 接入 `chrome.storage.local`
- 岗位去重
- 采集历史列表
- 删除与清空操作

### 第 5 天

- JSONL 导出
- CSV 导出
- Chrome 与 Edge 兼容测试
- 使用至少 10 条岗位人工核验

### 第 6 至 7 天

- 修复解析错误
- 增加基础测试
- 生成脱敏截图或 GIF
- 更新 README
- 整理 Git 提交

如果在第 7 天后仍未完成，应优先检查是否出现范围扩张，而不是继续增加功能。
