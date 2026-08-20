import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { cn } from "@/lib/utils";

/** Markdown 渲染：prose 排版 + GFM（表格/删除线/任务列表），适配暗色模式。 */
export function Markdown({ content, className }: { content: string; className?: string }) {
  return (
    <div className={cn("prose prose-neutral dark:prose-invert max-w-none text-sm", className)}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a: ({ node: _node, ...props }) => (
            <a {...props} target="_blank" rel="noreferrer" className="text-primary underline underline-offset-2" />
          ),
          table: ({ node: _node, ...props }) => (
            <div className="overflow-x-auto rounded-lg border">
              <table {...props} className="w-full text-sm" />
            </div>
          ),
          pre: ({ node: _node, ...props }) => (
            <pre
              {...props}
              className="overflow-x-auto rounded-lg bg-muted px-3 py-2 text-xs leading-relaxed"
            />
          ),
          code: ({ node: _node, className: codeClassName, ...props }) => {
            const isBlock = (codeClassName ?? "").includes("language-");
            if (isBlock) {
              return <code {...props} className={codeClassName} />;
            }
            return (
              <code
                {...props}
                className="rounded bg-muted px-1.5 py-0.5 text-[0.85em] font-medium text-foreground"
              />
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
