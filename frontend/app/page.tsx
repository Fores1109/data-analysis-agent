import Link from "next/link";
import {
  ArrowRight,
  BarChart3,
  BrainCircuit,
  Database,
  FileText,
  FlaskConical,
  FolderOpen,
  Link2,
  MessageSquareText,
  Sparkles,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const FEATURES = [
  {
    href: "/analyze",
    icon: MessageSquareText,
    title: "自然语言分析",
    desc: "对数据直接提问，自研 LangGraph Agent 生成并执行只读分析代码，回答流式输出。",
    accent: "from-indigo-500 to-violet-600",
  },
  {
    href: "/charts",
    icon: BarChart3,
    title: "图表可视化",
    desc: "7 种交互图表：柱状/折线/散点/直方图/箱线/热力图/时间序列，可加入报告。",
    accent: "from-cyan-500 to-blue-600",
  },
  {
    href: "/sql",
    icon: Database,
    title: "SQL 助手",
    desc: "自然语言生成 SQL、查询优化建议，配合 .env 配置的数据库表结构。",
    accent: "from-sky-500 to-cyan-600",
  },
  {
    href: "/abtest",
    icon: FlaskConical,
    title: "A/B 实验",
    desc: "Welch t 检验、双比例 z 检验（Yates 校正）、模拟实验，含效应量与结论解读。",
    accent: "from-rose-500 to-pink-600",
  },
  {
    href: "/ml",
    icon: BrainCircuit,
    title: "机器学习",
    desc: "Optuna 自动调参 + 模型对比评估，覆盖分类与回归场景。",
    accent: "from-emerald-500 to-teal-600",
  },
  {
    href: "/causal",
    icon: Link2,
    title: "因果推断",
    desc: "多元回归控制混杂（HC1 稳健标准误）、双重差分 DID，附逐变量解释。",
    accent: "from-purple-500 to-fuchsia-600",
  },
  {
    href: "/report",
    icon: FileText,
    title: "报告生成",
    desc: "汇总问答记录与图表，一键导出 Markdown / HTML 分析报告。",
    accent: "from-slate-500 to-gray-700",
  },
  {
    href: "/data",
    icon: FolderOpen,
    title: "数据源",
    desc: "浏览 data/ 目录内可用数据集（Olist 电商数据、示例销售数据）。",
    accent: "from-amber-500 to-orange-600",
  },
];

const TECH = [
  "Next.js 16",
  "shadcn/ui",
  "Tailwind CSS v4",
  "TypeScript",
  "FastAPI",
  "LangGraph",
  "Optuna",
  "SHAP",
];

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      {/* Hero */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-indigo-600 via-violet-600 to-fuchsia-600 p-8 text-white shadow-xl shadow-indigo-500/20">
        <div className="absolute -right-16 -top-16 size-56 rounded-full bg-white/10 blur-2xl" />
        <div className="absolute -bottom-20 right-24 size-40 rounded-full bg-white/10 blur-2xl" />
        <div className="relative space-y-3">
          <div className="flex items-center gap-2 text-sm font-medium text-white/80">
            <Sparkles className="size-4" /> Data Analysis Agent
          </div>
          <h1 className="text-2xl font-bold tracking-tight lg:text-3xl">
            用自然语言驱动你的数据分析
          </h1>
          <p className="max-w-2xl text-sm leading-relaxed text-white/85">
            基于 LangGraph 的多功能数据分析平台：自然语言问答 · SQL 助手 · 机器学习 ·
            A/B 实验 · 因果推断 · 时序预测，内置 Olist 巴西电商与游戏场景数据。
          </p>
          <div className="flex flex-wrap gap-2 pt-2">
            <Button asChild className="bg-white text-indigo-700 hover:bg-indigo-50">
              <Link href="/analyze">
                开始分析 <ArrowRight className="size-4" />
              </Link>
            </Button>
            <Button
              asChild
              variant="outline"
              className="border-white/30 bg-white/10 text-white hover:bg-white/20 hover:text-white"
            >
              <Link href="/data">查看数据集</Link>
            </Button>
          </div>
        </div>
      </div>

      {/* 功能卡片 */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {FEATURES.map(({ href, icon: Icon, title, desc, accent }) => (
          <Link key={href} href={href} className="group">
            <Card className="h-full transition-all hover:-translate-y-0.5 hover:shadow-lg">
              <CardHeader>
                <div
                  className={`mb-2 flex size-10 items-center justify-center rounded-xl bg-gradient-to-br ${accent} text-white shadow-md`}
                >
                  <Icon className="size-5" />
                </div>
                <CardTitle className="flex items-center gap-2 text-base">
                  {title}
                  <ArrowRight className="size-4 text-muted-foreground transition-transform group-hover:translate-x-1" />
                </CardTitle>
                <CardDescription>{desc}</CardDescription>
              </CardHeader>
            </Card>
          </Link>
        ))}
      </div>

      {/* 技术栈 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">技术栈</CardTitle>
          <CardDescription>前端骨架 + 后端服务</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          {TECH.map((t) => (
            <Badge key={t} variant="secondary" className="rounded-full">
              {t}
            </Badge>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
