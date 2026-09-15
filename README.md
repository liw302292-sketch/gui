# 报价引擎 Quote Engine

> 面向非标行业的 AI 报价基础设施。第一行业版本：**广告标识 / 广告制作**。

客户发一张图、一段微信聊天截图，系统自动识别需求、匹配企业自己的产品价格与报价规则，
在几十秒内生成一份专业报价单，并生成可分享的公开链接。

**核心架构铁律：AI 负责“理解和提取”，系统负责“计算和执行”。**
最终价格永远由后端规则引擎计算，AI 不能决定任何商业价格。

---

## 一、5 分钟跑起来

### 方式 A：Docker 一键启动（推荐）

```bash
# 1. 准备环境变量
cp .env.example .env          # Windows: copy .env.example .env

# 2. 启动全部服务（postgres + redis + backend + frontend + nginx）
docker compose up -d --build

# 3. 查看启动日志（首次会自动执行数据库迁移 + 灌入演示数据）
docker compose logs -f backend
```

打开浏览器：

| 地址 | 说明 |
| --- | --- |
| http://localhost | 官网（Nginx 入口） |
| http://localhost/app | 企业后台 |
| http://localhost/admin | 系统管理员后台 |
| http://localhost:8000/api/docs | 后端 Swagger API 文档 |

### 方式 B：本地开发（不需要 Docker，也不需要数据库）

没有配置 `DATABASE_URL` 时会自动使用 SQLite，因此本地零依赖即可运行。

```bash
# ---------- 后端 ----------
cd backend
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python seed.py --reset            # 建表 + 灌入演示数据（含 23 个产品、10 个客户、20 份报价）
uvicorn app.main:app --reload --port 8000

# ---------- 前端（新开一个终端）----------
cd frontend
npm install
npm run dev                       # http://localhost:3000
```

前端通过同源代理 `/api/backend/*` 访问后端（见 `frontend/next.config.ts`），
因此浏览器端只接触 HttpOnly Cookie，拿不到也不需要 JWT。

---

## 二、Demo 账号

系统初始化后自动创建以下账号（可在 `.env` 中修改）：

| 角色 | 账号 | 密码 | 说明 |
| --- | --- | --- | --- |
| 演示企业 | `demo@example.com` | `Demo123456!` | 星辰广告制作，含完整演示数据 |
| 平台管理员 | `admin@example.com` | `Admin123456!` | 可进入 `/admin` 查看全平台数据 |

演示企业自带：**23 个产品**、**10 个产品分类**、**10 个客户**、**20 份不同状态的报价**、
**5 条跟进记录**、**AI 调用与成本历史**、**免费/专业/企业三档套餐**。

> 生产环境首次启动时管理员会被标记为「必须修改密码」，登录后会强制跳转修改。

---

## 三、3 分钟走完一次真实报价（验收路径）

1. 用演示账号登录 → 进入工作台（今日报价 / 待跟进 / 本月报价金额 / 本月成交金额 / 转化漏斗）
2. 点击 **新建报价**
3. 上传一张微信截图，或直接粘贴：
   > 帮我做一个10米门头，铝塑板底，12个发光字，月底安装
4. 系统进入「AI 正在理解客户需求」：读取图片 → 分析文本 → 识别产品 → 提取参数 → 检查缺失项
5. 查看识别结果：门头 10m、发光字 12 个、安装、交期月底；同时提示缺少 **门头高度 / 安装地址 / 发光字尺寸**
6. 人工补全高度 → 点击 **确认并开始报价**
7. 报价工作台显示：明细、成本构成、每一行的计算公式、经济版 / 标准版 / 高级版三档方案
8. 点击 **发送给客户** 生成随机 token 公开链接 → 复制链接到新窗口打开（模拟客户）
9. 回到后台：报价状态自动变为 **已查看**，并生成站内通知；可继续添加跟进记录

---

## 四、DeepSeek 配置

AI 层完全独立在 `backend/app/services/ai/`，业务代码不会直接调用 DeepSeek；
换模型、换供应商、切换 mock/real 都只改环境变量。

