import { env } from "@/lib/env";

export async function POST(request: Request) {
  try {
    const body = await request.json();

    const backendResponse = await fetch(`${env.BACKEND_URL}/analyze/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!backendResponse.ok) {
      let detail = "Analysis stream failed";
      try {
        const payload = await backendResponse.json();
        if (payload && typeof payload.detail === "string" && payload.detail.trim()) {
          detail = payload.detail;
        }
      } catch {
        // no-op
      }

      return Response.json({ detail }, { status: backendResponse.status });
    }

    return new Response(backendResponse.body, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
      },
    });
  } catch (error) {
    console.error("Error in analyze stream proxy:", error);
    return Response.json(
      { detail: "Internal server error" },
      { status: 500 }
    );
  }
}

