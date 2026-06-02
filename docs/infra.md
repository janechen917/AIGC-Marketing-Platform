# 基础设施运维速查（infra）

本项目用 `docker compose` 启动 4 个容器：PostgreSQL / Redis / Qdrant / MinIO。
本文件是日常运维速查；架构与用途见 [`AI_GUIDE.md`](../AI_GUIDE.md)。

---

## 1. 启动 / 停止

```bash
docker compose up -d            # 后台启动全部
docker compose ps               # 查看状态
docker compose stop             # 停止但保留容器和数据
docker compose down             # 删除容器，保留数据
docker compose down -v          # 删除容器和命名卷（本项目不用命名卷，主要清理网络）
rm -rf docker-data/             # 彻底删除所有持久化数据
```

只启停某一个：
```bash
docker compose up -d postgres
docker compose restart redis
```

---

## 2. 查日志

```bash
docker compose logs -f postgres        # 实时跟随
docker compose logs --tail=100 redis   # 最后 100 行
docker compose logs                    # 全部容器
```

---

## 3. 连通性验证

```bash
# Postgres
docker compose exec postgres psql -U aigc -d aigc -c '\l'

# Redis
docker compose exec redis redis-cli ping        # 期望 PONG

# Qdrant
curl http://localhost:6333/collections           # JSON 响应

# MinIO（浏览器）
# 打开 http://localhost:9001
# 用户名/密码：minioadmin / minioadmin（或 .env 中配置）
```

---

## 4. 端口分配

| 端口 | 容器 | 用途 |
|---|---|---|
| 5432 | postgres | SQL 客户端连接 |
| 6379 | redis | Celery / 缓存 |
| 6333 | qdrant | HTTP API |
| 6334 | qdrant | gRPC（不常用） |
| 9000 | minio | S3 API（后端用） |
| 9001 | minio | Web 控制台（浏览器） |

被占用怎么办：改 `docker-compose.yml` 端口映射的**左侧数字**（如 `15432:5432`），同步改 `.env` 的 `DATABASE_URL`。

---

## 5. 数据持久化

所有数据都放在 `./docker-data/` 下，分子目录：

```
docker-data/
├── postgres/       Postgres 数据
├── redis/          Redis AOF
├── qdrant/         向量索引
└── minio/          对象存储
```

**该目录已在 `.gitignore` 排除，不会进 Git。**

备份某个组件：直接 `cp -a docker-data/postgres backup-pg-$(date +%F)`。

---

## 6. MinIO 初次使用

启动后需要手动创建一个 bucket：
1. 浏览器打开 http://localhost:9001
2. 登录 minioadmin / minioadmin
3. 左侧 **Buckets → Create Bucket** → 名字填 `aigc`（与 `.env` 的 `MINIO_BUCKET` 一致）
4. 后续 STEP 会改成代码自动创建

---

## 7. 常见问题

| 现象 | 原因 / 解决 |
|---|---|
| 启动报端口被占 | `lsof -i :5432` 找出占用进程；或改 compose 端口 |
| Postgres 拒绝连接 | 密码与 `.env` 不一致 → `docker compose down -v && rm -rf docker-data/postgres` 重置 |
| Codespaces 中无法从浏览器访问 9001 | 在 VS Code "PORTS" 面板把 9001 设为 Public |
| 磁盘不够 | `docker system prune -a` 清理旧镜像 |
| 想看容器内部 | `docker compose exec postgres sh` |

---

## 8. 重置全部数据（开发期常用）

```bash
docker compose down
rm -rf docker-data/
docker compose up -d
```
