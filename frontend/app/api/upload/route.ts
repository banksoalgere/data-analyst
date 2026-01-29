import { env } from "@/lib/env";

export async function POST(request: Request) {
  try {
    const formData = await request.formData();

    // Forward the file upload to the backend
    const backendResponse = await fetch(`${env.BACKEND_URL}/upload`, {
      method: "POST",
      body: formData,
    });

    if (!backendResponse.ok) {
      const errorData = await backendResponse.json();
      return Response.json(
        { detail: errorData.detail || "Upload failed" },
        { status: backendResponse.status }
      );
    }

    const result = await backendResponse.json();
    return Response.json(result);

  } catch (error) {
    console.error("Error in upload proxy:", error);
    return Response.json(
      { detail: "Internal server error" },
      { status: 500 }
    );
  }
}
