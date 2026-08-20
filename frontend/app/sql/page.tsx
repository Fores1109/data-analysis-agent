"use client";

import { useState } from "react";
import { Check, Copy, Database, Sparkles, Wand2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Markdown } from "@/components/markdown";
import { api, ApiClientError } from "@/lib/api";

export default function SqlPage() {
  const [question, setQuestion] = useState("");
  const [sql, setSql] = useState("");
  const [advice, setAdvice] = useState("");
  const [generating, setGenerating] = useState(false);
  const [optimizing, setOptimizing] = useState(false);
  const [copied, setCopied] = useState(false);

  const errMsg = (e: unknown) =>
    e instanceof ApiClientError ? e.detail : e instanceof Error ? e.message : String(e);

  const generate = async () => {
    const q = question.trim();
    if (!q || generating) return;
    setGenerating(true);
    try {
      const res = await api.generateSql(q);
      setSql(res.sql);
      toast.success("SQL 已生成");
    } catch (e) {
      toast.error(errMsg(e));
    } finally {
      setGenerating(false);
    }
  };

  const optimize = async () => {
    const q = question.trim();
    if (!q || optimizing) return;
    setOptimizing(true);
    try {
      const res = await api.optimizeSql(q);
      setAdvice(res.advice);
      toast.success("优化建议已生成");
    } catch (e) {
      toast.error(errMsg(e));
    } finally {
      setOptimizing(false);
    }
  };

  const copy = async () => {
    if (!sql) return;
    await navigator.clipboard.writeText(sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold tracking-tight">🗄️ SQL 助手</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          用自然语言描述查询需求，AI 根据 .env 配置的数据库表结构生成 SQL 并给出优化建议。
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Sparkles className="size-4 text-indigo-500" /> 自然语言 → SQL
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="例如：统计每个月的订单数量与总销售额，按月份排序"
            rows={3}
          />
          <div className="flex gap-2">
            <Button onClick={generate} disabled={generating || !question.trim()}>
              <Wand2 className="size-4" />
              {generating ? "生成中…" : "生成 SQL"}
            </Button>
            <Button variant="outline" onClick={optimize} disabled={optimizing || !question.trim()}>
              {optimizing ? "优化中…" : "优化建议"}
            </Button>
          </div>

          {sql && (
            <div className="space-y-2 pt-1">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
                  <Database className="size-3.5" /> 生成的 SQL
                </span>
                <Button variant="ghost" size="sm" onClick={copy} className="h-7 text-xs">
                  {copied ? <Check className="size-3.5 text-emerald-500" /> : <Copy className="size-3.5" />}
                  {copied ? "已复制" : "复制"}
                </Button>
              </div>
              <pre className="overflow-x-auto rounded-lg border bg-muted/40 p-3 text-xs leading-relaxed">
                <code>{sql}</code>
              </pre>
            </div>
          )}

          {advice && (
            <div className="space-y-2 pt-1">
              <span className="text-xs font-medium text-muted-foreground">优化建议</span>
              <div className="rounded-lg border bg-card p-3">
                <Markdown content={advice} />
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
