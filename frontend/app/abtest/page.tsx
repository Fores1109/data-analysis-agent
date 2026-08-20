"use client";

import { useEffect, useRef, useState } from "react";
import { FlaskConical, Loader2 } from "lucide-react";
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
import { Textarea } from "@/components/ui/textarea";
import { ConclusionBanner, StatCards, type StatItem } from "@/components/stat-cards";
import { api, ApiClientError } from "@/lib/api";
import { DATASETS } from "@/lib/datasets";
import { isNumeric, useDataPreview } from "@/lib/use-data-preview";
import type { AbProportionResult, AbTestResult, SimulateAbResult } from "@/lib/types";

const errMsg = (e: unknown) =>
  e instanceof ApiClientError ? e.detail : e instanceof Error ? e.message : String(e);

/** 把 t 检验结果转成统计卡片 */
function abItems(res: AbTestResult): StatItem[] {
  const sig = res["p 值"] < 0.05;
  return [
    { label: "对照组均值", value: res["对照组均值"] },
    { label: "实验组均值", value: res["实验组均值"] },
    { label: "差异", value: res["差异"], tone: sig ? "good" : "default" },
    { label: "t 值", value: res["t 值"] },
    { label: "p 值", value: res["p 值"], tone: sig ? "good" : "bad" },
    { label: "Cohen's d", value: res["Cohen's d"] },
  ];
}

/** 把 z 检验结果转成统计卡片 */
function propItems(res: AbProportionResult): StatItem[] {
  const sig = res["p 值"] < 0.05;
  const pct = (v: number) => `${(v * 100).toFixed(2)}%`;
  return [
    { label: "对照组转化率", value: pct(res["对照组转化率"]) },
    { label: "实验组转化率", value: pct(res["实验组转化率"]) },
    { label: "转化率提升", value: res["转化率提升"], tone: sig ? "good" : "default" },
    { label: "z 值", value: res["z 值"] },
    { label: "p 值", value: res["p 值"], tone: sig ? "good" : "bad" },
    { label: "连续性校正", value: res["连续性校正"] ? "是（Yates）" : "否" },
  ];
}

