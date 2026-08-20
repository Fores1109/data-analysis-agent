"use client";

import { useEffect, useRef, useState } from "react";
import { Link2, Loader2 } from "lucide-react";
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { CoefTable } from "@/components/coef-table";
import { Note, StatCards } from "@/components/stat-cards";
import { api, ApiClientError } from "@/lib/api";
import { DATASETS } from "@/lib/datasets";
import { isNumeric, useDataPreview } from "@/lib/use-data-preview";
import type { DidResult, OlsResult } from "@/lib/types";

const errMsg = (e: unknown) =>
  e instanceof ApiClientError ? e.detail : e instanceof Error ? e.message : String(e);

/** 可选列的多选 chips */
function ChipGroup({
  options,
  selected,
  onChange,
  emptyHint = "该数据集没有可选的数值列",
}: {
  options: string[];
  selected: string[];
  onChange: (v: string[]) => void;
  emptyHint?: string;
}) {
  if (options.length === 0) {
    return <p className="text-xs text-muted-foreground">{emptyHint}</p>;
  }
  const toggle = (opt: string) =>
    onChange(selected.includes(opt) ? selected.filter((x) => x !== opt) : [...selected, opt]);
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((opt) => (
        <Button
          key={opt}
          type="button"
          size="sm"
          variant={selected.includes(opt) ? "default" : "outline"}
          className="rounded-full text-xs"
          onClick={() => toggle(opt)}
        >
          {opt}
        </Button>
      ))}
    </div>
  );
}

/** 回归逐变量解释（镜像 Streamlit 版的行为） */
function Interpretations({ res, outcome }: { res: OlsResult; outcome: string }) {
  const rows = Object.entries(res["系数表"]).filter(([name]) => name !== "const");
  if (rows.length === 0) return null;
  return (
    <div className="space-y-1.5 rounded-lg border bg-card p-4 text-sm">
      <p className="text-xs font-medium text-muted-foreground">📖 逐变量解释</p>
      {rows.map(([name, r]) => {
        const coef = r["系数"];
        if (coef === null) {
          return (
            <p key={name}>
              <strong>{name}</strong>：无法估计（数据不足或完全共线）。
            </p>
          );
        }
        const sig = r.p !== null && r.p !== undefined && r.p < 0.05;
        const dir = coef >= 0 ? "增加" : "减少";
        return (
          <p key={name} className="leading-relaxed">
            <strong>{name}</strong>：系数 {coef >= 0 ? "+" : ""}
            {coef.toFixed(4)}（p={r.p === null ? "—" : r.p.toFixed(4)}，
            {sig ? "显著" : "不显著"}）。在控制其他变量后，{name} 每增加 1 个单位，
            {outcome} 平均{dir} {Math.abs(coef).toFixed(4)}。
          </p>
        );
      })}
    </div>
  );
}

