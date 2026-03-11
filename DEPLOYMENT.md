# 部署说明（当前生产方案）

当前推荐与已验证方案：**Hugging Face Spaces（Docker）**。  
当前线上 Space：`lun9527/zongzhu`

- Space 页面：<https://huggingface.co/spaces/lun9527/zongzhu>
- 访问域名：<https://lun9527-zongzhu.hf.space>

---

## 1. 部署前提

- 代码仓库在本地：`/Users/yanzhanglun/Desktop/测评报告`
- Space `README.md` 已包含 front matter：
  - `sdk: docker`
  - `app_port: 8080`
- HF token 需要 `Write access to contents/settings`

---

## 2. 环境变量（Space Settings -> Variables）

建议配置：

- `MAX_CONTENT_LENGTH_MB=20`
- `JOB_RETENTION_HOURS=24`
- `MAX_KEPT_JOBS=300`
- `JOB_WORKERS=1`
- `GUNICORN_WORKERS=1`
- `GUNICORN_THREADS=2`
- `GUNICORN_TIMEOUT=300`

---

## 3. 发布方式 A：Git 推送（常规）

```bash
cd /Users/yanzhanglun/Desktop/测评报告
git remote add hf https://huggingface.co/spaces/lun9527/zongzhu  # 已有可跳过
git fetch hf main
git push hf main
```

如果出现非快进错误（`fetch first`），先同步再推：

```bash
cd /Users/yanzhanglun/Desktop/测评报告
git fetch hf main
git checkout -b codex/hf-sync FETCH_HEAD
git cherry-pick <需要上线的commit>
git push hf HEAD:main
git checkout main
```

---

## 4. 发布方式 B：API 上传（无须处理 Git 历史冲突）

适合快速替换线上单个文件：

```bash
python3 - <<'PY'
from huggingface_hub import HfApi
api = HfApi(token="hf_xxx")
api.upload_file(
    path_or_fileobj="/Users/yanzhanglun/Desktop/测评报告/assessment-skill/main.py",
    path_in_repo="assessment-skill/main.py",
    repo_id="lun9527/zongzhu",
    repo_type="space",
)
print("ok")
PY
```

---

## 5. 线上验收（每次发布后必做）

```bash
BASE_URL="https://lun9527-zongzhu.hf.space"
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

- `/healthz` 为 `status=ok`
- 任务最终 `status=success`
- `/files` 可列出生成文件
- `/archive` 返回 200 且 `content-type: application/zip`

---

## 6. 已知高频故障

1. `Failed to fetch`
- 多为前端缓存旧 JS、服务未运行或 token/权限异常。
- 先看 `/healthz`，再看浏览器 Network 的 `POST /jobs`。

2. 字体本地正常、线上异常
- 检查 `assessment-skill/fonts/template/` 是否为完整字体（非精简子集）。
- 检查 `pdf_generator_v4.py` 字体优先级与 Matplotlib 字体绑定是否被改动。

3. 段位边界判错（典型：55.1 被判成一段）
- 根因是浮点误差边界。
- 当前版本已修复：判段前总分统一 `round(..., 2)`。

---

## 7. 安全提醒

- 不要在聊天、代码或提交历史里暴露 HF token。
- 一旦泄露，立刻去 <https://huggingface.co/settings/tokens> 撤销并重建。