```env
# mock：不需要任何 Key，返回确定性演示数据（默认）
# real：真实调用 DeepSeek
AI_MODE=mock

DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_TEXT_MODEL=deepseek-v4-flash
DEEPSEEK_REASONING_MODEL=deepseek-v4-pro
DEEPSEEK_VISION_MODEL=deepseek-v4-flash-vision-exp
```

- 配置位置：项目根目录 `.env`（后端通过 `pydantic-settings` 读取）
- **API Key 只存在于后端环境变量中，永远不会出现在前端代码里**
- 未填写 Key 时系统自动进入 Mock 模式，整个项目依然可以完整跑通
- JSON 解析失败会自动重试一次；仍然失败则保留原始响应、标记任务失败，允许人工编辑识别结果

模型职责分工（自动选择，无需手工指定）：

| 任务 | 模型 |
| --- | --- |
| 文字需求识别、缺失补问、回复文案 | `DEEPSEEK_TEXT_MODEL` |
| 报价解释、区间建议（复杂分析） | `DEEPSEEK_REASONING_MODEL` |
| 截图 / 图片识别 | `DEEPSEEK_VISION_MODEL` |

---

## 五、数据库初始化 / 迁移

```bash
# 执行迁移（生产环境必须执行）
cd backend && alembic upgrade head

# 灌入初始化数据（幂等，已存在则跳过）
python seed.py

# 重置演示数据库并重新灌入（会清空数据！）
python seed.py --reset

# 只创建套餐与管理员，不创建演示企业
python seed.py --no-demo
```

回滚迁移：

```bash
alembic downgrade -1
```

---

## 六、环境变量

完整清单见 [`.env.example`](.env.example)，关键项：

| 变量 | 说明 |
| --- | --- |
| `DATABASE_URL` | 留空 → 自动使用 SQLite；Docker 中为 PostgreSQL |
| `REDIS_URL` | 留空或不可用时自动降级为进程内缓存/限流 |
| `APP_SECRET_KEY` | JWT 签名密钥，**生产必须修改** |
| `AI_MODE` | `mock` / `real` |
| `STORAGE_BACKEND` | `local`（默认，通过鉴权接口访问）/ `s3` |
| `PAYMENT_PROVIDER` | `mock`（默认，开发环境自动完成支付） |
| `RATE_LIMIT_PER_MINUTE` / `AI_RATE_LIMIT_PER_MINUTE` | 限流阈值 |

---

## 七、项目结构

```
报价引擎/
├── docker-compose.yml          # postgres + redis + backend + frontend + nginx
├── .env.example                # 环境变量示例
├── Makefile                    # make up / seed / test / reset-demo
├── nginx/nginx.conf            # 反向代理配置（含独立域名示例）
├── docs/DEPLOYMENT.md          # 部署与域名说明
├── backend/                    # FastAPI + SQLAlchemy + Alembic
│   ├── app/
│   │   ├── core/               # 配置、数据库、安全、错误、限流、存储
│   │   ├── models/             # 23 张业务表（全部带 company_id）
│   │   ├── schemas/            # Pydantic 请求/响应模型
│   │   ├── api/v1/             # auth/company/products/price-rules/quotes/...
│   │   ├── services/
│   │   │   ├── pricing/        # ★ 规则引擎（与 AI 完全解耦）
│   │   │   │   ├── pricing_engine.py
│   │   │   │   ├── formula_engine.py
│   │   │   │   ├── rule_matcher.py
│   │   │   │   └── profit_calculator.py
│   │   │   ├── ai/             # ★ AI 层（业务代码只与这里交互）
│   │   │   │   ├── deepseek_client.py
│   │   │   │   ├── quotation_ai.py
│   │   │   │   ├── vision_parser.py
│   │   │   │   ├── prompt_manager.py
│   │   │   │   └── usage_tracker.py
│   │   │   └── ...             # 报价、PDF、文件、统计、套餐、审计
│   │   ├── industry/           # ★ 行业模板（广告标识 = 第一套模板）
│   │   ├── prompts/            # 集中管理 5 个 Prompt
│   │   └── main.py
│   ├── alembic/                # 数据库迁移（含 initial schema）
│   ├── tests/                  # 69 个自动化测试
│   └── seed.py                 # 初始化 + 演示数据
└── frontend/                   # Next.js 16 + TypeScript + Tailwind 4
    └── src/
        ├── app/                # 官网 / 后台 / 公开报价 / 管理员后台
        ├── components/         # 设计系统（按钮/表格/弹窗/Badge/空状态/图表…）
        ├── lib/                # API 客户端与类型定义
        └── hooks/
```