export default function AbTestPage() {
  const [dataPath, setDataPath] = useState(DATASETS[0].path);
  const { preview, loading: previewLoading, error: previewError } = useDataPreview(dataPath);

  const numeric = (preview?.columns ?? []).filter((c) => isNumeric(preview!.dtypes[c] ?? ""));
  const [ctrlCol, setCtrlCol] = useState("");
  const [trtCol, setTrtCol] = useState("");
  // 预览就绪后按新数据集重置列选择（只在新数据集首次就绪时触发，避免用旧列名）
  const resetRef = useRef<string | null>(null);
  useEffect(() => {
    if (!preview || resetRef.current === dataPath) return;
    resetRef.current = dataPath;
    const num = preview.columns.filter((c) => isNumeric(preview.dtypes[c] ?? ""));
    setCtrlCol(num[0] ?? "");
    setTrtCol(num[1] ?? num[0] ?? "");
  }, [preview, dataPath]);
  const [pasteA, setPasteA] = useState("100,102,99,105,101,98");
  const [pasteB, setPasteB] = useState("108,110,105,112,107,109");
  const [result, setResult] = useState<AbTestResult | null>(null);
  const [running, setRunning] = useState(false);

  // 转化率
  const [cs, setCs] = useState(80);
  const [cn, setCn] = useState(1000);
  const [ts, setTs] = useState(95);
  const [tn, setTn] = useState(1000);
  const [propResult, setPropResult] = useState<AbProportionResult | null>(null);
  const [propRunning, setPropRunning] = useState(false);

  // 模拟
  const [simN, setSimN] = useState(500);
  const [simEff, setSimEff] = useState(0.2);
  const [simSeed, setSimSeed] = useState(42);
  const [simResult, setSimResult] = useState<SimulateAbResult | null>(null);
  const [simRunning, setSimRunning] = useState(false);

  const runCols = async () => {
    if (!ctrlCol || !trtCol || running) return;
    setRunning(true);
    setResult(null);
    try {
      setResult(await api.abTest(dataPath, ctrlCol, trtCol));
    } catch (e) {
      toast.error(errMsg(e));
    } finally {
      setRunning(false);
    }
  };

  const runPaste = async () => {
    if (running) return;
    const parse = (s: string) =>
      s
        .replace(/，/g, ",")
        .split(",")
        .map((x) => Number(x.trim()))
        .filter((x) => Number.isFinite(x));
    const a = parse(pasteA);
    const b = parse(pasteB);
    if (a.length < 3 || b.length < 3) {
      toast.error("每组至少需要 3 个有效数值");
      return;
    }
    setRunning(true);
    setResult(null);
    try {
      setResult(await api.abTestValues(a, b));
    } catch (e) {
      toast.error(errMsg(e));
    } finally {
      setRunning(false);
    }
  };

  const runProp = async () => {
    if (propRunning) return;
    setPropRunning(true);
    setPropResult(null);
    try {
      setPropResult(await api.abProportion(cs, cn, ts, tn));
    } catch (e) {
      toast.error(errMsg(e));
    } finally {
      setPropRunning(false);
    }
  };

  const runSim = async () => {
    if (simRunning) return;
    setSimRunning(true);
    setSimResult(null);
    try {
      setSimResult(await api.abSimulate(simN, simEff, simSeed));
    } catch (e) {
      toast.error(errMsg(e));
    } finally {
      setSimRunning(false);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold tracking-tight">🧪 A/B 实验</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          对两组数据进行统计检验：Welch t 检验（连续指标）· 双比例 z 检验（转化率）·
          模拟实验，含效应量与结论解读。
        </p>
      </div>

      <Tabs defaultValue="ttest">
        <TabsList>
          <TabsTrigger value="ttest">连续指标检验</TabsTrigger>
          <TabsTrigger value="proportion">转化率检验</TabsTrigger>
          <TabsTrigger value="simulate">模拟实验</TabsTrigger>
        </TabsList>

        {/* ---------- 连续指标 ---------- */}
        <TabsContent value="ttest" className="space-y-4 pt-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <FlaskConical className="size-4 text-indigo-500" /> Welch t 检验（两组均值差异）
              </CardTitle>
              <CardDescription>选择「数据集两列」或「手动粘贴两组数值」。</CardDescription>
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
                  <Label>对照组列（A）</Label>
                  <Select value={ctrlCol} onValueChange={setCtrlCol}>
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
                  <Label>实验组列（B）</Label>
                  <Select value={trtCol} onValueChange={setTrtCol}>
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
              </div>

              <div className="rounded-lg border border-dashed p-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label>对照组数值（逗号分隔）</Label>
                    <Textarea rows={3} value={pasteA} onChange={(e) => setPasteA(e.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <Label>实验组数值（逗号分隔）</Label>
                    <Textarea rows={3} value={pasteB} onChange={(e) => setPasteB(e.target.value)} />
                  </div>
                </div>
                <Button className="mt-3" variant="outline" size="sm" onClick={runPaste} disabled={running}>
                  {running && <Loader2 className="size-4 animate-spin" />} 粘贴数值运行检验
                </Button>
              </div>

              <Button onClick={runCols} disabled={running || !ctrlCol || !trtCol}>
                {running && <Loader2 className="size-4 animate-spin" />}
                运行 t 检验
              </Button>

              {result && (
                <div className="space-y-3">
                  <StatCards items={abItems(result)} />
                  <ConclusionBanner text={result["结论"]} />
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ---------- 转化率 ---------- */}
        <TabsContent value="proportion" className="space-y-4 pt-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <FlaskConical className="size-4 text-indigo-500" /> 双比例 z 检验（转化率）
              </CardTitle>
              <CardDescription>输入两组实验的成功数与总人数（默认带 Yates 连续性校正，更保守）。</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-4">
                <div className="space-y-2">
                  <Label htmlFor="cs">对照组成功数</Label>
                  <Input id="cs" type="number" min={0} value={cs} onChange={(e) => setCs(Number(e.target.value))} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="cn">对照组总人数</Label>
                  <Input id="cn" type="number" min={1} value={cn} onChange={(e) => setCn(Number(e.target.value))} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="ts">实验组成功数</Label>
                  <Input id="ts" type="number" min={0} value={ts} onChange={(e) => setTs(Number(e.target.value))} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="tn">实验组总人数</Label>
                  <Input id="tn" type="number" min={1} value={tn} onChange={(e) => setTn(Number(e.target.value))} />
                </div>
              </div>
              <Button onClick={runProp} disabled={propRunning}>
                {propRunning && <Loader2 className="size-4 animate-spin" />} 运行转化率检验
              </Button>
              {propResult && (
                <div className="space-y-3">
                  <StatCards items={propItems(propResult)} />
                  <ConclusionBanner text={propResult["结论"]} />
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ---------- 模拟实验 ---------- */}
        <TabsContent value="simulate" className="space-y-4 pt-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <FlaskConical className="size-4 text-indigo-500" /> 模拟 A/B 实验
              </CardTitle>
              <CardDescription>
                生成两组模拟数据并检验：把样本量调大、效应量调大，观察 p 值如何变化。
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-3">
                <div className="space-y-2">
                  <Label htmlFor="simN">每组样本量</Label>
                  <Input id="simN" type="number" min={10} max={20000} step={50} value={simN} onChange={(e) => setSimN(Number(e.target.value))} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="simEff">效应量（Cohen's d）</Label>
                  <Input id="simEff" type="number" min={0} max={2} step={0.05} value={simEff} onChange={(e) => setSimEff(Number(e.target.value))} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="simSeed">随机种子</Label>
                  <Input id="simSeed" type="number" min={0} max={99999} value={simSeed} onChange={(e) => setSimSeed(Number(e.target.value))} />
                </div>
              </div>
              <Button onClick={runSim} disabled={simRunning}>
                {simRunning && <Loader2 className="size-4 animate-spin" />} 模拟并检验
              </Button>
              {simResult && (
                <div className="space-y-3">
                  <StatCards
                    items={[
                      { label: "每组样本量", value: simResult.n },
                      { label: "对照组均值", value: simResult.control_mean },
                      { label: "实验组均值", value: simResult.treatment_mean },
                    ]}
                    cols={3}
                  />
                  <StatCards items={abItems(simResult.test)} />
                  <ConclusionBanner text={simResult.test["结论"]} />
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
