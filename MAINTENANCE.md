# 维护手册（Maintenance Guide）

适用项目：`/Users/yanzhanglun/Desktop/测评报告`

目标：给后续维护者一份“可直接接手”的操作说明，确保在不破坏现有 PDF 生成效果的前提下，持续更新功能与部署版本。

---

## 1. 现状基线

- 当前系统是 **Web 上传 Excel -> 后端异步任务 -> 批量生成 PDF -> 在线下载/ZIP 下载**。
- 核心判读逻辑以三份 TXT 语料为准，代码实现已对齐。
- 线上部署主用 Hugging Face Space（Docker）。
- 目前已修复过的高频问题：
  - 前端 `Failed to fetch`（异步任务与下载链路）
  - 线上字体异常（本地正常、线上异常）
  - 雷达图中文乱码（Matplotlib 字体回退）
  - 段位边界浮点误判（`55.1` 被误判一段）
  - 第三部分分页与排版稳定性

### 1.1 当前线上版本核验点

- 生产访问地址：`https://lun9527-zongzhu.hf.space`
- 关键样例（2026-03-10 回归）：
  - `NLZ100118` 应为 `六段`（不是一段）
- 修复原则：
  - 判段前总分统一 `round(total_score, 2)`

---

## 2. 关键目录与职责

- `/Users/yanzhanglun/Desktop/测评报告/app.py`
  - Flask 入口
  - 异步任务管理（`/jobs`、进度、下载、归档）
  - 上传校验与任务目录管理
- `/Users/yanzhanglun/Desktop/测评报告/assessment-skill/main.py`
  - 读取 Excel
  - 段位/等级判定
  - 按语料组装内容
- `/Users/yanzhanglun/Desktop/测评报告/assessment-skill/pdf_generator_v4.py`
  - PDF 页面结构与排版
  - 雷达图绘制
  - 字体注册与字体回退策略
- `/Users/yanzhanglun/Desktop/测评报告/assessment-skill/fonts/template/`
  - PDF 中文字体资源（必须保留完整字形字体）
- `/Users/yanzhanglun/Desktop/测评报告/templates/index.html`
  - 页面骨架
- `/Users/yanzhanglun/Desktop/测评报告/static/app.js`
  - 上传、轮询、状态显示、下载行为
- `/Users/yanzhanglun/Desktop/测评报告/static/style.css`
  - Web 视觉样式
- `/Users/yanzhanglun/Desktop/测评报告/scripts/qa_check_reports.py`
  - 批量 PDF 质量校验脚本
- `/Users/yanzhanglun/Desktop/测评报告/DEPLOYMENT.md`
  - 平台部署说明

---

## 3. 接口与运行行为（必须保持兼容）

必须可用接口：

- `GET /healthz`
- `POST /jobs`
- `GET /jobs/<job_id>`
- `GET /jobs/<job_id>/files`
- `GET /jobs/<job_id>/file/<int:file_index>`
- `GET /jobs/<job_id>/archive`
- `POST /upload`（兼容旧入口）
- `GET /download/<job_id>/<filename>`（兼容旧下载）

不建议随意变更：

- `job_id` 目录隔离机制
- 按 `file_index` 下载的实现（避免中文/emoji 文件名兼容问题）
- 任务保留/清理策略（`JOB_RETENTION_HOURS`、`MAX_KEPT_JOBS`）

---

## 4. 本地开发与回归

### 4.1 启动

```bash
cd /Users/yanzhanglun/Desktop/测评报告
python3 -m pip install -r requirements.txt
python3 app.py
```

访问：

- `http://127.0.0.1:5001`

### 4.2 最小检查（改动后必跑）

```bash
cd /Users/yanzhanglun/Desktop/测评报告
python3 -m py_compile app.py assessment-skill/main.py assessment-skill/pdf_generator_v4.py wsgi.py
python3 -m unittest discover -s assessment-skill/tests -q
```

### 4.3 批量质量校验（建议）

```bash
cd /Users/yanzhanglun/Desktop/测评报告
python3 scripts/qa_check_reports.py \
  --excel "/Users/yanzhanglun/Desktop/测评报告/总助九段胜任力专业测评--3.0_20260125161237.xlsx" \
  --reports-dir "/Users/yanzhanglun/Desktop/测评报告/outputs/jobs/<job_id>"
```

---

## 5. 变更规范（按类型）

### 5.1 判读逻辑变更

只改：

- `/Users/yanzhanglun/Desktop/测评报告/assessment-skill/main.py`
- 三份语料 TXT

必须验证：

- 段位是否按阈值正确
- 9 维能力等级是否按满分类型（8/10/12）正确
- 10084、10076 等历史样例不回归

### 5.2 PDF 排版或字体变更

只改：

- `/Users/yanzhanglun/Desktop/测评报告/assessment-skill/pdf_generator_v4.py`
- `/Users/yanzhanglun/Desktop/测评报告/assessment-skill/fonts/template/*`

必须验证：

- 本地与线上（HF）字体一致
- 雷达图标签无乱码
- 三大部分分页规则符合当前需求
- 第三部分底部与日期间距稳定

