"use client";

/** SSE 流式读取：POST /api/analyze/stream，逐 token 回调。 */

export interface StreamHandlers {
  onToken: (token: string) => void;
  onError: (message: string) => void;
  onDone: () => void;
  /** 传入 AbortController.signal 可中途停止 */
  signal?: AbortSignal;
}

export async function streamAnalyze(
  dataPath: string,
  question: string,
  handlers: StreamHandlers,
): Promise<void> {
  let res: Response;
  try {
    res = await fetch("/api/analyze/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ data_path: dataPath, question }),
      signal: handlers.signal,
    });
  } catch (e) {
    if (!handlers.signal?.aborted) {
      handlers.onError(e instanceof Error ? e.message : String(e));
    }
    handlers.onDone();
    return;
  }

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const j = await res.json();
      detail = typeof j.detail === "string" ? j.detail : JSON.stringify(j);
    } catch {
      /* 保持默认 */
    }
    handlers.onError(detail);
    handlers.onDone();
    return;
  }

  if (!res.body) {
    handlers.onError("响应无数据流");
    handlers.onDone();
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let finished = false;

  const doneOnce = () => {
    if (!finished) {
      finished = true;
      handlers.onDone();
    }
  };

  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split("\n\n");
      buffer = events.pop() ?? "";
      for (const ev of events) {
        const line = ev.trim();
        if (!line.startsWith("data:")) continue;
        const payload = line.slice(5).trim();
        if (payload === "[DONE]") {
          doneOnce();
          continue;
        }
        try {
          const obj = JSON.parse(payload) as { token?: string; error?: string };
          if (typeof obj.token === "string") handlers.onToken(obj.token);
          else if (typeof obj.error === "string") handlers.onError(obj.error);
        } catch {
          /* 半行不完整，忽略 */
        }
      }
    }
  } catch (e) {
    if (!handlers.signal?.aborted) {
      handlers.onError(e instanceof Error ? e.message : String(e));
    }
  } finally {
    reader.releaseLock();
    doneOnce();
  }
}