export default function CausalPage() {
  const [dataPath, setDataPath] = useState(DATASETS[0].path);
  const { preview, loading: previewLoading, error: previewError } = useDataPreview(dataPath);

  const allCols = preview?.columns ?? [];
  const numeric = allCols.filter((c) => isNumeric(preview!.dtypes[c] ?? ""));

  // ---- OLS ----
  const [outcome, setOutcome] = useState("");
  const [predictors, setPredictors] = useState<string[]>([]);
  const [robust, setRobust] = useState("HC1");
  const [olsResult, setOlsResult] = useState<OlsResult | null>(null);
  const [olsRunning, setOlsRunning] = useState(false);

  // 预览就绪后按新数据集重置字段选择（只在新数据集首次就绪时触发，避免用旧列名）
  const resetRef = useRef<string | null>(null);
  useEffect(() => {
    if (!preview || resetRef.current === dataPath) return;
    resetRef.current = dataPath;
    const num = preview.columns.filter((c) => isNumeric(preview.dtypes[c] ?? ""));
    setOutcome(num[0] ?? "");
    setPredictors([]);
    setGroupCol("");
    setTimeCol("");
    setConfounders([]);
    setOlsResult(null);
    setDidResult(null);
  }, [preview, dataPath]); // eslint-disable-line react-hooks/exhaustive-deps

  // ---- DID ----
  const [groupCol, setGroupCol] = useState("");
  const [timeCol, setTimeCol] = useState("");
  const [treatedValue, setTreatedValue] = useState("1");
  const [postValue, setPostValue] = useState("1");
  const [confounders, setConfounders] = useState<string[]>([]);
  const [didResult, setDidResult] = useState<DidResult | null>(null);
  const [didRunning, setDidRunning] = useState(false);

  const runOls = async () => {
    if (!outcome || predictors.length === 0 || olsRunning) return;
    setOlsRunning(true);
    setOlsResult(null);
    try {
      setOlsResult(await api.causalOls(dataPath, outcome, predictors, robust));
    } catch (e) {
      toast.error(errMsg(e));
    } finally {
      setOlsRunning(false);
    }
  };

  const runDid = async () => {
    if (!outcome || !groupCol || !timeCol || didRunning) return;
    setDidRunning(true);
    setDidResult(null);
    try {
      setDidResult(
        await api.causalDid({
          dataPath,
          outcome,
          groupCol,
          treatedValue,
          timeCol,
          postValue,
          confounders,
          robust,
        }),
      );
    } catch (e) {
      toast.error(errMsg(e));
    } finally {
      setDidRunning(false);
    }
  };

  const predictorOptions = numeric.filter((c) => c !== outcome);
  const confounderOptions = numeric.filter((c) => c !== outcome && c !== groupCol && c !== timeCol);

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold tracking-tight">🔗 因果推断</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          教学级实现：多元回归控制已观测混杂 / 双重差分 DID。回归只能控制已观测变量，
          不能证明因果——请结合实验设计解读。
        </p>
      </div>

      <Tabs defaultValue="ols">
        <TabsList>
          <TabsTrigger value="ols">多元回归（控制混杂）</TabsTrigger>
          <TabsTrigger value="did">双重差分 DID</TabsTrigger>
        </TabsList>

        {/* ---------- OLS ---------- */}
        <TabsContent value="ols" className="space-y-4 pt-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Link2 className="size-4 text-indigo-500" /> 多元回归
              </CardTitle>
              <CardDescription>
                结果变量 Y + 解释变量 X（建议数值列）；默认 HC1 异方差稳健标准误。
              </CardDescription>
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

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label>结果变量 Y（被解释）</Label>
                  <Select value={outcome} onValueChange={setOutcome}>
                    <SelectTrigger>
                      <SelectValue placeholder={numeric.length ? "选择数值列" : "当前数据集无数值列"} />
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
                <div className="space-y-2">
                  <Label>稳健标准误</Label>
                  <Select value={robust} onValueChange={setRobust}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="HC1">HC1 异方差稳健</SelectItem>
                      <SelectItem value="nonrobust">普通标准误</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label>解释变量 X（点选，可多选）</Label>
                <ChipGroup
                  options={predictorOptions}
                  selected={predictors}
                  onChange={setPredictors}
                />
              </div>

              <Button onClick={runOls} disabled={olsRunning || !outcome || predictors.length === 0}>
                {olsRunning && <Loader2 className="size-4 animate-spin" />} 运行回归
              </Button>

              {olsResult && (
                <div className="space-y-4">
                  <StatCards
                    cols={4}
                    items={[
                      { label: "R²", value: olsResult["R²"] ?? "—", tone: "accent" },
                      { label: "样本量", value: olsResult["样本量"] },
                      { label: "F", value: olsResult["F"] ?? "—" },
                      { label: "F p 值", value: olsResult["F_p"] ?? "—" },
                    ]}
                  />
                  <CoefTable coefs={olsResult["系数表"]} />
                  <Interpretations res={olsResult} outcome={outcome} />
                  <Note>{olsResult["提示"]}</Note>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ---------- DID ---------- */}
        <TabsContent value="did" className="space-y-4 pt-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Link2 className="size-4 text-indigo-500" /> 双重差分 DID
              </CardTitle>
              <CardDescription>
                DID 需要面板数据：每个单元同时有「实验组/对照组」标识与「前/后」两个时点。
              </CardDescription>
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
                  <Label>结果变量 Y</Label>
                  <Select value={outcome} onValueChange={setOutcome}>
                    <SelectTrigger>
                      <SelectValue placeholder={numeric.length ? "选择数值列" : "无数值列"} />
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
                <div className="space-y-2">
                  <Label>分组列（实验/对照）</Label>
                  <Select value={groupCol} onValueChange={setGroupCol}>
                    <SelectTrigger>
                      <SelectValue placeholder="选择分组列" />
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
                <div className="space-y-2">
                  <Label>时点列（前/后）</Label>
                  <Select value={timeCol} onValueChange={setTimeCol}>
                    <SelectTrigger>
                      <SelectValue placeholder="选择时点列" />
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
              </div>

              <div className="grid gap-4 sm:grid-cols-3">
                <div className="space-y-2">
                  <Label htmlFor="did-tv">实验组标识值</Label>
                  <Input id="did-tv" value={treatedValue} onChange={(e) => setTreatedValue(e.target.value)} placeholder="如 1" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="did-pv">后时点标识值</Label>
                  <Input id="did-pv" value={postValue} onChange={(e) => setPostValue(e.target.value)} placeholder="如 1" />
                </div>
                <div className="space-y-2">
                  <Label>稳健标准误</Label>
                  <Select value={robust} onValueChange={setRobust}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="HC1">HC1 异方差稳健</SelectItem>
                      <SelectItem value="nonrobust">普通标准误</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label>控制变量（可选）</Label>
                <ChipGroup options={confounderOptions} selected={confounders} onChange={setConfounders} />
              </div>

              <Button onClick={runDid} disabled={didRunning || !outcome || !groupCol || !timeCol}>
                {didRunning && <Loader2 className="size-4 animate-spin" />} 运行 DID
              </Button>

              {didResult && (
                <div className="space-y-4">
                  <StatCards
                    items={[
                      {
                        label: "DID 估计值（处理效应）",
                        value: didResult["DID 估计值"] ?? "—",
                        tone: didResult["p 值"] !== null && didResult["p 值"]! < 0.05 ? "good" : "default",
                      },
                      { label: "p 值", value: didResult["p 值"] ?? "—", tone: didResult["p 值"] !== null && didResult["p 值"]! < 0.05 ? "good" : "bad" },
                      { label: "显著性", value: didResult["显著性"] },
                    ]}
                  />
                  {didResult["95%置信区间"] && (
                    <p className="text-sm text-muted-foreground">
                      95% 置信区间：[{didResult["95%置信区间"]![0] ?? "—"},{" "}
                      {didResult["95%置信区间"]![1] ?? "—"}]（{didResult["完整回归"]["稳健标准误"]} 稳健标准误）
                    </p>
                  )}
                  <p className="text-sm leading-relaxed">
                    <strong>解释：</strong>实验组相对对照组在「前后」之间的变化差异为{" "}
                    {didResult["DID 估计值"] ?? "—"} {didResult["显著性"]}，可理解为干预带来的净效应估计。
                  </p>
                  <div className="space-y-2">
                    <p className="text-xs font-medium text-muted-foreground">完整回归表</p>
                    <CoefTable coefs={didResult["完整回归"]["系数表"]} highlight="_treated_post" />
                  </div>
                  <Note>{didResult["提示"]}</Note>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
