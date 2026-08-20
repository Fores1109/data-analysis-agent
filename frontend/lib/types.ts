/** FastAPI 响应类型（与 api/main.py 对应） */

export interface HealthResponse {
  status: string;
}

export interface AnalyzeRequest {
  data_path: string;
  question: string;
}

export interface AnalyzeResponse {
  /** LLM 生成的 markdown 文本答案 */
  answer: string;
}

export interface SqlRequest {
  question: string;
}

export interface SqlGenerateResponse {
  sql: string;
}

export interface SqlOptimizeResponse {
  advice: string;
}

export interface DbSchemaResponse {
  tables: DbTable[];
}

export interface DbTable {
  name: string;
  columns: { name: string; type: string }[];
}

/** /api/ml/train 返回的是 auto_train 的 dict，结构随数据变化，先按 Record 兜底 */
export type MlTrainResponse = Record<string, unknown>;

/** /api/ab/test 返回的是 ab_ttest 的 dict */
export type AbTestResponse = Record<string, unknown>;

/** data/ 目录内的可用数据集（API 按相对路径读取） */
export interface DatasetInfo {
  /** 传给 data_path 的相对路径 */
  path: string;
  name: string;
  description: string;
  format: string;
  size?: string;
}

/** /api/data/preview 返回：列信息 + 前 50 行预览 */
export interface DataPreview {
  shape: [number, number];
  columns: string[];
  dtypes: Record<string, string>;
  head: Record<string, unknown>[];
}

/** /api/ab/test_values 与 /api/ab/test 返回：Welch t 检验结果 */
export interface AbTestResult {
  对照组均值: number;
  实验组均值: number;
  差异: number;
  "t 值": number;
  "p 值": number;
  "Cohen's d": number;
  结论: string;
}

/** /api/ab/proportion 返回：双比例 z 检验结果 */
export interface AbProportionResult {
  对照组转化率: number;
  实验组转化率: number;
  转化率提升: string;
  "z 值": number;
  "p 值": number;
  连续性校正: boolean;
  结论: string;
}

/** /api/ab/simulate 返回：模拟数据 + 检验结果 */
export interface SimulateAbResult {
  n: number;
  control_mean: number;
  treatment_mean: number;
  control: number[];
  treatment: number[];
  test: AbTestResult;
}

/** OLS 系数行 */
export interface CoefRow {
  系数: number | null;
  标准误: number | null;
  t: number | null;
  p: number | null;
  "95%置信区间": [number | null, number | null];
}

/** /api/causal/ols 返回：多元回归结果 */
export interface OlsResult {
  系数表: Record<string, CoefRow>;
  "R²": number | null;
  样本量: number;
  自由度: number;
  F: number | null;
  F_p: number | null;
  稳健标准误: string;
  提示: string;
}

/** /api/causal/did 返回：双重差分结果 */
export interface DidResult {
  "DID 估计值": number | null;
  "p 值": number | null;
  显著性: string;
  "95%置信区间": [number | null, number | null] | null;
  完整回归: OlsResult;
  提示: string;
}

/** /api/charts/generate 返回：plotly figure JSON（data / layout / config） */
export type ChartFigure = Record<string, unknown>;

/** 报告用问答对 */
export interface ReportQaPair {
  question: string;
  answer: string;
}

/** /api/report/generate 返回：Markdown + HTML 报告 */
export interface ReportResponse {
  markdown: string;
  html: string;
  saved_path: string | null;
}

export interface ApiError {
  /** HTTP 状态码 */
  status: number;
  /** FastAPI 的 detail 字段（可能是字符串或结构） */
  detail: string;
}

/** data/ 目录内的可用数据集（API 按相对路径读取） */
export interface DatasetInfo {
  /** 传给 data_path 的相对路径 */
  path: string;
  name: string;
  description: string;
  format: string;
  size?: string;
}
