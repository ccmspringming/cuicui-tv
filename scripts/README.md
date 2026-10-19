# scripts/

## cf-fix-dns.py

删除某个主机名下**遗留的 DNS 记录**，让 Worker 的自定义域名能接管该主机名。

用途：Cloudflare 报错 **100117**（`Hostname already has externally managed
DNS records`）。从 Pages 项目解绑域名后，那条 CNAME/A 记录仍留在 DNS 区里，
必须单独删除。

安全约束：

- 只删 name **精确等于** `TARGET_HOST` 的记录，不碰通配符、不碰其他子域名；
- 默认 `DRY_RUN=1`，只报告不删除；确认后再用 `DRY_RUN=0` 执行。

需要 token 具备 **Zone → DNS → Edit** 权限（`Edit Cloudflare Workers`
模板不含该权限，需另行添加）。

运行方式见 `.github/workflows/fix-dns.yml` 的 dispatch 参数。
