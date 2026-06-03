import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AIGC 营销平台",
  description: "广告文案 / 好评 / 海报 / 视频 一站式生成",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
