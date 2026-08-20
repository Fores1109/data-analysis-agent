/** FastAPI 客户端：经 Next.js BFF 代理（app/api/[...path]/route.ts）转发，浏览器只请求同源 /api/*。 */
import type {
  AbProportionResult,
  AbTestResult,
  AnalyzeRequest,
  AnalyzeResponse,
  ChartFigure,
  DataPreview,
  DidResult,
  DbSchemaResponse,
  HealthResponse,
  MlTrainResponse,
  OlsResult,
  ReportQaPair,
  ReportResponse,
  SimulateAbResult,
  SqlGenerateResponse,
  SqlOptimizeResponse,
} from "./types";

export class ApiClientError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(`API 请求失败（${status}）：${detail}`);
    this.name = "ApiClientError";
    this.status = status;
    this.detail = detail;
  }
}

/** 从 FastAPI 错误响应中提取 detail（可能是字符串或校验错误结构） */
function extractDetail(payload: unknown): string {
  if (!payload || typeof payload !== "object") return String(payload ?? "未知错误");
  const p = payload as Record<string, unknown>;
  if (typeof p.detail === "string") return p.detail;
  if (Array.isArray(p.detail)) {
    return p.detail
      .map((d) => {
        const item = d as Record<string, unknown>;
        const msg = item.msg ?? item.message ?? JSON.stringify(d);
        const loc = Array.isArray(item.loc) ? item.loc.slice(1).join(".") : "";
        return loc ? `${loc}: ${msg}` : String(msg);
      })
      .join("；");
  }
  return JSON.stringify(payload);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(path, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
    });
  } catch (e) {
    throw new Error(
      `无法连接后端（请确认 FastAPI 已启动：uvicorn api.main:app --port 8000）: ${
        e instanceof Error ? e.message : String(e)
      }`,
    );
  }

  const text = await res.text();
  const payload = text ? JSON.parse(text) : null;

  if (!res.ok) {
    throw new ApiClientError(res.status, extractDetail(payload));
  }
  return payload as T;
}

function post<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, { method: "POST", body: JSON.stringify(body) });
}

export const api = {
  health: () => request<HealthResponse>("/api/health"),

  /** 自然语言问答分析 */
  analyze: (dataPath: string, question: string) =>
    post<AnalyzeResponse>("/api/analyze", { data_path: dataPath, question } satisfies AnalyzeRequest),

  /** 自然语言 → SQL */
  generateSql: (question: string) => post<SqlGenerateResponse>("/api/sql/generate", { question }),

  /** SQL 优化建议 */
  optimizeSql: (question: string) => post<SqlOptimizeResponse>("/api/sql/optimize", { question }),

  /** 读取 .env 配置的数据库表结构 */
  dbSchema: () => request<DbSchemaResponse>("/api/db/schema"),

  /** 机器学习自动训练 */
  train: (dataPath: string, target: string) =>
    post<MlTrainResponse>(
      `/api/ml/train?data_path=${encodeURIComponent(dataPath)}&target=${encodeURIComponent(target)}`,
      {},
    ),

  /** 数据集列信息与前 50 行预览（供表单动态取列） */
  dataPreview: (dataPath: string) =>
    request<DataPreview>(`/api/data/preview?data_path=${encodeURIComponent(dataPath)}`),

  /** A/B 检验：数据集两列 Welch t 检验 */
  abTest: (dataPath: string, controlCol: string, treatmentCol: string) =>
    post<AbTestResult>(
      `/api/ab/test?data_path=${encodeURIComponent(dataPath)}&control_col=${encodeURIComponent(
        controlCol,
      )}&treatment_col=${encodeURIComponent(treatmentCol)}`,
      {},
    ),

  /** A/B 检验：直接粘贴两组数值 */
  abTestValues: (control: number[], treatment: number[]) =>
    post<AbTestResult>("/api/ab/test_values", { control, treatment }),

  /** A/B 检验：双比例 z 检验（转化率） */
  abProportion: (cs: number, cn: number, ts: number, tn: number) =>
    post<AbProportionResult>("/api/ab/proportion", {
      control_success: cs,
      control_n: cn,
      treat_success: ts,
      treat_n: tn,
    }),

  /** A/B 模拟实验：生成两组正态数据并检验 */
  abSimulate: (nPerGroup: number, effect: number, seed: number) =>
    post<SimulateAbResult>("/api/ab/simulate", { n_per_group: nPerGroup, effect, seed }),

  /** 因果推断：多元回归（控制混杂） */
  causalOls: (dataPath: string, outcome: string, predictors: string[], robust: string) =>
    post<OlsResult>("/api/causal/ols", { data_path: dataPath, outcome, predictors, robust }),

  /** 因果推断：双重差分 DID */
  causalDid: (opts: {
    dataPath: string;
    outcome: string;
    groupCol: string;
    treatedValue: string;
    timeCol: string;
    postValue: string;
    confounders: string[];
    robust: string;
  }) =>
    post<DidResult>("/api/causal/did", {
      data_path: opts.dataPath,
      outcome: opts.outcome,
      group_col: opts.groupCol,
      treated_value: opts.treatedValue,
      time_col: opts.timeCol,
      post_value: opts.postValue,
      confounders: opts.confounders,
      robust: opts.robust,
    }),

  /** 图表生成：返回 plotly figure JSON */
  chartsGenerate: (req: {
    dataPath: string;
    chartType: string;
    x: string;
    y?: string;
    color?: string;
    bins?: number;
  }) =>
    post<ChartFigure>("/api/charts/generate", {
      data_path: req.dataPath,
      chart_type: req.chartType,
      x: req.x,
      y: req.y ?? "",
      color: req.color ?? "",
      bins: req.bins ?? 30,
    }),

  /** 报告生成：问答记录 + 图表 + 数据概览 → Markdown / HTML */
  reportGenerate: (req: {
    title: string;
    dataName: string;
    dataPath: string;
    qaPairs: ReportQaPair[];
    charts: ChartFigure[];
    save: boolean;
  }) =>
    post<ReportResponse>("/api/report/generate", {
      title: req.title,
      data_name: req.dataName,
      data_path: req.dataPath,
      qa_pairs: req.qaPairs,
      charts: req.charts,
      save: req.save,
    }),
};
