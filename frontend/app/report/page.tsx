"use client";

import { useMemo, useState } from "react";
import { Download, FileText, Loader2, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Markdown } from "@/components/markdown";
import { api, ApiClientError } from "@/lib/api";
import { DATASETS } from "@/lib/datasets";
import {
  clearQaHistory,
  clearReportCharts,
  loadQaHistory,
  loadReportCharts,
} from "@/lib/storage";
import type { ReportResponse } from "@/lib/types";

const errMsg = (e: unknown) =>
  e instanceof ApiClientError ? e.detail : e instanceof Error ? e.message : String(e);

function download(filename: string, text: string, mime: string) {
  const blob = new Blob([text], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export default function ReportPage() {
  const [title, setTitle] = useState("数据分析报告");
  const [dataPath, setDataPath] = useState(DATASETS[0].path);
  const [save, setSave] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [report, setReport] = useState<ReportResponse | null>(null);

  const qaPairs = useMemo(() => loadQaHistory(), []);
  const charts = useMemo(() => loadReportCharts(), []);

  const dataName = DATASETS.find((d) => d.path === dataPath)?.name ?? dataPath;

  const generate = async () => {
    if (generating) return;
    setGenerating(true);
    setReport(null);
    try {
      const res = await api.reportGenerate({
        title: title.trim() || "数据分析报告",
        dataName,
        dataPath,
        qaPairs,
        charts,
        save,
      });
      setReport(res);
      toast.success(res.saved_path ? `报告已生成并保存：${res.saved_path}` : "报告已生成");
    } catch (e) {
      toast.error(errMsg(e));
    } finally {
      setGenerating(false);
    }
  };

  const clearAll = () => {
    clearQaHistory();
    clearReportCharts();
    toast.success("已清空问答历史与图表记录（刷新后生效）");
  };

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold tracking-tight">📑 报告生成</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          汇总「自然语言分析」页的问答记录与「图表可视化」页加入的图表，一键导出 Markdown / HTML。
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <FileText className="size-4 text-indigo-500" /> 报告设置
          </CardTitle>
          <CardDescription>
            当前有 <strong>{qaPairs.length}</strong> 条问答记录、<strong>{charts.length}</strong>{" "}
            张图表（来自本浏览器会话）。
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="report-title">报告标题</Label>
              <Input id="report-title" value={title} onChange={(e) => setTitle(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label>数据来源（用于概览）</Label>
              <Select value={dataPath} onValueChange={setDataPath}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {DATASETS.map((d) => (
                    <SelectItem key={d.path} value={d.path}>
                      {d.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Switch id="report-save" checked={save} onCheckedChange={setSave} />
            <Label htmlFor="report-save" className="font-normal text-sm text-muted-foreground">
              同时保存到后端 data/reports 目录
            </Label>
          </div>

          <div className="flex flex-wrap gap-2">
            <Button onClick={generate} disabled={generating}>
              {generating && <Loader2 className="size-4 animate-spin" />} 生成报告
            </Button>
            <Button variant="outline" onClick={clearAll}>
              <Trash2 className="size-4" /> 清空历史
            </Button>
          </div>

          {report && (
            <div className="space-y-4 pt-1">
              <div className="flex flex-wrap gap-2">
                <Button
                  variant="secondary"
                  onClick={() => download(`${title}.md`, report.markdown, "text/markdown")}
                >
                  <Download className="size-4" /> 下载 Markdown
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => download(`${title}.html`, report.html, "text/html")}
                >
                  <Download className="size-4" /> 下载 HTML（含图表）
                </Button>
              </div>
              <Separator />
              <div className="rounded-lg border bg-card p-4">
                <p className="mb-2 text-xs font-medium text-muted-foreground">预览</p>
                <Markdown content={report.markdown} />
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
