import { env } from "@/lib/env";

export async function POST(request: Request) {
  try {
    const body = await request.json();

    // Forward the streaming request to the backend
    const backendResponse = await fetch(`${env.BACKEND_URL}/chat/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!backendResponse.ok) {
      return new Response(
        JSON.stringify({ error: "Backend service error" }),
        { status: backendResponse.status }
      );
    }

    // Return the streaming response
    return new Response(backendResponse.body, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
      },
    });
  } catch (error) {
    console.error("Error in stream proxy:", error);
    return new Response(
      JSON.stringify({ error: "Internal server error" }),
      { status: 500 }
    );
  }
}
