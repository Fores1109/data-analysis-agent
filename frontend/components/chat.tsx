"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { Bot, Send, Square } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Markdown } from "@/components/markdown";
import { cn } from "@/lib/utils";
import { streamAnalyze } from "@/lib/sse";
import { appendQaHistory, loadQaHistory } from "@/lib/storage";
import { DATASETS } from "@/lib/datasets";

interface Message {
  id: number;
  role: "user" | "assistant";
  content: string;
  error?: boolean;
}

const EXAMPLE_QUESTIONS = [
  "哪个月的销售额最高？",
  "各城市平均销售额是多少？",
  "数据里有没有明显异常值？",
];

export function Chat() {
  const [dataPath, setDataPath] = useState(DATASETS[0].path);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);
  const idRef = useRef(1);
  const abortRef = useRef<AbortController | null>(null);
  const answerRef = useRef("");
  const bottomRef = useRef<HTMLDivElement>(null);

  // 挂载后从 localStorage 恢复最近 20 条问答（避免 SSR 水合不一致）
  useEffect(() => {
    const history = loadQaHistory().slice(-20);
    if (history.length) {
      const restored: Message[] = history.flatMap((qa) => [
        { id: idRef.current++, role: "user", content: qa.question },
        { id: idRef.current++, role: "assistant", content: qa.answer },
      ]);
      setMessages(restored);
    }
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, pending]);

  const appendToken = (id: number, token: string) => {
    answerRef.current += token;
    setMessages((ms) => ms.map((m) => (m.id === id ? { ...m, content: m.content + token } : m)));
  };

  const send = async (text?: string) => {
    const question = (text ?? input).trim();
    if (!question || pending) return;
    setInput("");
    answerRef.current = "";

    const userMsg: Message = { id: idRef.current++, role: "user", content: question };
    const asstMsg: Message = { id: idRef.current++, role: "assistant", content: "" };
    setMessages((ms) => [...ms, userMsg, asstMsg]);
    setPending(true);

    const controller = new AbortController();
    abortRef.current = controller;
    let errored = false;

    await streamAnalyze(dataPath, question, {
      signal: controller.signal,
      onToken: (t) => appendToken(asstMsg.id, t),
      onError: (m) => {
        errored = true;
        setMessages((ms) =>
          ms.map((x) => (x.id === asstMsg.id ? { ...x, content: `❌ ${m}`, error: true } : x)),
        );
      },
      onDone: () => setPending(false),
    });

    // 完整问答写入 localStorage（供报告页使用）；中途停止/出错不写
    if (!errored && !controller.signal.aborted && answerRef.current.trim()) {
      appendQaHistory({ question, answer: answerRef.current });
    }
    abortRef.current = null;
  };

  const stop = () => abortRef.current?.abort();

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    void send();
  };

  return (
    <div className="flex h-[calc(100vh-11.5rem)] min-h-[480px] flex-col gap-4">
      {/* 数据集选择 */}
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
        <span className="text-xs text-muted-foreground">（data_path: {dataPath}）</span>
      </div>

      {/* 消息区 */}
      <ScrollArea className="flex-1 rounded-xl border bg-card">
        <div className="space-y-4 p-4">
          {messages.length === 0 && (
            <div className="flex h-full flex-col items-center justify-center gap-3 py-16 text-center">
              <div className="flex size-12 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600 text-white shadow-lg shadow-indigo-500/25">
                <Bot className="size-6" />
              </div>
              <div>
                <p className="text-sm font-medium">对数据用自然语言提问</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  AI 会生成并执行只读 pandas 代码来分析，回答流式输出，支持表格与 Markdown
                </p>
              </div>
              <div className="flex flex-wrap justify-center gap-2 pt-2">
                {EXAMPLE_QUESTIONS.map((q) => (
                  <Button
                    key={q}
                    variant="outline"
                    size="sm"
                    className="rounded-full text-xs"
                    onClick={() => void send(q)}
                  >
                    {q}
                  </Button>
                ))}
              </div>
            </div>
          )}

          {messages.map((m) =>
            m.role === "user" ? (
              <div key={m.id} className="flex justify-end">
                <div className="max-w-[80%] rounded-2xl rounded-br-md bg-primary px-4 py-2.5 text-sm text-primary-foreground">
                  {m.content}
                </div>
              </div>
            ) : (
              <div key={m.id} className="flex items-start gap-3">
                <div className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 text-white">
                  <Bot className="size-4" />
                </div>
                <div
                  className={cn(
                    "max-w-[85%] rounded-2xl rounded-tl-md border bg-muted/30 px-4 py-3",
                    m.error && "border-destructive/40 bg-destructive/5",
                  )}
                >
                  {m.error ? (
                    <p className="text-sm text-destructive">{m.content}</p>
                  ) : m.content ? (
                    <Markdown content={m.content} />
                  ) : (
                    <p className="text-xs text-muted-foreground">思考中…</p>
                  )}
                </div>
              </div>
            ),
          )}
          <div ref={bottomRef} />
        </div>
      </ScrollArea>

      {/* 输入区 */}
      <form onSubmit={onSubmit} className="flex items-end gap-2">
        <Textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="输入问题，Enter 发送，Shift+Enter 换行"
          rows={1}
          className="max-h-40 min-h-11 flex-1 resize-none"
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              void send();
            }
          }}
        />
        {pending ? (
          <Button type="button" size="icon" variant="outline" className="size-11 shrink-0" onClick={stop}>
            <Square className="size-4 fill-current" />
            <span className="sr-only">停止</span>
          </Button>
        ) : (
          <Button type="submit" size="icon" className="size-11 shrink-0" disabled={!input.trim()}>
            <Send className="size-4" />
            <span className="sr-only">发送</span>
          </Button>
        )}
      </form>
    </div>
  );
}
