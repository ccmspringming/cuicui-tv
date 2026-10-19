# cuicui-tv — Cloudflare Workers 部署说明

LibreTV（Next.js 15）通过 `@opennextjs/cloudflare` 适配器部署到 Cloudflare Workers。

## 本仓库新增内容

| 文件 | 作用 |
|---|---|
| `open-next.config.ts` | OpenNext Cloudflare 适配器配置 |
| `wrangler.jsonc` | Workers 配置（`nodejs_compat`、静态资源绑定） |
| `.github/workflows/deploy-cloudflare.yml` | push 到 main 自动构建并部署 |
| `package.json` | 增加 `@opennextjs/cloudflare` + `wrangler` 依赖与脚本 |

本地已验证：`next build` → `opennextjs-cloudflare build` → `opennextjs-cloudflare preview`，`/api/status` 返回正确版本号。

## 首次部署（三步）

### 1. 配置 GitHub Secrets

仓库 → Settings → Secrets and variables → Actions → New repository secret：

| Name | 说明 |
|---|---|
| `CLOUDFLARE_API_TOKEN` | Cloudflare API Token（模板 **Edit Cloudflare Workers**） |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare Account ID（Dashboard 右侧栏） |
| `PASSWORD` | 站点访问密码 |

`CLOUDFLARE_API_TOKEN` 生成路径：Cloudflare Dashboard → My Profile → API Tokens → Create Token → 选 **Edit Cloudflare Workers** 模板。

### 2. 触发部署

Actions → Deploy to Cloudflare Workers → Run workflow（或直接 push 到 main）。

### 3. 绑定域名

Cloudflare Dashboard → Workers & Pages → `cuicui-tv` → Settings → Domains & Routes → Add custom domain → 填 `tv.cuicui.de`。

> 若 `tv.cuicui.de` 目前被旧的 Cloudflare Pages 项目占用，需先在 Pages 项目里移除该域名，再绑定到 Worker。

## 环境变量

在 Worker → Settings → Variables and Secrets 中添加（**用 Secret 类型**）：

| 变量 | 必填 | 说明 |
|---|---|---|
| `PASSWORD` | 是 | 访问密码 |

其余可选变量见上游文档（`DEFAULT_SOURCES`、`DEFAULT_LIVE_SOURCES`、`LIVE_ALLOW_PRIVATE` 等）。

## 升级上游

```bash
git fetch upstream
git merge upstream/main     # 解决冲突后
git push origin main        # 自动触发重新部署
```

## 数据迁移

浏览器打开旧站（Pages 版）→ 设置 → 导出配置；新站 → 设置 → 导入配置。点播源、直播源、观看历史一并迁移。
