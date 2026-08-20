"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { DataPreview } from "@/lib/types";

/** 按 data_path 加载数据集的列信息/预览；dataPath 变化时自动重新加载。 */
export function useDataPreview(dataPath: string | null) {
  const [preview, setPreview] = useState<DataPreview | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (path: string) => {
    setLoading(true);
    setError(null);
    try {
      setPreview(await api.dataPreview(path));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setPreview(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (dataPath) void load(dataPath);
  }, [dataPath, load]);

  return { preview, loading, error, reload: load };
}

/** 判断 dtype 是否为数值型 */
export function isNumeric(dtype: string): boolean {
  return /^(int|float|uint|decimal)/i.test(dtype);
}

/** 从预览中取数值列 */
export function numericColumns(preview: DataPreview | null): string[] {
  if (!preview) return [];
  return preview.columns.filter((c) => isNumeric(preview.dtypes[c] ?? ""));
}
