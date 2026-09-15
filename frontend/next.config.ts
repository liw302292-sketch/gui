import type { NextConfig } from "next";

/**
 * 前端只与同源 /api/backend/* 通信，由 Next 反向代理到后端。
 * 好处：
 *  - 后端 JWT 存放在 HttpOnly Cookie，浏览器不接触 token
 *  - 同源请求天然规避大部分 CSRF 与跨域问题
 *  - 生产环境可平滑切换到 api.xxx.com 独立域名
 */
const backendUrl = process.env.BACKEND_INTERNAL_URL ?? "http://localhost:8000";
// Docker 镜像使用 standalone 产物；本地 `npm start` 走普通产物。
const useStandalone = process.env.NEXT_OUTPUT_STANDALONE === "true";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  ...(useStandalone ? { output: "standalone" as const } : {}),
  outputFileTracingRoot: __dirname,
  experimental: {
    optimizePackageImports: ["lucide-react"],
  },
  async rewrites() {
    return [
      {
        source: "/api/backend/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "X-Frame-Options", value: "SAMEORIGIN" },
        ],
      },
    ];
  },
};

export default nextConfig;
