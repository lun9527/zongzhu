# 部署方案（低维护、非大规模场景）

你当前场景（小规模、希望快上线）最推荐：
- GitHub 托管代码
- Hugging Face Spaces（Docker，自动分配 `*.hf.space` 域名 + 自动 HTTPS）

## 0. 免付费门槛方案（推荐）

如果 Render 页面提示付费，建议切换到 Hugging Face Spaces：

1. 打开：https://huggingface.co/new-space
2. 填写：
   - `Owner`：你的 HF 账号
   - `Space name`：`assessment-report`
   - `License`：任选（如 `MIT`）
   - `SDK`：`Docker`
   - `Visibility`：`Public`（免费）
3. 本地执行（将当前仓库推送到 Space）：
   ```bash
   cd /Users/yanzhanglun/Desktop/测评报告
   git remote add hf https://huggingface.co/spaces/<你的HF用户名>/assessment-report
   git push hf main
   ```
4. 在 Space 的 `Settings -> Variables` 添加：
   - `MAX_CONTENT_LENGTH_MB=20`
   - `JOB_RETENTION_HOURS=24`
   - `MAX_KEPT_JOBS=300`
   - `GUNICORN_WORKERS=1`
   - `GUNICORN_THREADS=2`
   - `GUNICORN_TIMEOUT=300`
5. 等待构建完成后访问：
   - `https://<owner>-assessment-report.hf.space`

说明：
- 项目已支持读取平台 `PORT` 环境变量，无需额外改代码。
- 适合你当前小规模给朋友使用的场景。

## 1. 最省事流程（推荐）

### 1.1 一次性准备

你只需要提供 GitHub Token（Classic 或 Fine-grained，具备仓库创建/写入权限）：

```bash
export GH_TOKEN='你的GitHubToken'
```

### 1.2 一条命令自动完成

```bash
cd /Users/yanzhanglun/Desktop/测评报告
./scripts/publish_and_prepare_deploy.sh assessment-report private
```

脚本会自动做：
- 初始化 git（如果尚未初始化）
- 提交当前代码
- 在你的 GitHub 账号下创建仓库
- 推送 `main` 分支
- 输出 Render 一键部署链接

### 1.3 一键部署

打开脚本输出的链接：
- `https://render.com/deploy?repo=https://github.com/<你的账号>/<仓库名>`

点击 Deploy 后，Render 会给你一个可直接访问的域名：
- `https://<service-name>.onrender.com`

你可以直接把这个域名发给朋友使用。

---

## 2. 代码中已具备的部署能力

- `Dockerfile`：容器化运行
- `render.yaml`：Render Blueprint 配置
- `/healthz`：健康检查
- `job_id` 隔离目录：并发更安全
- 自动清理历史任务目录：减少磁盘堆积

---

## 3. 运行参数（Render / Docker 通用）

可通过环境变量调整：
- `MAX_CONTENT_LENGTH_MB`（默认 `16`）
- `JOB_RETENTION_HOURS`（默认 `24`）
- `MAX_KEPT_JOBS`（默认 `300`）
- `GUNICORN_WORKERS`（默认 `1`）
- `GUNICORN_THREADS`（默认 `2`）
- `GUNICORN_TIMEOUT`（默认 `300`）

---

## 4. 如果你坚持全自动（连部署点击都不想做）

可以继续走 API 自动化，但需要额外提供平台 API Key（比如 Render API Key）。
我拿到后可以继续帮你做“推送后自动创建服务并返回域名”的全链路脚本。
