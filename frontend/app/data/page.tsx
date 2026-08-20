import type { Metadata } from "next";
import { Database, FileSpreadsheet } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { DATASETS } from "@/lib/datasets";

export const metadata: Metadata = {
  title: "数据源",
  description: "查看后端 data/ 目录中可用的数据集",
};

export default function DataPage() {
  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold tracking-tight">📂 数据源</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          后端 FastAPI 仅允许按相对路径读取项目 <code className="rounded bg-muted px-1">data/</code> 目录内的文件
          （<code className="rounded bg-muted px-1">data_path</code> 白名单校验，防路径穿越）。
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {DATASETS.map((d) => (
          <Card key={d.path} className="transition-shadow hover:shadow-md">
            <CardHeader>
              <div className="flex items-start justify-between gap-2">
                <CardTitle className="flex items-center gap-2 text-base">
                  <FileSpreadsheet className="size-4 text-indigo-500" />
                  {d.name}
                </CardTitle>
                <Badge variant="secondary" className="shrink-0">
                  {d.format}
                </Badge>
              </div>
              <CardDescription>{d.description}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2 rounded-lg bg-muted/50 px-3 py-2">
                <Database className="size-3.5 shrink-0 text-muted-foreground" />
                <code className="truncate text-xs">{d.path}</code>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
