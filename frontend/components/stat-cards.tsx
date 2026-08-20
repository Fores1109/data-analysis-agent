import { cn } from "@/lib/utils";
import { Card, CardContent } from "@/components/ui/card";

export interface StatItem {
  label: string;
  value: string | number | boolean;
  tone?: "default" | "good" | "bad" | "accent";
}

const TONE_CLASS: Record<NonNullable<StatItem["tone"]>, string> = {
  default: "text-foreground",
  good: "text-emerald-600 dark:text-emerald-400",
  bad: "text-rose-600 dark:text-rose-400",
  accent: "text-indigo-600 dark:text-indigo-400",
};

/** 通用指标卡片组：一组 {label, value} 以网格卡片展示 */
export function StatCards({
  items,
  cols = 3,
}: {
  items: StatItem[];
  cols?: 2 | 3 | 4;
}) {
  const grid =
    cols === 4
      ? "sm:grid-cols-2 lg:grid-cols-4"
      : cols === 2
        ? "sm:grid-cols-2"
        : "sm:grid-cols-2 lg:grid-cols-3";
  return (
    <div className={cn("grid gap-3", grid)}>
      {items.map((it) => (
        <Card key={it.label} className="bg-card/70">
          <CardContent className="p-4">
            <p className="truncate text-xs text-muted-foreground">{it.label}</p>
            <p
              className={cn(
                "mt-1 truncate text-xl font-semibold tabular-nums",
                TONE_CLASS[it.tone ?? "default"],
              )}
              title={String(it.value)}
            >
              {String(it.value)}
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

/** 检验结论横幅：p<0.05 绿色、否则琥珀色 */
export function ConclusionBanner({ text }: { text: string }) {
  const significant = text.includes("显著") && !text.includes("不显著");
  return (
    <div
      className={cn(
        "rounded-lg border px-4 py-3 text-sm leading-relaxed",
        significant
          ? "border-emerald-500/30 bg-emerald-500/5 text-emerald-800 dark:text-emerald-300"
          : "border-amber-500/30 bg-amber-500/5 text-amber-800 dark:text-amber-300",
      )}
    >
      <span className="font-semibold">📌 结论：</span>
      {text}
    </div>
  );
}

/** 提示信息框（回归/DID 的统计提示） */
export function Note({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-indigo-500/25 bg-indigo-500/5 px-4 py-3 text-xs leading-relaxed text-muted-foreground">
      {children}
    </div>
  );
}
