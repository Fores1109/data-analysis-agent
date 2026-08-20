/** 跨页面会话数据（localStorage）：聊天问答历史 + 报告用图表。 */

export const QA_HISTORY_KEY = "data-agent-qa-history";
export const REPORT_CHARTS_KEY = "data-agent-report-charts";

export interface StoredQa {
  question: string;
  answer: string;
}

function read<T>(key: string, fallback: T): T {
  if (typeof window === "undefined") return fallback;
  try {
    const raw = window.localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}

function write(key: string, value: unknown) {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* 忽略存储失败 */
  }
}

export function loadQaHistory(): StoredQa[] {
  return read<StoredQa[]>(QA_HISTORY_KEY, []);
}

/** 追加一条问答；最多保留 50 条（最早丢弃） */
export function appendQaHistory(qa: StoredQa) {
  const list = loadQaHistory();
  list.push(qa);
  if (list.length > 50) list.splice(0, list.length - 50);
  write(QA_HISTORY_KEY, list);
}

/** 清空问答历史（报告页导出后可调用） */
export function clearQaHistory() {
  write(QA_HISTORY_KEY, []);
}

export function loadReportCharts(): Record<string, unknown>[] {
  return read<Record<string, unknown>[]>(REPORT_CHARTS_KEY, []);
}

/** 把一张图加入报告；最多保留 10 张 */
export function appendReportChart(fig: Record<string, unknown>) {
  const list = loadReportCharts();
  list.push(fig);
  if (list.length > 10) list.splice(0, list.length - 10);
  write(REPORT_CHARTS_KEY, list);
}

export function clearReportCharts() {
  write(REPORT_CHARTS_KEY, []);
}
