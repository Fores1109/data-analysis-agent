"use client";

import { useEffect, useRef, useState } from "react";
import { BarChart3, Loader2, Plus } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { PlotChart } from "@/components/plot-chart";
import { api, ApiClientError } from "@/lib/api";
import { DATASETS } from "@/lib/datasets";
import { isNumeric, useDataPreview } from "@/lib/use-data-preview";
import { appendReportChart } from "@/lib/storage";
import type { ChartFigure } from "@/lib/types";

const CHART_TYPES = [
  { value: "bar", label: "柱状图" },
  { value: "line", label: "折线图" },
  { value: "scatter", label: "散点图" },
  { value: "histogram", label: "直方图" },
  { value: "box", label: "箱线图" },
  { value: "heatmap", label: "相关性热力图" },
  { value: "time_series", label: "时间序列" },
];

const errMsg = (e: unknown) =>
  e instanceof ApiClientError ? e.detail : e instanceof Error ? e.message : String(e);

export default function ChartsPage() {
  const [dataPath, setDataPath] = useState(DATASETS[0].path);
  const { preview, loading: previewLoading, error: previewError } = useDataPreview(dataPath);

  const allCols = preview?.columns ?? [];
  const numeric = allCols.filter((c) => isNumeric(preview!.dtypes[c] ?? ""));

  const [chartType, setChartType] = useState("bar");
  const [x, setX] = useState("");
  const [y, setY] = useState("");
  const [color, setColor] = useState("");
  const [bins, setBins] = useState(30);
  const [figure, setFigure] = useState<ChartFigure | null>(null);
  const [running, setRunning] = useState(false);
  // 记录已重置过的数据集：预览就绪后只对新数据集重置一次，避免用旧数据集列名
  const resetRef = useRef<string | null>(null);

  useEffect(() => {
    if (!preview || resetRef.current === dataPath) return;
    resetRef.current = dataPath;
    const numCols = preview.columns.filter((c) => isNumeric(preview.dtypes[c] ?? ""));
    setX(preview.columns[0] ?? "");
    setY(numCols[0] ?? "");
    setColor("");
    setFigure(null);
  }, [preview, dataPath]);

  const needsX = chartType !== "heatmap";
  const needsY = ["bar", "line", "scatter", "box", "time_series"].includes(chartType);
  const needsColor = chartType === "scatter";
  const needsBins = chartType === "histogram";

  const run = async () => {
    if (running) return;
    if (needsX && !x) return toast.error("请选择 X 轴字段");
    if (needsY && chartType !== "bar" && !y) return toast.error("请选择 Y 轴数值字段");
    setRunning(true);
    setFigure(null);
    try {
      const fig = await api.chartsGenerate({
        dataPath,
        chartType,
        x,
        y: chartType === "bar" && !y ? "" : y,
        color: color || undefined,
        bins,
      });
      setFigure(fig);
    } catch (e) {
      toast.error(errMsg(e));
    } finally {
      setRunning(false);
    }
  };

  const addToReport = () => {
    if (!figure) return;
    appendReportChart(figure);
    toast.success("已加入报告（见「报告生成」页面）");
  };

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold tracking-tight">📈 图表可视化</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          选择图表类型与字段生成交互图表，可把图表加入报告（报告生成页会嵌入）。
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <BarChart3 className="size-4 text-indigo-500" /> 图表生成
          </CardTitle>
          <CardDescription>后端基于 plotly 生成，前端交互渲染。</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm text-muted-foreground">数据集：</span>
            <Select value={dataPath} onValueChange={setDataPath}>
              <SelectTrigger className="w-72">
                <SelectValue placeholder="选择数据集" />
              </SelectTrigger>
              <SelectContent>
                {DATASETS.map((d) => (
                  <SelectItem key={d.path} value={d.path}>
                    {d.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {previewLoading && <Loader2 className="size-4 animate-spin text-muted-foreground" />}
            {previewError && <span className="text-xs text-destructive">{previewError}</span>}
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            <div className="space-y-2">
              <Label>图表类型</Label>
              <Select value={chartType} onValueChange={setChartType}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {CHART_TYPES.map((t) => (
                    <SelectItem key={t.value} value={t.value}>
                      {t.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {needsX && (
              <div className="space-y-2">
                <Label>X 轴 / 分类字段</Label>
                <Select value={x} onValueChange={setX}>
                  <SelectTrigger>
                    <SelectValue placeholder="选择字段" />
                  </SelectTrigger>
                  <SelectContent>
                    {allCols.map((c) => (
                      <SelectItem key={c} value={c}>
                        {c}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
            {needsY && (
              <div className="space-y-2">
                <Label>Y 轴 / 数值字段</Label>
                <Select value={y} onValueChange={setY}>
                  <SelectTrigger>
                    <SelectValue placeholder={chartType === "bar" ? "（不指定，计数）" : "选择数值列"} />
                  </SelectTrigger>
                  <SelectContent>
                    {numeric.map((c) => (
                      <SelectItem key={c} value={c}>
                        {c}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
            {needsColor && (
              <div className="space-y-2">
                <Label>颜色分组（可选）</Label>
                <Select value={color} onValueChange={setColor}>
                  <SelectTrigger>
                    <SelectValue placeholder="（无）" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">（无）</SelectItem>
                    {allCols.map((c) => (
                      <SelectItem key={c} value={c}>
                        {c}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
            {needsBins && (
              <div className="space-y-2">
                <Label htmlFor="bins">分箱数</Label>
                <Input
                  id="bins"
                  type="number"
                  min={2}
                  max={200}
                  value={bins}
                  onChange={(e) => setBins(Number(e.target.value))}
                />
              </div>
            )}
          </div>

          <div className="flex gap-2">
            <Button onClick={run} disabled={running}>
              {running && <Loader2 className="size-4 animate-spin" />} 生成图表
            </Button>
            {figure && (
              <Button variant="outline" onClick={addToReport}>
                <Plus className="size-4" /> 加入报告
              </Button>
            )}
          </div>

          {figure && (
            <div className="rounded-lg border bg-card p-3">
              <PlotChart figure={figure} />
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