---

## 八、报价规则引擎

价格 = `产品 + 数量 + 尺寸 + 单位 + 成本 + 损耗 + 人工 + 运输 + 其他费用 + 利润规则`，
全部由 `backend/app/services/pricing/` 计算，每一步都保留明细。

支持的计价方式：

| 类型 | 公式 |
| --- | --- |
| 固定单价 | 数量 × 单价 |
| 面积 | 宽 × 高 × 数量 × 单价 |
| 体积 | 长 × 宽 × 高 × 数量 × 单价 |
| 重量 | 重量 × 单价 |
| 成本加成 | 成本 × (1 + 加价率) |
| 毛利率 | 售价 = 成本 / (1 - 毛利率) |
| 损耗 | 材料成本 × 损耗率 |
| 人工 | 固定人工费，或 面积 / 数量 × 人工单价 |
| 运输 | 固定运输费，或按公里/按趟 |
| 条件价格 | 例如面积 > 20㎡ 自动使用批发价 |

计价方式优先级：**需求显式指定 > 价格规则 > 产品设置 > 按尺寸推断**，
并始终以「保底毛利率」兜底。每个报价项都会保存可读的计算过程，例如：

```
计价数量：10m × 1.55m × 1 = 15.5 平方米；单价：280 元/平方米；
材料成本 2247.5 = 15.5 × 145；损耗 134.85 = 材料成本 × 6%；
人工：固定人工 0 + 55/平方米 × 15.5 = 852.5；总成本 3234.85；
定价依据：计价数量 × 单价；保底毛利率 28% → 4492.85；取整（10）+7.15；最终售价 4500
```

报价取整方式（企业可配置）：精确到分 / 元 / 10 元 / 100 元 / 心理价（10857 → 10880）。

三档方案（经济版 / 标准版 / 高级版）通过「售价系数 + 利润率调整」产生真实差异，
客户看到的是方案，成本与利润率只有企业自己可见。

---

## 九、行业模板（换行业不换引擎）

底层是「报价引擎 + 行业模板」，广告只是第一套模板：

| 行业 | 状态 |
| --- | --- |
| 广告标识 `advertising` | ✅ 已上线（门头/发光字/灯箱/标牌/喷绘/写真/展架/导视/安装/运输） |
| 门窗 `doors_windows` | 🕒 即将上线（占位，第一版不开放） |
| 包装印刷 `packaging` | 🕒 即将上线 |
| 机械加工 `machining` | 🕒 即将上线 |

新增行业只需在 `backend/app/industry/templates/` 增加一个模板文件并注册：
产品分类、产品、字段、公式、规则、报价模板、Prompt 全部随模板走，核心 SaaS 代码零改动。

---

## 十、测试

```bash
cd backend
pytest -q          # 69 个测试全部通过
```

覆盖范围：注册、登录、企业创建、产品与价格规则、规则引擎计算（固定/面积/体积/重量/成本加成/毛利率/取整）、
创建报价、版本与审计、生成公开链接、客户查看追踪、跟进、企业数据隔离、AI mock、JSON 解析容错、
套餐与 mock 支付、管理员后台权限、行业模板。

前端类型检查与构建：

```bash
cd frontend
npm run typecheck
npm run build
```

---

## 十一、当前已完成 / 明确未实现

