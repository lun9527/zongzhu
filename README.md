# 九段总助测评报告系统

一个基于 Excel 上传、按三份 TXT 语料执行判读逻辑、批量生成 PDF 报告的 Web 系统。

## 1. 项目目标

- 输入：固定格式的 Excel（`.xlsx`/`.xls`）。
- 处理：按分数计算段位与能力等级，再按语料库匹配文案。
- 输出：与模板风格对齐的 PDF 报告（支持批量）。

## 2. 核心能力

- 支持前端上传 Excel 并批量生成多份 PDF。
- 严格校验 Excel 关键列，缺列时直接返回错误。
- 使用 `job_id` 隔离上传与输出目录，避免并发互相覆盖。
- 下载链接含 `job_id`，避免跨任务误下载。
- 自动清理历史任务目录，控制磁盘占用。
- 提供 `/healthz` 健康检查接口。

## 3. 判读逻辑（以三份 TXT 语料为准）

代码实现位置：`/Users/yanzhanglun/Desktop/测评报告/assessment-skill/main.py`

### 3.1 段位判定（总分）

总分 = 九项能力分值之和：
- 执行力、协调力、优化力、统筹力、预见力、业务力、财务力、领导力、决策力

段位区间：
- 一段：`0 - 15.09`
- 二段：`15.1 - 30.09`
- 三段：`30.1 - 40.09`
- 四段：`40.1 - 45.09`
- 五段：`45.1 - 55.09`
- 六段：`55.1 - 70.09`
- 七段：`70.1 - 75.09`
- 八段：`75.1 - 85.09`
- 九段：`85.1 - 90`

### 3.2 能力等级判定（A/B/C/D/E）

按每项能力的满分类型套用阈值：

- 满分 `8`（执行力/协调力/优化力）
  - A: `7.2-8.0`
  - B: `6.4-7.1`
  - C: `5.6-6.3`
  - D: `4.8-5.5`
  - E: `0-4.7`

- 满分 `10`（统筹力/预见力/业务力）
  - A: `9.0-10.0`
  - B: `8.0-8.9`
  - C: `7.0-7.9`
  - D: `6.0-6.9`
  - E: `0-5.9`

- 满分 `12`（财务力/领导力/决策力）
  - A: `10.8-12.0`
  - B: `9.6-10.7`
  - C: `8.4-9.5`
  - D: `7.2-8.3`
  - E: `0-7.1`

### 3.3 第三部分建议匹配规则

优势升华区（A/B）按“段位区间建议”选取，关键规则：
- 段位 `1-3`：优先 `1-3段`，其次 `1-6段`。
- 段位 `4-6`：优先 `4-6段`，其次 `1-6段`。
- 段位 `7-9`：
  - 若该能力是 A，优先 `7-9段+`；
  - 否则优先 `7-9段`。
- 特殊规则：若段位 `<=6` 且能力属于 `财务力/领导力/决策力` 且等级是 A，优先用 `7-9段+`。

重点改善区（D/E）取语料中的 improvement 内容。

核心诊断与发展建议为固定文案。

### 3.4 语料文件

位于项目根目录：
- `/Users/yanzhanglun/Desktop/测评报告/综合段位语料库.txt`
- `/Users/yanzhanglun/Desktop/测评报告/能力维度、等级及分数解读语料库.txt`
- `/Users/yanzhanglun/Desktop/测评报告/个性化发展行动计划语料库].txt`

## 4. Excel 输入格式要求

后端强校验字段（必须存在）：
- `序号`
- `微信昵称`
- `【执行力】`
- `【协调力】`
- `【优化力】`
- `【统筹力】`
- `【预见力】`
- `【业务力】`
- `【财务力】`
- `【领导力】`
- `【决策力】`

可选但推荐字段：
- `测评时间：`
- `【职业信息】输入手机号以便我们给您发送测评报告`

## 5. 输出规则

- 文件命名：`九段总助测评结果报告-NLZ100{序号}-{微信昵称}-{段位}.pdf`
- 下载地址：`/download/<job_id>/<filename>`
- 每次上传返回 `job_id` 与该次任务的文件列表。

## 6. API 一览

- `GET /`：上传页面
- `POST /upload`：上传 Excel 并生成报告
- `GET /download/<job_id>/<filename>`：下载报告
- `GET /healthz`：健康检查

## 7. 本地运行

```bash
cd /Users/yanzhanglun/Desktop/测评报告
python3 -m pip install -r requirements.txt
python3 app.py
```

浏览器访问：`http://127.0.0.1:5001`

生产模式建议：

```bash
cd /Users/yanzhanglun/Desktop/测评报告
gunicorn -c gunicorn_conf.py wsgi:app
```

## 8. 环境变量

- `APP_HOST`：Flask 本地运行监听地址（默认 `0.0.0.0`）
- `APP_PORT`：Flask 本地运行端口（默认 `5001`）
- `FLASK_DEBUG`：是否开启 debug（默认 `0`）
- `MAX_CONTENT_LENGTH_MB`：上传大小限制（默认 `16`）
- `JOB_RETENTION_HOURS`：任务保留小时数（默认 `24`）
- `MAX_KEPT_JOBS`：最大任务目录数（默认 `300`）
- `PDF_FONT_PATH`：自定义中文字体路径
- `PDF_FONT_BOLD_PATH`：自定义中文粗体字体路径

## 9. 目录结构

```text
/Users/yanzhanglun/Desktop/测评报告
├── app.py
├── wsgi.py
├── gunicorn_conf.py
├── Dockerfile
├── requirements.txt
├── templates/
├── static/
├── uploads/jobs/
├── outputs/jobs/
├── assessment-skill/
│   ├── main.py
│   ├── pdf_generator_v4.py
│   └── tests/
└── 三份语料库 txt
```

## 10. 测试与验证

```bash
cd /Users/yanzhanglun/Desktop/测评报告
python3 -m unittest discover -s assessment-skill/tests -q
python3 -m py_compile app.py assessment-skill/main.py assessment-skill/pdf_generator_v4.py wsgi.py
```

