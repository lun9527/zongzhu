# 部署方案（低维护、非大规模场景）

你当前场景（小规模、希望快上线）最推荐：
- GitHub 托管代码
- Render 一键部署（自动分配 `*.onrender.com` 域名 + 自动 HTTPS）

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

