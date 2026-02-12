#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

REPO_NAME="${1:-assessment-report}"
VISIBILITY="${2:-private}"

if [[ -z "${GH_TOKEN:-}" ]]; then
  echo "[ERROR] GH_TOKEN 未设置。"
  echo "示例：export GH_TOKEN='ghp_xxx'"
  exit 1
fi

case "$VISIBILITY" in
  public) PRIVATE_JSON=false ;;
  private) PRIVATE_JSON=true ;;
  *)
    echo "[ERROR] 第二个参数只能是 public 或 private"
    exit 1
    ;;
esac

# 1) 初始化 git
if [[ ! -d .git ]]; then
  git init -b main
fi

# 2) 基础 git 身份（仅当前仓库）
if ! git config user.name >/dev/null; then
  git config user.name "codex-bot"
fi
if ! git config user.email >/dev/null; then
  git config user.email "codex-bot@local"
fi

# 3) 提交当前代码
 git add .
if ! git diff --cached --quiet; then
  git commit -m "chore: prepare deployment and docs"
fi

# 4) 获取 GitHub 用户名
USER_JSON="$(curl -fsSL \
  -H "Authorization: Bearer ${GH_TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/user)"

OWNER="$(python3 - <<'PY'
import json,sys
obj=json.loads(sys.stdin.read())
print(obj.get('login','').strip())
PY
<<<"$USER_JSON")"

if [[ -z "$OWNER" ]]; then
  echo "[ERROR] 无法从 GH_TOKEN 获取 GitHub 用户信息。"
  exit 1
fi

# 5) 创建仓库（已存在则忽略）
CREATE_PAYLOAD="$(python3 - <<PY
import json
print(json.dumps({"name":"$REPO_NAME","private":$PRIVATE_JSON}))
PY
)"

HTTP_CODE="$(curl -s -o /tmp/github_repo_create_resp.json -w "%{http_code}" \
  -H "Authorization: Bearer ${GH_TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  -d "$CREATE_PAYLOAD" \
  https://api.github.com/user/repos)"

if [[ "$HTTP_CODE" != "201" && "$HTTP_CODE" != "422" ]]; then
  echo "[ERROR] GitHub 创建仓库失败，HTTP=$HTTP_CODE"
  cat /tmp/github_repo_create_resp.json
  exit 1
fi

REPO_URL="https://github.com/${OWNER}/${REPO_NAME}.git"
if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "$REPO_URL"
else
  git remote add origin "$REPO_URL"
fi

# 6) 使用 GIT_ASKPASS 推送，避免在命令行明文暴露 token
ASKPASS_FILE="$(mktemp)"
cat > "$ASKPASS_FILE" <<'AP'
#!/usr/bin/env bash
case "$1" in
  *Username*) echo "x-access-token" ;;
  *Password*) echo "${GH_TOKEN}" ;;
  *) echo "" ;;
esac
AP
chmod +x "$ASKPASS_FILE"

GIT_ASKPASS="$ASKPASS_FILE" GIT_TERMINAL_PROMPT=0 git push -u origin main
rm -f "$ASKPASS_FILE"

PUBLIC_REPO_URL="https://github.com/${OWNER}/${REPO_NAME}"
RENDER_ONE_CLICK_URL="https://render.com/deploy?repo=${PUBLIC_REPO_URL}"

echo ""
echo "✅ 已推送到 GitHub: ${PUBLIC_REPO_URL}"
echo "🚀 Render 一键部署链接: ${RENDER_ONE_CLICK_URL}"
echo ""
echo "部署完成后你会拿到域名：https://<service-name>.onrender.com"