**已完成（真实可用，非演示页面）**

- 官网 6 个页面（首页 8 屏 / 功能 / 价格 / 演示 / 登录 / 注册），含 SEO、OG、sitemap、robots
- 邮箱或手机号注册 → 自动创建企业 / 用户 / 成员，并按行业模板预置产品价格库与报价模板
- 企业后台：工作台、报价、客户、产品与价格（分类 / Excel 导入）、价格规则、报价模板、跟进、数据、AI 助手、企业设置、套餐
- AI 需求识别（截图 / 图片 / PDF / Excel / 文字）、缺失信息补问、客户回复（专业 / 简洁 / 成交）、报价解释、区间建议
- 规则引擎计算、三档方案、报价版本、审计日志、报价单 PDF、公开链接（有效期 + 访问密码）、查看行为追踪
- 客户管理与跟进（状态、下次跟进时间、今日待跟进提醒）、转化漏斗与经营数据
- 管理员后台：平台总览、企业、用户、套餐、订单、订阅、AI 使用与成本、报价统计、日志与异常、系统设置
- 套餐 / 订单 / 订阅（数据库驱动）+ 支付抽象层（开发环境 mock 支付自动完成）
- 多租户隔离、权限校验、限流、文件校验与隔离存储、JWT + HttpOnly Cookie、CSRF 来源校验
- Docker Compose 一键部署、Alembic 初始迁移、Seed 数据、完整 README 与部署文档

**明确未实现（不假装完成）**

- 微信支付 / 支付宝真实对接（当前为 mock + 抽象层，接入后订单与订阅逻辑无需修改）
- 微信 OAuth 登录（`users` 表已预留 `wechat_openid` / `wechat_unionid` 字段）
- 短信 / 邮件 / 微信通知推送（当前只有站内通知，接口已预留）
- 多人协作的实际邀请流程（数据模型、套餐成员上限已就绪，邀请 UI 未开放）
- 门窗 / 包装 / 机械加工行业模板（仅占位，第一版只开放广告标识）
- Excel 导入的字段映射可视化配置（当前按列名自动识别）
- 报价单多版式模板（当前提供配色、条款、页脚与三档开关）

---

## 十二、常见问题

**Q：本地没有 Docker 能跑吗？**
能。不配置 `DATABASE_URL` 会自动使用 SQLite；Redis 未启动会自动降级为进程内限流与缓存。

**Q：PDF 生成依赖什么？**
优先使用 WeasyPrint（Docker 镜像已安装 Pango 与 Noto CJK 字体，排版最精细）；
在没有系统库的机器（如 Windows 本地）自动降级为 fpdf2 + 系统中文字体；
再不行则返回打印用 HTML，由浏览器「打印为 PDF」。

**Q：数据会不会泄露给 AI？**
送给 AI 的只有客户需求内容与企业产品分类名称，不含成本、报价历史、客户隐私；
公开报价页与 PDF 也只输出对客内容，永远不包含成本、利润率、毛利。

**Q：怎么换成我自己的价格？**
「产品与价格」页面直接修改或 Excel 导入（列名：分类、产品名称、单位、计价方式、成本、默认报价、损耗率、人工单价、最低利润率）。

---

## 十三、下一步建议

1. **接真实支付**：把 `PAYMENT_PROVIDER` 切到微信支付/支付宝，在 `services/plan_service.py` 的 `pay_order` 中接入回调即可。
2. **用真实价格替换演示数据**：先导入 20-50 个高频产品，规则引擎立刻可用。
3. **接第二个行业模板**：按门窗或包装复制一个模板文件，验证「换行业不换引擎」的扩展路径。
4. **上线前加固**：修改 `APP_SECRET_KEY`、接入对象存储（S3/OSS）、开启 HTTPS、把 Redis 与 PostgreSQL 换成云托管实例并配置备份。
5. **埋点与转化分析**：在公开报价页增加「客户停留时长 / 是否点击确认」埋点，进一步优化成交率。

