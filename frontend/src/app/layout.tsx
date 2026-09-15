import type { Metadata, Viewport } from "next";

import { SessionProvider } from "@/components/providers";
import "./globals.css";

const appName = process.env.NEXT_PUBLIC_APP_NAME ?? "报价引擎";
const appUrl = process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000";

export const metadata: Metadata = {
  metadataBase: new URL(appUrl),
  title: {
    default: `${appName} — 客户发张图，30 秒出报价`,
    template: `%s · ${appName}`,
  },
  description:
    "广告标识行业 AI 报价系统：把微信里的客户需求，自动变成专业报价单。AI 识别需求，系统按你自己的价格库计算，30 秒生成可分享的报价单。",
  keywords: [
    "广告报价软件",
    "广告制作报价",
    "广告报价系统",
    "发光字报价",
    "门头报价",
    "广告公司报价单",
    "AI报价",
  ],
  applicationName: appName,
  authors: [{ name: appName }],
  openGraph: {
    type: "website",
    locale: "zh_CN",
    url: appUrl,
    siteName: appName,
    title: `${appName} — 客户发张图，30 秒出报价`,
    description: "把微信里的客户需求，自动变成专业报价。AI 负责识别，系统负责计算。",
  },
  twitter: {
    card: "summary_large_image",
    title: `${appName} — 客户发张图，30 秒出报价`,
    description: "广告制作行业 AI 报价系统。",
  },
  robots: { index: true, follow: true },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#ffffff",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen antialiased">
        <SessionProvider>{children}</SessionProvider>
      </body>
    </html>
  );
}

