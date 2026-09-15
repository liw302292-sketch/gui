"use client";

import {
  ArrowRight,
  BadgeCheck,
  Bell,
  Calculator,
  ClipboardList,
  Clock,
  FileSpreadsheet,
  FileText,
  Layers,
  LineChart,
  MessageSquare,
  Package,
  Send,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  Truck,
  Users,
  Zap,
} from "lucide-react";
import Link from "next/link";

import { HeroDemo } from "@/components/marketing/hero-demo";
import { MockChat, MockDashboard, MockQuotation, MockStructured, MockWorkbench } from "@/components/marketing/landing-mocks";
import { SiteFooter, SiteHeader } from "@/components/marketing/site-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const PAINS = [
  {
    icon: MessageSquare,
    title: "微信需求零散",
    lines: ["“10 米门头”“12 个发光字”散落在几十条聊天里", "信息反复确认，漏一项就要重新算一次"],
  },
  {
    icon: FileSpreadsheet,
    title: "Excel 重复计算",
    lines: ["面积、损耗、人工、运输每次都要手敲", "改一个尺寸，整张表全部重算"],
  },
  {
    icon: FileText,
    title: "报价单重复制作",
    lines: ["每次都要复制旧报价单、改字号、改金额", "发出去还是截图或手打，不够专业"],
  },
];

const STEPS = [
  {
    step: "01",
    icon: Sparkles,
    title: "识别",
    desc: "上传微信截图、图片或粘贴文字，AI 自动提取产品、尺寸、数量、安装与交期。",
    points: ["截图 / 图片 / PDF / Excel / 文字", "缺什么信息自动列出来", "识别结果随时可人工修改"],
  },
  {
    step: "02",
    icon: Calculator,
    title: "计算",
    desc: "用你自己的价格库和规则引擎计算成本、损耗、人工、运输与利润，AI 不会碰价格。",
    points: ["面积 / 固定 / 成本加成 / 毛利率", "条件价格：大于 20㎡ 用批发价", "每一项都能追溯「为什么是这个价」"],
  },
  {
    step: "03",
    icon: Send,
    title: "出单",
    desc: "一键生成专业报价单，支持经济版 / 标准版 / 高级版三档方案，可下载 PDF 或分享链接。",
    points: ["企业 Logo 与条款自动带上", "公开链接可设有效期与访问密码", "客户看不到你的成本与利润"],
  },
  {
    step: "04",
    icon: TrendingUp,
    title: "跟进",
    desc: "客户是否打开、看了几次、用什么设备，后台全都看得到，谁该跟进一目了然。",
    points: ["已查看 / 待跟进 / 已成交自动流转", "今日待跟进自动提醒", "AI 帮你写回复与解释"],
  },
];

const PRICE_LIBRARY = [
  { name: "门头", desc: "铝塑板 / 不锈钢 / 亚克力 / 烤漆", unit: "按平方米" },
  { name: "发光字", desc: "不锈钢 / 亚克力 / PVC / 树脂", unit: "按个" },
  { name: "灯箱", desc: "LED / 超薄 / 拉布 / 吸塑", unit: "按个 · 按平方" },
  { name: "标牌", desc: "亚克力 / 不锈钢 / PVC", unit: "按块" },
  { name: "喷绘", desc: "喷绘布 / UV 打印", unit: "按平方米" },
  { name: "写真", desc: "高清写真 / 覆膜", unit: "按平方米" },
  { name: "展架", desc: "X 展架 / 易拉宝 / 桁架", unit: "按套" },
  { name: "导视", desc: "楼层导视 / 科室牌", unit: "按块" },
  { name: "安装", desc: "常规安装 / 高空安装", unit: "按项" },
  { name: "运输", desc: "市区 / 跨区运输", unit: "按车 · 按公里" },
];

const INDUSTRIES = [
  { name: "广告标识", status: "已上线", active: true, desc: "门头、发光字、灯箱、标牌、喷绘写真、安装运输" },
  { name: "门窗", status: "即将上线", active: false, desc: "按尺寸与型材报价" },
  { name: "包装印刷", status: "即将上线", active: false, desc: "按数量与工艺报价" },
  { name: "机械加工", status: "即将上线", active: false, desc: "按材料与工时报价" },
];

