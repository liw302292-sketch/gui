"use client";

import { ArrowRight, BadgeCheck, Check, Globe, Lock, Smartphone } from "lucide-react";
import Link from "next/link";

import { SiteFooter, SiteHeader } from "@/components/marketing/site-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { toast } from "@/components/ui/toast";

const DEMO_STEPS = [
  { step: "01", title: "登录演示企业", desc: "账号 demo@example.com / Demo123456!，企业名称为「星辰广告制作」。" },
  { step: "02", title: "打开「新建报价」", desc: "上传一张微信截图，或直接粘贴：帮我做一个10米门头，铝塑板底，12个发光字，月底安装。" },
  { step: "03", title: "查看识别结果", desc: "AI 输出结构化需求，并提示缺少门头高度、安装地址、发光字尺寸。" },
  { step: "04", title: "确认并生成报价", desc: "规则引擎按价格库计算，生成经济版 / 标准版 / 高级版三档方案。" },
  { step: "05", title: "生成公开链接", desc: "复制链接在手机或新窗口打开，模拟客户查看，后台状态会自动变成「已查看」。" },
];

export default function DemoPage() {
  const demoEmail = "demo@example.com";
  const demoPassword = "Demo123456!";

  async function copy(text: string, label: string) {
    try {
      await navigator.clipboard.writeText(text);
      toast.success(`${label}已复制`);
    } catch {
      toast.error("复制失败，请手动选择文本复制");
    }
  }

  return (
    <div className="bg-background">
      <SiteHeader />

      <section className="border-b border-line bg-surface py-16">
        <div className="container-page grid gap-10 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
          <div>
            <Badge tone="accent">在线演示</Badge>
            <h1 className="mt-4 text-[34px] font-semibold leading-tight tracking-tight text-ink sm:text-[40px]">
              3 分钟走完一次真实报价
            </h1>
            <p className="mt-4 max-w-xl text-[15.5px] leading-relaxed text-muted">
              演示环境已经预置好一家广告公司：23 个产品、10 个客户、20 份不同状态的报价与跟进记录。
              没有 DeepSeek API Key 也能完整跑通，系统会自动进入 Mock AI 模式。
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/login">
                <Button size="lg">
                  用演示账号登录
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <Link href="/register">
                <Button variant="secondary" size="lg">
                  用自己的公司注册
                </Button>
              </Link>
            </div>
          </div>

          <div className="rounded-[18px] border border-line bg-surface p-6 shadow-[var(--shadow-card)]">
            <h2 className="text-[15px] font-semibold text-ink">演示账号</h2>
            <div className="mt-4 space-y-3">
              <DemoCredential
                label="演示企业（推荐）"
                email={demoEmail}
                password={demoPassword}
                onCopy={copy}
              />
              <DemoCredential
                label="平台管理员后台"
                email="admin@example.com"
                password="Admin123456!"
                onCopy={copy}
              />
            </div>
            <p className="mt-4 flex items-start gap-2 text-[12px] leading-relaxed text-faint">
              <Lock className="mt-0.5 h-3.5 w-3.5 shrink-0" />
              演示数据仅用于体验，生产环境第一次启动会强制提示修改管理员密码。
            </p>
          </div>
        </div>
      </section>

      <section className="py-16">
        <div className="container-page">
          <h2 className="text-[26px] font-semibold tracking-tight text-ink">演示路径</h2>
          <p className="mt-3 max-w-2xl text-[14.5px] leading-relaxed text-muted">
            跟着下面五步走一遍，你会看到从客户一句话到客户打开报价的完整链路。
          </p>

          <div className="mt-10 grid gap-4 lg:grid-cols-5">
            {DEMO_STEPS.map((item) => (
              <div key={item.step} className="rounded-[16px] border border-line bg-surface p-5">
                <span className="font-mono text-[12px] tracking-widest text-faint">{item.step}</span>
                <h3 className="mt-3 text-[15px] font-semibold text-ink">{item.title}</h3>
                <p className="mt-2 text-[12.5px] leading-relaxed text-muted">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="border-y border-line bg-surface py-16">
        <div className="container-page grid gap-10 lg:grid-cols-3">
          <div className="rounded-[18px] border border-line p-6">
            <Smartphone className="h-5 w-5 text-accent" />
            <h3 className="mt-4 text-[15px] font-semibold text-ink">手机上也能用</h3>
            <p className="mt-2 text-[13px] leading-relaxed text-muted">
              移动端底部有「新建报价 / 报价 / 客户 / 跟进 / 我的」五个入口，老板在外面也能直接报价。
            </p>
          </div>
          <div className="rounded-[18px] border border-line p-6">
            <Globe className="h-5 w-5 text-accent" />
            <h3 className="mt-4 text-[15px] font-semibold text-ink">公开报价页真实可用</h3>
            <p className="mt-2 text-[13px] leading-relaxed text-muted">
              每个报价都有一条随机链接，客户无需登录即可查看、下载、打印，系统会记录查看行为。
            </p>
          </div>
          <div className="rounded-[18px] border border-line p-6">
            <BadgeCheck className="h-5 w-5 text-accent" />
            <h3 className="mt-4 text-[15px] font-semibold text-ink">可以随便改</h3>
            <p className="mt-2 text-[13px] leading-relaxed text-muted">
              演示数据都可以修改、删除。想接自己的真实价格？在「产品与价格」里改价格，或直接 Excel 导入。
            </p>
          </div>
        </div>
      </section>

      <section className="py-16">
        <div className="container-page">
          <div className="rounded-[20px] border border-line bg-surface p-8">
            <h2 className="text-[22px] font-semibold tracking-tight text-ink">演示环境包含什么</h2>
            <div className="mt-6 grid gap-x-8 gap-y-3 sm:grid-cols-2 lg:grid-cols-3">
              {[
                "23 个广告产品与成本、报价",
                "6 条价格规则（含面积批发价）",
                "10 个客户与跟进状态",
                "20 份不同状态的报价单",
                "5 条跟进记录",
                "AI 调用历史与成本统计",
                "管理员后台与平台数据",
                "免费 / 专业 / 企业三档套餐",
                "Mail: 全部功能无需 API Key",
              ].map((item) => (
                <div key={item} className="flex items-center gap-2.5 text-[13.5px] text-ink-soft">
                  <Check className="h-3.5 w-3.5 shrink-0 text-success" />
                  {item.replace("Mail: ", "")}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <SiteFooter />
    </div>
  );
}

function DemoCredential({
  label,
  email,
  password,
  onCopy,
}: {
  label: string;
  email: string;
  password: string;
  onCopy: (text: string, label: string) => void;
}) {
  return (
    <div className="rounded-[14px] border border-line bg-surface-2 p-4">
      <p className="text-[12.5px] font-medium text-ink-soft">{label}</p>
      <div className="mt-2 space-y-1.5 font-mono text-[12.5px] text-ink">
        <button type="button" className="block hover:text-accent" onClick={() => onCopy(email, "邮箱")}>
          {email}
        </button>
        <button type="button" className="block hover:text-accent" onClick={() => onCopy(password, "密码")}>
          {password}
        </button>
      </div>
    </div>
  );
}

