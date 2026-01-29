import { env } from "@/lib/env";

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
      const errorData = await backendResponse.json();
      return Response.json(
        { detail: errorData.detail || "Analysis failed" },
        { status: backendResponse.status }
      );
    }

    const result = await backendResponse.json();
    return Response.json(result);

  } catch (error) {
    console.error("Error in analyze proxy:", error);
    return Response.json(
      { detail: "Internal server error" },
      { status: 500 }
    );
  }
}
