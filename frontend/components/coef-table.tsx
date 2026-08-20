import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { CoefRow } from "@/lib/types";

function fmt(v: number | null | undefined): string {
  if (v === null || v === undefined) return "—";
  return Number(v).toFixed(4);
}

/** 回归系数表：变量 / 系数 / 标准误 / t / p（显著高亮）/ 95% 置信区间 */
export function CoefTable({
  coefs,
  highlight,
}: {
  coefs: Record<string, CoefRow>;
  /** 高亮的变量名（如 DID 交互项 _treated_post） */
  highlight?: string;
}) {
  const rows = Object.entries(coefs);
  if (rows.length === 0) return null;

  return (
    <div className="overflow-x-auto rounded-lg border">
      <table className="w-full text-sm">
        <thead className="bg-muted/60 text-xs text-muted-foreground">
          <tr>
            <th className="px-3 py-2 text-left font-medium">变量</th>
            <th className="px-3 py-2 text-right font-medium">系数</th>
            <th className="px-3 py-2 text-right font-medium">标准误</th>
            <th className="px-3 py-2 text-right font-medium">t</th>
            <th className="px-3 py-2 text-right font-medium">p</th>
            <th className="px-3 py-2 text-right font-medium">95% 置信区间</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(([name, r]) => {
            const p = r.p;
            const significant = p !== null && p !== undefined && p < 0.05;
            const isHighlight = name === highlight;
            return (
              <tr
                key={name}
                className={cn("border-t transition-colors", isHighlight && "bg-primary/5")}
              >
                <td className="px-3 py-2 font-medium">
                  {name === "const" ? "截距 (const)" : name}
                  {isHighlight && (
                    <Badge variant="outline" className="ml-2 border-primary/40 text-primary">
                      DID 交互项
                    </Badge>
                  )}
                </td>
                <td className="px-3 py-2 text-right tabular-nums">{fmt(r["系数"])}</td>
                <td className="px-3 py-2 text-right tabular-nums text-muted-foreground">
                  {fmt(r["标准误"])}
                </td>
                <td className="px-3 py-2 text-right tabular-nums text-muted-foreground">{fmt(r.t)}</td>
                <td
                  className={cn(
                    "px-3 py-2 text-right font-medium tabular-nums",
                    significant ? "text-emerald-600 dark:text-emerald-400" : "text-muted-foreground",
                  )}
                >
                  {fmt(p)}
                  {significant && <span className="ml-0.5">*</span>}
                </td>
                <td className="px-3 py-2 text-right tabular-nums text-muted-foreground">
                  [{fmt(r["95%置信区间"]?.[0])}, {fmt(r["95%置信区间"]?.[1])}]
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
