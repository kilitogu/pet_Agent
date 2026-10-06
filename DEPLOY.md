# 部署指南

> 结论先说：**值得部署。** 面试官能直接点开用，和只能看你截图，是完全不同的说服力。
> 但线上环境和本机跑通是两件事，下面这 8 个坑一定要提前处理，否则交付当天会翻车。

---

## 一、最快路径：Docker Compose（推荐）

项目已经准备好全部配置文件，三步上线：

```bash
# 1) 准备配置
cp .env.example .env
vim .env            # 填 MYSQL_ROOT_PASSWORD / JWT_SECRET_KEY / DEEPSEEK_KEY / CORS_ORIGINS

# 2) 构建并启动（首次约 5-10 分钟，主要时间在装 torch）
docker compose up -d --build

# 3) 查看状态
docker compose ps
docker compose logs -f backend
```

打开 `http://<服务器公网IP>` 即可。**只有前端 80 端口对外暴露**，MySQL 与后端只在容器内网可见。

已包含的配置文件：

| 文件 | 作用 |
|---|---|
| `docker-compose.yml` | 编排 MySQL + 后端 + 前端(nginx)，含健康检查与数据卷 |
| `backend/Dockerfile` | Python 镜像；**先装 CPU 版 torch**，把镜像从 ~4GB 压到 ~1GB |
| `frontend/Dockerfile` | 多阶段构建：Node 打包 → nginx 托管静态产物 |
| `frontend/nginx.conf` | 反代 `/api`、`/uploads`，含 SSE 与上传的针对性配置 |
| `.env.example` | compose 需要的环境变量模板 |
| `backend/.dockerignore` | 防止把 `.env`、`.venv`、向量索引打进镜像 |

---

## 二、上线前必改的 8 个坑

### 1. SSE 流式输出被 nginx 缓冲掉（最容易踩）
nginx 默认会缓冲上游响应。不关掉缓冲，AI 回答会被**攒成一整段一次性吐出**，
前端"逐字打印"的效果直接消失，看起来就像没做流式。

`frontend/nginx.conf` 里已经处理：
```nginx
location /api/ {
    proxy_pass http://backend:8000;
    proxy_buffering off;      # ← 关键
    proxy_cache off;
    proxy_read_timeout 300s;
}
```

### 2. 上传图片返回 413
后端允许 100MB，nginx 默认只允许 1MB。已在配置里放大：
```nginx
client_max_body_size 110m;
```

### 3. 刷新子页面 404
前端是 history 路由（`/manager/home`），直接刷新时 nginx 找不到对应文件。必须回退：
```nginx
location / { try_files $uri $uri/ /index.html; }
```

### 4. 线上图片全部裂开（本项目已修）
原来 `Layout.vue / Home.vue / AI.vue` 里的图片地址兜底写死成 `http://127.0.0.1:8000`，
本机没问题，**一上线全班图片都裂**。

已改为**相对路径 + 反向代理**：
```js
const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')
```
开发走 vite proxy，线上走 nginx，两边行为一致。

### 5. 密钥泄露
- `.gitignore` 已忽略 `.env`、`!.env.example` 保留模板
- `backend/.dockerignore` 已排除 `.env`，不会打进镜像
- 不要在代码里写字面量密钥，不要在群里发含密钥的截图

### 6. 数据没持久化，重建容器就全没了
`uploads/`（上传的封面）、`data/chroma/`（向量索引）、MySQL 数据都必须挂卷。
`docker-compose.yml` 里已挂好，并把 HuggingFace 缓存也挂上，避免每次重建重新下载 embedding 模型。

### 7. CORS 白名单漏了线上域名
后端 `CORS_ORIGINS` 默认只有 `http://localhost:5173`。
线上要补上真实访问地址，否则前端请求会被浏览器拦掉：
```
CORS_ORIGINS=http://your-domain.com,http://your-server-ip
```

### 8. DeepSeek Key 放公网 = 有人替你花钱
这是**最需要认真对待的一条**。公开演示站如果不设防：
- 别人可以无限刷你的 AI 接口，直接消耗你的额度
- 抓包拿到接口后可以批量调用

建议至少做一层：
1. **限制注册**：演示站可以关闭注册入口，只留一个演示账号；
2. **加限流**：在 nginx 或后端对 `/api/ai/chat/stream` 做 IP 限流（如每分钟 10 次）；
3. **控制额度**：给 API Key 设置消费上限，别绑大额账号；
4. **兜底**：演示用 `deepseek-chat`，不要用更贵的模型。

---

## 三、裸机部署（不想用 Docker 时）

```bash
# 后端
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000     # 用 systemd 常驻

# 前端
cd frontend
npm ci && npm run build                                # 产物在 dist/
# 把 dist/ 交给 nginx 托管，复用上面的 nginx.conf（把 backend:8000 改成 127.0.0.1:8000）
```

需要额外自己处理：MySQL 安装、Python 进程守护（systemd/supervisor）、证书。

---

## 四、一定要配 HTTPS

浏览器在非 HTTPS 下会限制部分能力，微信内打开也会拦。用 Let's Encrypt 免费证书：

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```
配好后记得同步更新 `.env` 里的 `CORS_ORIGINS` 为 `https://your-domain.com`。

---

## 五、上线检查清单

- [ ] `.env` 已填全，且**没有被提交到 git**（`git status` 里看不到）
- [ ] `CORS_ORIGINS` 包含线上真实域名
- [ ] 首页能正常登录（试一下新注册的普通用户，应能看到「总览 / 分类管理 / AI 助手」）
- [ ] AI 助手问一句「现在有哪些待领养的猫」，确认**逐字输出**且出现工具调用轨迹
- [ ] 上传一张宠物封面，确认图片能显示（验证 `/uploads` 反代与 `client_max_body_size`）
- [ ] 刷新 `/manager/pet` 页面，不出现 404
- [ ] `docker compose restart` 后，宠物数据和上传文件仍在（验证卷）
- [ ] AI 接口做了限流或关闭了公开注册

---

## 六、给面试演示的加分项

1. **录 30 秒屏录**：提问 → 看到工具调用轨迹 → 逐字输出答案。面试时直接播放，比口头描述有力得多。
2. **README 里放架构图与踩坑记录**（本项目 README 已含），面试官扫一眼就知道你理解了链路。
3. **主动讲清成本控制**：能说出"我给演示站加了限流、并把 Key 设了消费上限"，
   比单纯说"我部署了"要专业得多。
