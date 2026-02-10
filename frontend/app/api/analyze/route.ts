import { env } from "@/lib/env";
import { getErrorDetail, readProxyPayload } from "@/lib/proxy";

export async function POST(request: Request) {
  try {
    const body = await request.json();

    // Forward the analyze request to the backend
    const backendResponse = await fetch(`${env.BACKEND_URL}/analyze`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!backendResponse.ok) {
      const payload = await readProxyPayload(backendResponse);
      return Response.json(
        { detail: getErrorDetail(payload, "Analysis failed") },
        { status: backendResponse.status }
      );
    }

    const payload = await readProxyPayload(backendResponse);
    return Response.json(payload);

  } catch (error) {
    console.error("Error in analyze proxy:", error);
    return Response.json(
      { detail: "Internal server error" },
      { status: 500 }
    );
  }
}
