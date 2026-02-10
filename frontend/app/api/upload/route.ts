import { env } from "@/lib/env";
import { getErrorDetail, readProxyPayload } from "@/lib/proxy";

export async function POST(request: Request) {
  try {
    const formData = await request.formData();

    // Forward the file upload to the backend
    const backendResponse = await fetch(`${env.BACKEND_URL}/upload`, {
      method: "POST",
      body: formData,
    });

    if (!backendResponse.ok) {
      const payload = await readProxyPayload(backendResponse);
      return Response.json(
        { detail: getErrorDetail(payload, "Upload failed") },
        { status: backendResponse.status }
      );
    }

    const payload = await readProxyPayload(backendResponse);
    return Response.json(payload);

  } catch (error) {
    console.error("Error in upload proxy:", error);
    return Response.json(
      { detail: "Internal server error" },
      { status: 500 }
    );
  }
}