注意：

- 不要把“精简子集字体”当默认字体资源。
- Matplotlib 必须绑定可用中文字体文件（避免容器回退乱码）。

### 5.3 前端交互变更

只改：

- `/Users/yanzhanglun/Desktop/测评报告/templates/index.html`
- `/Users/yanzhanglun/Desktop/测评报告/static/app.js`
- `/Users/yanzhanglun/Desktop/测评报告/static/style.css`

必须验证：

- 上传后能拿到 `job_id`
- 状态轮询从 `queued/running` 到 `success/failed`
- 文件列表、单文件下载、ZIP 下载都可用

---

## 6. 线上部署与发布（Hugging Face）

### 6.1 发布前

```bash
cd /Users/yanzhanglun/Desktop/测评报告
git status --short
python3 -m py_compile app.py assessment-skill/main.py assessment-skill/pdf_generator_v4.py
python3 -m unittest discover -s assessment-skill/tests -q
```

### 6.2 发布后验收（线上）

以 `BASE_URL=https://lun9527-zongzhu.hf.space` 为例：

```bash
curl -sS "$BASE_URL/healthz"
curl -sS -X POST -F "file=@/Users/yanzhanglun/Desktop/测评报告/总助九段胜任力专业测评--3.0_20260125161237.xlsx" "$BASE_URL/jobs"
```

拿到 `job_id` 后：

```bash
curl -sS "$BASE_URL/jobs/<job_id>"
curl -sS "$BASE_URL/jobs/<job_id>/files"
curl -I -sS "$BASE_URL/jobs/<job_id>/archive"
```

通过标准：

- `healthz` 返回 `status=ok`
- 任务最终 `status=success`
- `files` 可列出结果
- `archive` 返回 `200` 且 `application/zip`

---

## 7. 常见故障与处理

### 7.1 前端显示 `Failed to fetch`

检查顺序：

- `GET /healthz` 是否可达
- 浏览器 Network 里 `POST /jobs` 是否 202
- 是否命中了旧缓存 JS（强刷 + 版本参数）
- 线上容器是否重建成功

### 7.2 本地字体正常、线上字体异常

优先检查：

- `assessment-skill/fonts/template` 是否为完整字体文件
- `pdf_generator_v4.py` 字体候选顺序是否被改坏
- Matplotlib 是否绑定了中文字体文件

### 7.3 雷达图中文乱码

根因通常是 Matplotlib 字体回退。处理：

- 在 `generate_radar_chart_v2` 中使用字体文件路径构造 `FontProperties`
- 对雷达轴标签和图例同时设置字体

### 7.4 第三部分分页或底部间距异常

检查：

- `PageBreak()` 是否被误改
- 第三部分 `ParagraphStyle` 的 `leading/spaceBefore/spaceAfter`
- 页脚日期绘制坐标是否被改动

### 7.5 “分数不低但段位显示一段”

排查顺序：

- 先核对该用户 9 维分值和 `测评得分` 列。
- 打印总分原始值（`repr(total_score)`）看是否为 `xx.x999999...`。
- 确认 `get_rank()` 入口有两位小数标准化（`round(..., 2)`）。

验收标准：

- 边界分值（如 `55.1`）必须稳定落入正确段位。
- 单测 `test_rank_boundary_handles_float_precision` 必须通过。

---

## 8. 环境变量建议值

- `APP_HOST=0.0.0.0`
- `APP_PORT=5001`（本地）
- `MAX_CONTENT_LENGTH_MB=20`
- `JOB_RETENTION_HOURS=24`
- `MAX_KEPT_JOBS=300`
- `JOB_WORKERS=1`
- `GUNICORN_WORKERS=1`
- `GUNICORN_THREADS=2`
- `GUNICORN_TIMEOUT=300`

字体定制（可选）：

- `PDF_FONT_PATH`
- `PDF_FONT_BOLD_PATH`

---

## 9. 维护发布流程（建议固定）

每次发布按这个顺序：

1. 本地改动与自测（语法 + 单测 + 小样本生成）
2. 关键样例回归（至少 10084、10076）
3. 提交 GitHub（`main`）
4. 部署/同步到 HF
5. 线上跑 1 次真实任务验收
6. 记录发布说明（改了什么、验证了什么）

---

## 10. 安全与仓库卫生

- 不要把 HF/GitHub Token 写入代码、脚本、日志。
- 用户若在聊天里泄露 Token，应立即到平台后台撤销并重建。
- `outputs/`、`tmp/`、`uploads/` 不要提交入库。
- 字体文件体积大但属于运行依赖，变更时要注明来源与目的。

---

## 11. 变更记录模板（复制即用）

```text
变更日期：
变更人：
变更范围：
- 代码文件：
- 配置文件：
- 语料文件：

变更目的：

风险点：

本地验证：
- [ ] py_compile
- [ ] unittest
- [ ] 样例PDF检查（10084/10076）

线上验证：
- [ ] /healthz
- [ ] /jobs 创建
- [ ] 任务 success
- [ ] 文件与 ZIP 下载

回滚方案：
```
