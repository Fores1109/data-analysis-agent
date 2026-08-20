"use client";

import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api";

export function ApiStatus() {
  const [state, setState] = useState<"checking" | "online" | "offline">("checking");

  useEffect(() => {
    let cancelled = false;
    api
      .health()
      .then(() => !cancelled && setState("online"))
      .catch(() => !cancelled && setState("offline"));
    return () => {
      cancelled = true;
    };
  }, []);

  const dot =
    state === "online" ? "bg-emerald-500" : state === "offline" ? "bg-rose-500" : "bg-amber-400 animate-pulse";
  const text =
    state === "online" ? "API 在线" : state === "offline" ? "API 离线" : "检测中…";

  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-sidebar-border px-2.5 py-1 text-xs text-muted-foreground">
      <span className={cn("size-1.5 rounded-full", dot)} />
      {text}
    </span>
  );
}