const PLANS = [
  {
    code: "free",
    name: "免费",
    price: "0",
    cycle: "永久免费",
    desc: "先把报价这件事跑起来",
    features: ["每月 20 份报价", "每月 100 次 AI 识别", "产品价格库", "公开报价链接", "基础数据统计"],
    cta: "免费开始报价",
    highlight: false,
  },
  {
    code: "pro",
    name: "专业",
    price: "399",
    cycle: "/ 年",
    desc: "给每天都在报价的老板",
    features: [
      "不限报价数量",
      "每月 2000 次 AI 识别",
      "三档方案（经济/标准/高级）",
      "自定义报价单与条款",
      "客户跟进与转化统计",
      "3 个成员账号",
    ],
    cta: "开始专业版",
    highlight: true,
  },
  {
    code: "enterprise",
    name: "企业",
    price: "999-1999",
    cycle: "/ 年",
    desc: "多门店、多业务员的团队",
    features: [
      "不限报价数量",
      "每月 20000 次 AI 识别",
      "20 个成员账号",
      "开放 API",
      "优先技术支持",
      "私有部署方案",
    ],
    cta: "开始企业版",
    highlight: false,
  },
];

export default function LandingPage() {
  return (
    <div className="bg-background">
      <SiteHeader />

      <section className="relative overflow-hidden">
        <div className="pointer-events-none absolute inset-0 grid-backdrop opacity-70 [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_40%,transparent_100%)]" />
        <div className="pointer-events-none absolute -top-32 left-1/2 h-[420px] w-[820px] -translate-x-1/2 rounded-full bg-gradient-to-b from-accent/12 to-transparent blur-3xl" />

        <div className="container-page relative grid items-center gap-12 pb-20 pt-16 lg:grid-cols-[1.05fr_1fr] lg:gap-16 lg:pb-24 lg:pt-24">
          <div className="animate-[fade-up_0.6s_cubic-bezier(0.16,1,0.3,1)_both]">
            <div className="inline-flex items-center gap-2 rounded-full border border-line bg-surface px-3 py-1.5 text-[12.5px] text-ink-soft shadow-[var(--shadow-subtle)]">
              <span className="flex h-4 w-4 items-center justify-center rounded-full bg-accent-soft">
                <Zap className="h-2.5 w-2.5 text-accent" />
              </span>
              专为广告制作公司打造的 AI 报价系统
            </div>

            <h1 className="mt-6 text-[38px] font-semibold leading-[1.15] tracking-tight text-ink sm:text-[46px] lg:text-[54px]">
              客户发张图，
              <br />
              <span className="text-gradient">30 秒出报价。</span>
            </h1>

            <p className="mt-5 max-w-xl text-[16px] leading-relaxed text-muted sm:text-[17px]">
              把微信里的客户需求，自动变成专业报价。AI 负责看懂需求，你自己的价格库和规则负责算钱——
              每一条报价都能说清楚钱花在哪里。
            </p>

            <div className="mt-8 flex flex-wrap items-center gap-3">
              <Link href="/register">
                <Button size="lg">
                  免费开始报价
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <Link href="/demo">
                <Button variant="secondary" size="lg">
                  查看演示
                </Button>
              </Link>
            </div>

            <div className="mt-8 flex flex-wrap items-center gap-x-7 gap-y-3 text-[13px] text-muted">
              <span className="flex items-center gap-1.5">
                <Clock className="h-3.5 w-3.5 text-accent" />
                平均 30 秒出报价
              </span>
              <span className="flex items-center gap-1.5">
                <ShieldCheck className="h-3.5 w-3.5 text-accent" />
                没有 API Key 也能用
              </span>
              <span className="flex items-center gap-1.5">
                <BadgeCheck className="h-3.5 w-3.5 text-accent" />
                数据按企业严格隔离
              </span>
            </div>
          </div>

          <div className="animate-[fade-up_0.6s_0.1s_cubic-bezier(0.16,1,0.3,1)_both]">
            <HeroDemo />
          </div>
        </div>
      </section>

      <section className="border-y border-line bg-surface py-20">
        <div className="container-page">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-[28px] font-semibold leading-snug tracking-tight text-ink sm:text-[32px]">
              你不是不会报价，
              <br className="sm:hidden" />
              只是不应该重复算一百次。
            </h2>
            <p className="mt-4 text-[15px] leading-relaxed text-muted">
              一家广告公司一年要做几百份报价，其中大部分是重复劳动。
            </p>
          </div>

          <div className="mt-12 grid gap-5 md:grid-cols-3">
            {PAINS.map((pain) => {
              const Icon = pain.icon;
              return (
                <div key={pain.title} className="card p-6 transition-transform duration-300 hover:-translate-y-1">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-line bg-surface-2">
                    <Icon className="h-4 w-4 text-ink" />
                  </div>
                  <h3 className="mt-4 text-[16px] font-semibold text-ink">{pain.title}</h3>
                  <ul className="mt-3 space-y-2">
                    {pain.lines.map((line) => (
                      <li key={line} className="flex gap-2 text-[13.5px] leading-relaxed text-muted">
                        <span className="mt-[7px] h-1 w-1 shrink-0 rounded-full bg-faint" />
                        {line}
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      <section className="py-20">
        <div className="container-page">
          <div className="flex flex-wrap items-end justify-between gap-6">
            <div className="max-w-xl">
              <Badge tone="accent">四步闭环</Badge>
              <h2 className="mt-4 text-[28px] font-semibold leading-snug tracking-tight text-ink sm:text-[32px]">
                从客户发来的一句话，到一份能签单的报价
              </h2>
            </div>
            <p className="max-w-sm text-[14px] leading-relaxed text-muted">
              报价引擎不是又一个 Excel 插件。它把识别、计算、出单、跟进连成一条不会漏项的流水线。
            </p>
          </div>

          <div className="mt-12 grid gap-5 lg:grid-cols-4">
            {STEPS.map((item) => {
              const Icon = item.icon;
              return (
                <div key={item.step} className="relative rounded-[16px] border border-line bg-surface p-6">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[12px] tracking-widest text-faint">{item.step}</span>
                    <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent-soft text-accent">
                      <Icon className="h-4 w-4" />
                    </span>
                  </div>
                  <h3 className="mt-5 text-[17px] font-semibold text-ink">{item.title}</h3>
                  <p className="mt-2 text-[13.5px] leading-relaxed text-muted">{item.desc}</p>
                  <ul className="mt-4 space-y-1.5 border-t border-line pt-4">
                    {item.points.map((point) => (
                      <li key={point} className="flex items-start gap-2 text-[12.5px] text-ink-soft">
                        <BadgeCheck className="mt-0.5 h-3.5 w-3.5 shrink-0 text-success" />
                        {point}
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      <section className="border-y border-line bg-surface py-20">
        <div className="container-page">
          <div className="mx-auto max-w-2xl text-center">
            <Badge tone="accent">真实产品界面</Badge>
            <h2 className="mt-4 text-[28px] font-semibold leading-snug tracking-tight text-ink sm:text-[32px]">
              微信截图 → AI 识别 → 报价工作台 → 报价单
            </h2>
            <p className="mt-4 text-[15px] leading-relaxed text-muted">
              每一步都真实可用，不是演示图。识别结果可以改，价格永远由你的规则引擎算。
            </p>
          </div>

          <div className="mt-14 space-y-6">
            <FlowRow index="01" title="客户需求" caption="微信聊天、图片、PDF、Excel，甚至直接粘贴一段话" content={<MockChat />} />
            <FlowRow
              index="02"
              title="AI 识别结果"
              caption="产品、尺寸、数量、安装、交期自动结构化，缺失项自动标出来"
              content={<MockStructured />}
              reversed
            />
            <FlowRow
              index="03"
              title="报价工作台"
              caption="人工校正后一键重算，成本、损耗、人工、利润逐项可见"
              content={<MockWorkbench />}
            />
            <FlowRow
              index="04"
              title="专业报价单"
              caption="三档方案、企业条款、公开链接，客户手机上打开就能看"
              content={<MockQuotation />}
              reversed
            />
          </div>
        </div>
      </section>

      <section className="py-20">
        <div className="container-page">
          <div className="grid items-center gap-12 lg:grid-cols-[0.9fr_1.1fr]">
            <div>
              <Badge tone="accent">工作台</Badge>
              <h2 className="mt-4 text-[28px] font-semibold leading-snug tracking-tight text-ink sm:text-[32px]">
                今天该做什么，打开就知道
              </h2>
              <p className="mt-4 text-[15px] leading-relaxed text-muted">
                今日报价、待跟进、本月报价金额、本月成交金额——四个数字管住一天的节奏。
                报价转化漏斗让你看清客户到底卡在哪一步。
              </p>
              <div className="mt-7 space-y-3">
                {[
                  { icon: Bell, text: "客户查看了报价，立刻提醒你跟进" },
                  { icon: Users, text: "今日待跟进客户自动列出来" },
                  { icon: LineChart, text: "报价金额与成交趋势一目了然" },
                ].map((item) => {
                  const Icon = item.icon;
                  return (
                    <div key={item.text} className="flex items-center gap-3 text-[14px] text-ink-soft">
                      <span className="flex h-8 w-8 items-center justify-center rounded-lg border border-line bg-surface">
                        <Icon className="h-3.5 w-3.5 text-accent" />
                      </span>
                      {item.text}
                    </div>
                  );
                })}
              </div>
            </div>

            <MockDashboard />
          </div>
        </div>
      </section>

      <section className="border-y border-line bg-surface py-20">
        <div className="container-page">
          <div className="flex flex-wrap items-end justify-between gap-6">
            <div className="max-w-xl">
              <Badge tone="accent">价格库</Badge>
              <h2 className="mt-4 text-[28px] font-semibold leading-snug tracking-tight text-ink sm:text-[32px]">
                你自己的价格，你自己的规则
              </h2>
              <p className="mt-4 text-[15px] leading-relaxed text-muted">
                预置 10 个分类、20 多个常用产品，注册后可以直接改。也支持 Excel 批量导入现有价格表。
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              {["固定单价", "面积计价", "体积 / 重量", "成本加成", "毛利率", "条件价格"].map((tag) => (
                <Badge key={tag} tone="neutral">
                  {tag}
                </Badge>
              ))}
            </div>
          </div>

          <div className="mt-10 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
            {PRICE_LIBRARY.map((item) => (
              <div
                key={item.name}
                className="rounded-[14px] border border-line bg-surface p-4 transition-colors hover:border-line-strong"
              >
                <div className="flex items-center justify-between">
                  <span className="text-[14px] font-semibold text-ink">{item.name}</span>
                  <Package className="h-3.5 w-3.5 text-faint" />
                </div>
                <p className="mt-2 text-[12px] leading-relaxed text-muted">{item.desc}</p>
                <p className="mt-3 text-[11.5px] text-accent">{item.unit}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-20">
        <div className="container-page">
          <div className="mx-auto max-w-2xl text-center">
            <Badge tone="accent">行业模板</Badge>
            <h2 className="mt-4 text-[28px] font-semibold leading-snug tracking-tight text-ink sm:text-[32px]">
              底层是报价引擎，不是广告软件
            </h2>
            <p className="mt-4 text-[15px] leading-relaxed text-muted">
              广告只是第一套模板。换行业只需要换产品、字段、公式和规则，核心引擎不动。
            </p>
          </div>

          <div className="mt-12 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {INDUSTRIES.map((item) => (
              <div
                key={item.name}
                className={cn(
                  "rounded-[16px] border p-5",
                  item.active ? "border-accent/30 bg-accent-soft/40" : "border-line bg-surface",
                )}
              >
                <div className="flex items-center justify-between">
                  <h3 className="text-[15px] font-semibold text-ink">{item.name}</h3>
                  <Badge tone={item.active ? "accent" : "neutral"}>{item.status}</Badge>
                </div>
                <p className="mt-2.5 text-[12.5px] leading-relaxed text-muted">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="border-y border-line bg-surface py-20">
        <div className="container-page">
          <div className="mx-auto max-w-2xl text-center">
            <Badge tone="accent">价格</Badge>
            <h2 className="mt-4 text-[28px] font-semibold leading-snug tracking-tight text-ink sm:text-[32px]">
              比一次报价失误便宜得多
            </h2>
            <p className="mt-4 text-[15px] leading-relaxed text-muted">
              免费版就能跑完整闭环。用得顺手了再升级，随时可以换。
            </p>
          </div>

          <div className="mt-12 grid gap-5 lg:grid-cols-3">
            {PLANS.map((plan) => (
              <div
                key={plan.code}
                className={cn(
                  "relative flex flex-col rounded-[18px] border p-6",
                  plan.highlight ? "border-accent/40 bg-surface shadow-[var(--shadow-card)]" : "border-line bg-surface",
                )}
              >
                {plan.highlight ? (
                  <span className="absolute -top-3 left-6">
                    <Badge tone="dark">最受欢迎</Badge>
                  </span>
                ) : null}
                <h3 className="text-[16px] font-semibold text-ink">{plan.name}</h3>
                <p className="mt-1 text-[12.5px] text-muted">{plan.desc}</p>
                <div className="mt-5 flex items-end gap-1.5">
                  <span className="text-[14px] text-muted">¥</span>
                  <span className="text-[34px] font-semibold leading-none tracking-tight text-ink">{plan.price}</span>
                  <span className="text-[13px] text-muted">{plan.cycle}</span>
                </div>
                <ul className="mt-6 flex-1 space-y-2.5 border-t border-line pt-5">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-2 text-[13px] text-ink-soft">
                      <BadgeCheck className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
                      {feature}
                    </li>
                  ))}
                </ul>
                <Link href="/register" className="mt-6">
                  <Button variant={plan.highlight ? "primary" : "secondary"} className="w-full">
                    {plan.cta}
                  </Button>
                </Link>
              </div>
            ))}
          </div>

          <p className="mt-6 text-center text-[13px] text-muted">
            需要私有部署或源码授权？
            <Link href="/pricing" className="ml-1 text-accent hover:underline">
              查看部署方案
            </Link>
          </p>
        </div>
      </section>

      <section className="relative overflow-hidden py-24">
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-accent/[0.07] to-transparent" />
        <div className="container-page relative text-center">
          <h2 className="mx-auto max-w-2xl text-[30px] font-semibold leading-snug tracking-tight text-ink sm:text-[36px]">
            下一份报价，不必再从零开始。
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-[15px] leading-relaxed text-muted">
            注册后立即拥有完整价格库与 Demo 数据，3 分钟内做完你的第一份报价。
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Link href="/register">
              <Button size="lg">
                免费开始报价
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link href="/demo">
              <Button variant="secondary" size="lg">
                用演示账号体验
              </Button>
            </Link>
          </div>
          <div className="mt-6 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-[12.5px] text-faint">
            <span className="flex items-center gap-1.5">
              <Layers className="h-3.5 w-3.5" />
              无需安装，浏览器打开即用
            </span>
            <span className="flex items-center gap-1.5">
              <ClipboardList className="h-3.5 w-3.5" />
              支持 Excel 导入现有价格
            </span>
            <span className="flex items-center gap-1.5">
              <Truck className="h-3.5 w-3.5" />
              手机浏览器同样可用
            </span>
          </div>
        </div>
      </section>

      <SiteFooter />
    </div>
  );
}

function FlowRow({
  index,
  title,
  caption,
  content,
  reversed = false,
}: {
  index: string;
  title: string;
  caption: string;
  content: React.ReactNode;
  reversed?: boolean;
}) {
  return (
    <div
      className={cn(
        "grid items-center gap-6 rounded-[20px] border border-line bg-surface p-5 lg:grid-cols-[0.85fr_1.15fr] lg:gap-10 lg:p-7",
        reversed && "lg:grid-cols-[1.15fr_0.85fr]",
      )}
    >
      <div className={cn(reversed && "lg:order-2")}>
        <span className="font-mono text-[12px] tracking-widest text-faint">{index}</span>
        <h3 className="mt-2 text-[19px] font-semibold tracking-tight text-ink">{title}</h3>
        <p className="mt-2 text-[13.5px] leading-relaxed text-muted">{caption}</p>
      </div>
      <div className={cn(reversed && "lg:order-1")}>{content}</div>
    </div>
  );
}

