import { env } from "@/lib/env";
import { getErrorDetail, readProxyPayload } from "@/lib/proxy";

export async function POST(request: Request) {
  try {
    const body = await request.json();

    const backendResponse = await fetch(`${env.BACKEND_URL}/actions/approve`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    const payload = await readProxyPayload(backendResponse);
    if (!backendResponse.ok) {
      return Response.json(
        { detail: getErrorDetail(payload, "Failed to approve action") },
        { status: backendResponse.status }
      );
    }

    return Response.json(payload);
  } catch (error) {
    console.error("Error in action approve proxy:", error);
    return Response.json(
      { detail: "Internal server error" },
      { status: 500 }
    );
  }
}
