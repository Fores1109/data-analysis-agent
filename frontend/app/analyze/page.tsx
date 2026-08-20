import type { Metadata } from "next";
import { Chat } from "@/components/chat";

export const metadata: Metadata = {
  title: "自然语言分析",
  description: "对数据集用自然语言提问，AI 生成并执行只读分析代码",
};

export default function AnalyzePage() {
  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">💬 自然语言问答分析</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            选择数据集后直接提问，Agent 会生成并执行<strong>只读</strong> pandas 代码来分析您的数据。
          </p>
        </div>
      </div>

      <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 px-4 py-3 text-xs leading-relaxed text-muted-foreground">
        🛡️ <strong>安全须知</strong>：AI 生成的代码会在后端沙箱中执行（AST 静态检查 + 受限环境 + 子进程隔离 + 超时熔断），
        仅允许只读分析。请只对您信任的数据提问，不要在包含密钥/密码的文件上使用。
      </div>

      <Chat />
    </div>
  );
}
