import { env } from "@/lib/env";
import { getErrorDetail, readProxyPayload } from "@/lib/proxy";

export async function POST(request: Request) {
  try {
    const body = await request.json();

    const backendResponse = await fetch(`${env.BACKEND_URL}/causal-lab`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    const payload = await readProxyPayload(backendResponse);
    if (!backendResponse.ok) {
      return Response.json(
        { detail: getErrorDetail(payload, "Causal lab failed") },
        { status: backendResponse.status }
      );
    }

    return Response.json(payload);
  } catch (error) {
    console.error("Error in causal lab proxy:", error);
    return Response.json(
      { detail: "Internal server error" },
      { status: 500 }
    );
  }
}
