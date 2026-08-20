"use client";

import { useEffect, useRef } from "react";
import type { ChartFigure } from "@/lib/types";

type PlotlyModule = typeof import("plotly.js-dist-min");

/** plotly.js 图表渲染：接收后端返回的 figure JSON（data/layout/config）。 */
export function PlotChart({ figure, height = 480 }: { figure: ChartFigure; height?: number }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    let plotly: PlotlyModule["default"] | null = null;

    (async () => {
      const mod = await import("plotly.js-dist-min");
      const P = (mod.default ?? mod) as PlotlyModule["default"];
      plotly = P;
      if (cancelled || !ref.current) return;

      const f = figure as { data?: unknown; layout?: unknown; config?: unknown };
      void P.react(ref.current, f.data ?? [], f.layout ?? {}, {
        responsive: true,
        displaylogo: false,
        ...((f.config ?? {}) as object),
      });
    })();

    return () => {
      cancelled = true;
      if (plotly && ref.current) plotly.purge(ref.current);
    };
  }, [figure]);

  return <div ref={ref} className="w-full" style={{ height }} />;
}
