import { env } from "@/lib/env";

export async function POST(request: Request) {
  try {
    const body = await request.json();

    const backendResponse = await fetch(`${env.BACKEND_URL}/actions/draft`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    const payload = await backendResponse.json();
    if (!backendResponse.ok) {
      return Response.json(
        { detail: payload.detail || "Failed to draft actions" },
        { status: backendResponse.status }
      );
    }

    return Response.json(payload);
  } catch (error) {
    console.error("Error in action draft proxy:", error);
    return Response.json(
      { detail: "Internal server error" },
      { status: 500 }
    );
  }
}
