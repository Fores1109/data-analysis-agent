"use client";

import { useState } from "react";
import { BrainCircuit, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { api, ApiClientError } from "@/lib/api";
import { DATASETS } from "@/lib/datasets";
import type { MlTrainResponse } from "@/lib/types";

export default function MlPage() {
  const [dataPath, setDataPath] = useState(DATASETS[0].path);
  const [target, setTarget] = useState("");
  const [result, setResult] = useState<MlTrainResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const train = async () => {
    const col = target.trim();
    if (!col || loading) return;
    setLoading(true);
    setResult(null);
    try {
      const res = await api.train(dataPath, col);
      setResult(res);
      toast.success("训练完成");
    } catch (e) {
      toast.error(e instanceof ApiClientError ? e.detail : e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold tracking-tight">🤖 机器学习</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          后端用 Optuna(TPE) 对随机森林 / 梯度提升 / 线性模型做超参搜索并自动评估（分类 F1 / 回归 R²）。
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <BrainCircuit className="size-4 text-indigo-500" /> 自动训练
          </CardTitle>
          <CardDescription>选择数据集与目标列，开始 AutoML 训练（耗时与数据量有关）。</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="ml-dataset">数据集</Label>
              <Select value={dataPath} onValueChange={setDataPath}>
                <SelectTrigger id="ml-dataset">
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
            </div>
            <div className="space-y-2">
              <Label htmlFor="ml-target">目标列</Label>
              <Input
                id="ml-target"
                placeholder="例如：sales / price / is_churned"
                value={target}
                onChange={(e) => setTarget(e.target.value)}
              />
            </div>
          </div>

          <Button onClick={train} disabled={loading || !target.trim()}>
            {loading ? <Loader2 className="size-4 animate-spin" /> : <BrainCircuit className="size-4" />}
            {loading ? "训练中…" : "开始训练"}
          </Button>

          {result && (
            <div className="space-y-2 pt-1">
              <span className="text-xs font-medium text-muted-foreground">
                训练结果（原始返回结构，后续可做可视化）
              </span>
              <ScrollArea className="h-80 rounded-lg border bg-muted/40">
                <pre className="p-3 text-xs leading-relaxed">
                  {JSON.stringify(result, null, 2)}
                </pre>
              </ScrollArea>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
