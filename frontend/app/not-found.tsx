import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 text-center">
      <p className="text-6xl font-black tracking-tight text-muted-foreground/30">404</p>
      <h2 className="text-lg font-semibold">页面不存在</h2>
      <p className="text-sm text-muted-foreground">你访问的页面可能已被移动或删除。</p>
      <Button asChild>
        <Link href="/">返回仪表盘</Link>
      </Button>
    </div>
  );
}
