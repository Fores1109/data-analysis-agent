/**
 * BFF 代理：把浏览器的同源 /api/* 请求转发到 FastAPI（api/main.py）。
 * - 浏览器只与 Next.js 同源通信，后端无需配置 CORS；
 * - API_BASE 仅存在于服务端环境变量，密钥/地址不会暴露给浏览器；
 * - 转发保留 method / query / body / content-type；
 * - 响应体以流式透传（支持 SSE 流式输出，如 /api/analyze/stream）。
 *
 * 启动后端：uvicorn api.main:app --host 0.0.0.0 --port 8000
 */
import { NextRequest, NextResponse } from "next/server";

const API_BASE = (process.env.API_BASE || "http://localhost:8000").replace(/\/+$/, "");

async function proxy(
  req: NextRequest,
  ctx: RouteContext<"/api/[...path]">,
  method: string,
): Promise<Response> {
  const { path } = await ctx.params;
  // FastAPI 的 /health 在根路径，其余接口都在 /api/ 下（如 /api/analyze）
  const fastApiPath = path[0] === "health" ? "/health" : `/api/${path.join("/")}`;
  const target = `${API_BASE}${fastApiPath}${req.nextUrl.search}`;

  const headers: Record<string, string> = {};
  const contentType = req.headers.get("content-type");
  if (contentType) headers["content-type"] = contentType;

  const body = method === "GET" || method === "HEAD" ? undefined : await req.arrayBuffer();

  let res: Response;
  try {
    res = await fetch(target, { method, headers, body });
  } catch (e) {
    return NextResponse.json(
      { detail: `无法连接 FastAPI 后端（${API_BASE}）：${e instanceof Error ? e.message : String(e)}` },
      { status: 502 },
    );
  }

  // 流式透传上游响应体（SSE 场景保持逐块下发）
  return new Response(res.body, {
    status: res.status,
    headers: {
      "content-type": res.headers.get("content-type") ?? "application/json",
      "cache-control": "no-store",
    },
  });
}

export const GET = (req: NextRequest, ctx: RouteContext<"/api/[...path]">) => proxy(req, ctx, "GET");
export const POST = (req: NextRequest, ctx: RouteContext<"/api/[...path]">) => proxy(req, ctx, "POST");
export const PUT = (req: NextRequest, ctx: RouteContext<"/api/[...path]">) => proxy(req, ctx, "PUT");
export const DELETE = (req: NextRequest, ctx: RouteContext<"/api/[...path]">) => proxy(req, ctx, "DELETE");
export const PATCH = (req: NextRequest, ctx: RouteContext<"/api/[...path]">) => proxy(req, ctx, "PATCH");
export const OPTIONS = (req: NextRequest, ctx: RouteContext<"/api/[...path]">) => proxy(req, ctx, "OPTIONS");
