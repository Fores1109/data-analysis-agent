"use client";

import type { ReactNode } from "react";
import { usePathname } from "next/navigation";
import { Sidebar } from "@/components/layout/sidebar";
import { ApiStatus } from "@/components/api-status";
import { ThemeToggle } from "@/components/theme-toggle";

const PAGE_TITLES: Record<string, string> = {
  "/": "仪表盘",
  "/analyze": "自然语言分析",
  "/charts": "图表可视化",
  "/sql": "SQL 助手",
  "/abtest": "A/B 实验",
  "/ml": "机器学习",
  "/causal": "因果推断",
  "/report": "报告生成",
  "/data": "数据源",
};

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const title = PAGE_TITLES[pathname] ?? "数据分析 Agent";

  return (
    <div className="flex min-h-screen">
      <Sidebar />

      <div className="flex min-w-0 flex-1 flex-col">
        {/* 顶栏 */}
        <header className="sticky top-0 z-20 flex h-14 items-center justify-between border-b bg-background/80 px-5 backdrop-blur-md lg:px-8">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold tracking-tight">{title}</span>
          </div>
          <div className="flex items-center gap-2 md:hidden">
            <ApiStatus />
            <ThemeToggle />
          </div>
        </header>

        <main className="flex-1 px-5 py-6 lg:px-8 lg:py-8">{children}</main>

        <footer className="border-t px-5 py-4 text-center text-xs text-muted-foreground lg:px-8">
          数据分析 Agent · Next.js 前端骨架 · 数据由 FastAPI 服务提供
        </footer>
      </div>
    </div>
  );
}
