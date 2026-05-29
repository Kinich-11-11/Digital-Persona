import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Digital Persona",
  description: "Local-first AI persona chat MVP"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
