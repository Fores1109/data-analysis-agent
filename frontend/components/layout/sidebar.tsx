"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  BrainCircuit,
  Database,
  FileText,
  FlaskConical,
  FolderOpen,
  LayoutDashboard,
  Link2,
  MessageSquareText,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ApiStatus } from "@/components/api-status";
import { ThemeToggle } from "@/components/theme-toggle";

const NAV_ITEMS = [
  { href: "/", label: "仪表盘", icon: LayoutDashboard, exact: true },
  { href: "/analyze", label: "自然语言分析", icon: MessageSquareText },
  { href: "/charts", label: "图表可视化", icon: BarChart3 },
  { href: "/sql", label: "SQL 助手", icon: Database },
  { href: "/abtest", label: "A/B 实验", icon: FlaskConical },
  { href: "/ml", label: "机器学习", icon: BrainCircuit },
  { href: "/causal", label: "因果推断", icon: Link2 },
  { href: "/report", label: "报告生成", icon: FileText },
  { href: "/data", label: "数据源", icon: FolderOpen },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden md:flex w-64 shrink-0 flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground">
      {/* 品牌区 */}
      <div className="flex items-center gap-3 px-5 h-16 border-b border-sidebar-border">
        <div className="flex size-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 text-white shadow-md shadow-indigo-500/25">
          <Sparkles className="size-5" />
        </div>
        <div className="leading-tight">
          <div className="text-sm font-semibold tracking-tight">数据分析 Agent</div>
          <div className="text-[11px] text-muted-foreground">Data Analysis Agent</div>
        </div>
      </div>

      {/* 导航 */}
      <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
        <div className="px-3 pb-2 text-[11px] font-medium uppercase tracking-wider text-muted-foreground/70">
          功能
        </div>
        {NAV_ITEMS.map(({ href, label, icon: Icon, exact }) => {
          const active = exact ? pathname === href : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                active
                  ? "bg-sidebar-accent text-sidebar-accent-foreground"
                  : "text-muted-foreground hover:bg-sidebar-accent/60 hover:text-sidebar-foreground",
              )}
            >
              <Icon className="size-4" />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* 底部：API 状态 + 主题切换 */}
      <div className="space-y-3 border-t border-sidebar-border p-4">
        <div className="flex items-center justify-between gap-2">
          <ApiStatus />
          <ThemeToggle />
        </div>
        <p className="text-[11px] leading-relaxed text-muted-foreground/70">
          前端骨架 · Next.js 16 + shadcn/ui · 对接 FastAPI
        </p>
      </div>
    </aside>
  );
}
