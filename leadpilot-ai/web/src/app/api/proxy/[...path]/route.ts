import { NextRequest, NextResponse } from "next/server";

const AI_SERVICE_URL = process.env.AI_SERVICE_URL || "http://localhost:8000";
const AI_SERVICE_API_KEY = process.env.AI_SERVICE_API_KEY || "lp_secret_key_demo_2026";

async function handleProxy(req: NextRequest, { params }: { params: { path: string[] } }) {
  const path = params.path.join("/");
  const url = new URL(`${AI_SERVICE_URL}/${path}`);

  // Forward query parameters
  req.nextUrl.searchParams.forEach((val, key) => {
    url.searchParams.set(key, val);
  });

  const headers = new Headers();
  headers.set("X-API-Key", AI_SERVICE_API_KEY);

  const contentType = req.headers.get("content-type");
  if (contentType) {
    headers.set("content-type", contentType);
  }

  let body: any = null;
  if (req.method !== "GET" && req.method !== "HEAD") {
    body = await req.blob();
  }

  try {
    const response = await fetch(url.toString(), {
      method: req.method,
      headers: headers,
      body: body,
      cache: "no-store",
    });

    const data = await response.text();
    return new NextResponse(data, {
      status: response.status,
      headers: {
        "content-type": response.headers.get("content-type") || "application/json",
      },
    });
  } catch (error: any) {
    return NextResponse.json(
      { error: { code: "PROXY_ERROR", message: error.message || "Failed to reach AI service" } },
      { status: 502 }
    );
  }
}

export const GET = handleProxy;
export const POST = handleProxy;
export const PUT = handleProxy;
export const DELETE = handleProxy;
