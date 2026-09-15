"use client";

import {
  BadgeCheck,
  Bell,
  Building2,
  Calculator,
  Database,
  FileText,
  FolderLock,
  Gauge,
  Layers,
  LineChart,
  Lock,
  MessageSquare,
  ScanLine,
  Server,
  ShieldCheck,
  Sparkles,
  Users,
  Zap,
} from "lucide-react";
import Link from "next/link";

import { SiteFooter, SiteHeader } from "@/components/marketing/site-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

const GROUPS = [
  {
    badge: "需求识别",
    title: "把微信里的碎碎念，变成一张结构化的需求单",
    desc: "AI 只负责“看懂”与“提取”。它不会给你定价，也从来不会自己编数字。",
    items: [
      { icon: ScanLine, title: "微信截图 / 图片识别", desc: "直接上传客户发来的截图，自动识别产品、尺寸、数量与备注。" },
      { icon: FileText, title: "PDF / Excel / 文字", desc: "PDF 抽取文字、Excel 读取表格、直接粘贴聊天记录都可以。" },
      { icon: MessageSquare, title: "缺失信息自动补问", desc: "缺高度、缺安装地址、缺交期，系统直接生成可以发给客户的问题。" },
      { icon: Sparkles, title: "结果可人工修改", desc: "AI 输出永远是草稿。宽度、高度、数量、材质、工艺都能改，改完重新算。" },
    ],
  },
  {
    badge: "价格与规则",
    title: "价格永远由你自己的规则算，AI 碰不到钱",
    desc: "成本、损耗、人工、运输、利润率全部在后台规则引擎里计算，每一分钱都可追溯。",
    items: [
      { icon: Calculator, title: "四种计价方式", desc: "固定单价、面积、体积、重量，按产品和分类分别设置。" },
      { icon: Layers, title: "成本加成与毛利率", desc: "成本 × (1 + 加价率)，或成本 / (1 - 毛利率)，也可以同时设保底毛利率。" },
      { icon: Gauge, title: "损耗 · 人工 · 运输", desc: "损耗率、固定人工、按平方人工、运输费、其他费用逐项计入成本。" },
      { icon: Database, title: "条件价格与阶梯价", desc: "例如面积大于 20㎡ 自动使用批发价，数量超过 20 个自动给批量价。" },
    ],
  },
  {
    badge: "报价与出单",
    title: "三档方案，一次给出客户能选的价格",
    desc: "经济版 / 标准版 / 高级版自动生成，客户看到方案，老板看到完整成本。",
    items: [
      { icon: FileText, title: "专业报价单", desc: "企业 Logo、报价编号、有效期、付款条款、服务条款自动带上，支持 PDF 下载。" },
      { icon: Lock, title: "公开链接与访问密码", desc: "随机 token 链接，可设有效期与访问密码，不暴露任何数据库 ID。" },
      { icon: ShieldCheck, title: "客户端零成本泄露", desc: "客户页面只显示售价与规格，成本、利润率、毛利只对企业内部可见。" },
      { icon: Sparkles, title: "版本与审计", desc: "每次改价自动生成新版本，谁改的、什么时候改、改前改后全部留痕。" },
    ],
  },
  {
    badge: "客户与跟进",
    title: "客户看没看、看了几次，你比客户还清楚",
    desc: "不做复杂 CRM，只保留真正影响成交的那几件事。",
    items: [
      { icon: Bell, title: "查看行为追踪", desc: "首次打开时间、最近打开时间、打开次数、设备类型全部记录。" },
      { icon: Users, title: "客户档案与历史", desc: "一个客户的所有报价、跟进记录、活动记录集中在一个页面。" },
      { icon: LineChart, title: "转化漏斗", desc: "报价 → 查看 → 跟进 → 成交，哪一步掉客户一眼就能看到。" },
      { icon: Zap, title: "今日待跟进提醒", desc: "工作台直接告诉你今天有几个客户需要联系。" },
    ],
  },
  {
    badge: "企业级",
    title: "能交付给客户看的安全与可控",
    desc: "多租户隔离、额度控制、权限管理、日志审计，第一天就做好。",
    items: [
      { icon: Building2, title: "严格多租户隔离", desc: "所有业务数据都带企业标识，接口层强制校验，绝无跨企业读取。" },
      { icon: Gauge, title: "AI 额度与用量统计", desc: "按企业、按模型、按任务统计调用量与成本，用完提示升级套餐。" },
      { icon: FolderLock, title: "文件安全", desc: "文件类型校验、大小限制、文件名清洗、路径隔离，真实路径永不暴露。" },
      { icon: Server, title: "可私有部署", desc: "Docker Compose 一键启动，支持换成自己的服务器与对象存储。" },
    ],
  },
];

