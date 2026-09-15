# 部署与域名说明

## 一、Docker Compose 服务拓扑

```
                        ┌──────────────┐
   浏览器 ──────────────►│    Nginx     │ :80
                        └──────┬───────┘
                 /  /app /admin │ /api
                    ┌───────────┴────────────┐
                    ▼                        ▼
             ┌─────────────┐          ┌─────────────┐
             │  frontend   │  rewrites│   backend   │ :8000
             │  Next.js    │ ────────►│  FastAPI    │
             └─────────────┘  /api/   └──────┬──────┘
                                            │
                              ┌─────────────┴─────────────┐
                              ▼                           ▼
                      ┌─────────────┐             ┌─────────────┐
                      │ PostgreSQL  │             │   Redis     │
                      └─────────────┘             └─────────────┘
```

## 二、启动步骤

```bash
cp .env.example .env
# 修改 APP_SECRET_KEY / POSTGRES_PASSWORD / DEEPSEEK_API_KEY
docker compose up -d --build
docker compose logs -f backend     # 首次会自动 alembic upgrade head + seed
```

内置命令：

| 命令 | 作用 |
| --- | --- |
| `make up` | 构建并启动全部服务 |
| `make logs` | 查看日志 |
| `make migrate` | 执行数据库迁移 |
| `make seed` | 灌入演示数据（幂等） |
| `make reset-demo` | 重置演示数据库 |
| `make test` | 在容器内运行测试 |

## 三、域名结构（生产推荐）

推荐按业务拆分域名，Nginx 中已给出示例配置（`nginx/nginx.conf`）：

| 域名 | 用途 | 代理到 |
| --- | --- | --- |
| `www.example.com` | 官网 | frontend |
| `app.example.com` | 企业后台 | frontend |
| `quote.example.com` | 公开报价页 | frontend |
| `api.example.com` | REST API | backend |

开发阶段可以先全部走同域名（默认配置即可），上线后再拆分。

**拆分域名时需要同步调整：**

1. `APP_URL` 改成公开报价页域名（生成的公开链接以此为准）
2. 前端 `BACKEND_INTERNAL_URL` 指向 `api` 服务
3. `.env` 中 `CORS_ORIGINS` 增加所有前端域名
4. 后端 Cookie 在生产环境（`APP_ENV=production`）自动开启 `Secure`

## 四、HTTPS

推荐在 Nginx 前置 Certbot：

```bash
certbot --nginx -d www.example.com -d app.example.com -d quote.example.com -d api.example.com
```

## 五、生产检查清单

- [ ] `APP_ENV=production`（关闭开发环境自动建表，强制使用迁移）
- [ ] `APP_SECRET_KEY` 为长随机串，且不提交到仓库
- [ ] `POSTGRES_PASSWORD` 为强密码，数据库不对公网暴露
- [ ] `DEEPSEEK_API_KEY` 仅配置在后端 `.env`，确认前端构建产物中不含 Key
- [ ] `STORAGE_BACKEND=s3`，配置对象存储（MinIO / 阿里云 OSS / 腾讯云 COS）
- [ ] `AI_MODE=real`，并核对 `AI_PRICE_*` 与 DeepSeek 官方峰谷价保持一致
- [ ] 域名与 HTTPS 证书就绪，`CORS_ORIGINS` 已更新
- [ ] 定期备份 PostgreSQL 与对象存储
- [ ] 首次登录管理员账号后立即修改初始密码

## 六、常见运维操作

```bash
# 备份数据库
docker compose exec postgres pg_dump -U quote quote_engine > backup_$(date +%F).sql

# 恢复数据库
docker compose exec -T postgres psql -U quote quote_engine < backup.sql

# 查看后端日志（含 AI 调用与错误日志）
docker compose logs -f backend

# 重建某个服务
docker compose up -d --build backend

# 完全停止并删除数据卷（谨慎）
docker compose down -v
```

## 七、打包

- 后端镜像：`backend/Dockerfile`（Python 3.12 + WeasyPrint + Noto CJK 字体）
- 前端镜像：`frontend/Dockerfile`（Node 20 多阶段构建，standalone 产物，非 root 用户运行）
- Nginx 配置：`nginx/nginx.conf`（由 Compose 挂载，可直接替换为你的域名配置）