const AI_BOUNDARY = {
  can: [
    "理解客户自然语言",
    "识别微信截图与图片",
    "提取尺寸、数量、产品、材质、工艺",
    "发现缺失信息并生成补问",
    "生成客户回复与报价解释",
    "根据历史成交给出建议区间",
  ],
  cannot: [
    "决定最终价格",
    "决定成本与利润率",
    "执行任何企业计费逻辑",
    "存储订单金额",
    "计算支付金额",
  ],
};

export default function FeaturesPage() {
  return (
    <div className="bg-background">
      <SiteHeader />

      <section className="border-b border-line bg-surface py-16">
        <div className="container-page">
          <Badge tone="accent">功能</Badge>
          <h1 className="mt-4 max-w-3xl text-[34px] font-semibold leading-tight tracking-tight text-ink sm:text-[40px]">
            一套真正能跑完报价闭环的系统
          </h1>
          <p className="mt-4 max-w-2xl text-[15.5px] leading-relaxed text-muted">
            不是报价表模板，也不是只有界面的 Demo。上传需求、计算价格、生成报价单、客户查看、跟进成交，
            每一步都落到真实数据和真实数据库里。
          </p>
        </div>
      </section>

      {GROUPS.map((group, index) => (
        <section key={group.badge} className={index % 2 === 1 ? "border-b border-line bg-surface py-16" : "py-16"}>
          <div className="container-page">
            <Badge tone="accent">{group.badge}</Badge>
            <h2 className="mt-4 max-w-2xl text-[26px] font-semibold leading-snug tracking-tight text-ink">
              {group.title}
            </h2>
            <p className="mt-3 max-w-2xl text-[14.5px] leading-relaxed text-muted">{group.desc}</p>

            <div className="mt-10 grid gap-4 md:grid-cols-2">
              {group.items.map((item) => {
                const Icon = item.icon;
                return (
                  <div key={item.title} className="card p-5">
                    <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent-soft text-accent">
                      <Icon className="h-4 w-4" />
                    </span>
                    <h3 className="mt-4 text-[15px] font-semibold text-ink">{item.title}</h3>
                    <p className="mt-1.5 text-[13px] leading-relaxed text-muted">{item.desc}</p>
                  </div>
                );
              })}
            </div>
          </div>
        </section>
      ))}

      <section className="border-y border-line bg-surface py-16">
        <div className="container-page">
          <div className="mx-auto max-w-2xl text-center">
            <Badge tone="dark">架构铁律</Badge>
            <h2 className="mt-4 text-[26px] font-semibold leading-snug tracking-tight text-ink">
              为什么报价引擎不会算错价
            </h2>
            <p className="mt-3 text-[14.5px] leading-relaxed text-muted">
              我们把 AI 的能力和商业计算彻底分开：AI 负责理解，程序负责计算和执行。
            </p>
          </div>

          <div className="mt-10 grid gap-5 lg:grid-cols-2">
            <div className="rounded-[18px] border border-[#c8ecd7] bg-success-soft/50 p-6">
              <h3 className="flex items-center gap-2 text-[15px] font-semibold text-[#0b6b36]">
                <Sparkles className="h-4 w-4" />
                AI 负责
              </h3>
              <ul className="mt-4 space-y-2.5">
                {AI_BOUNDARY.can.map((item) => (
                  <li key={item} className="flex items-start gap-2.5 text-[13.5px] text-ink-soft">
                    <BadgeCheck className="mt-0.5 h-4 w-4 shrink-0 text-success" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            <div className="rounded-[18px] border border-[#f8d3d3] bg-danger-soft/50 p-6">
              <h3 className="flex items-center gap-2 text-[15px] font-semibold text-[#8f1d1d]">
                <Lock className="h-4 w-4" />
                AI 不负责
              </h3>
              <ul className="mt-4 space-y-2.5">
                {AI_BOUNDARY.cannot.map((item) => (
                  <li key={item} className="flex items-start gap-2.5 text-[13.5px] text-ink-soft">
                    <span className="mt-[7px] h-1.5 w-1.5 shrink-0 rounded-full bg-danger/70" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      <section className="py-16">
        <div className="container-page flex flex-wrap items-center justify-between gap-6 rounded-[20px] border border-line bg-surface p-8">
          <div>
            <h2 className="text-[22px] font-semibold tracking-tight text-ink">想先看一眼真实界面？</h2>
            <p className="mt-2 text-[14px] text-muted">用演示账号登录，价格库、20 份报价、客户跟进数据都已经准备好。</p>
          </div>
          <div className="flex gap-3">
            <Link href="/demo">
              <Button variant="secondary">查看演示</Button>
            </Link>
            <Link href="/register">
              <Button>免费开始报价</Button>
            </Link>
          </div>
        </div>
      </section>

      <SiteFooter />
    </div>
  );
}

