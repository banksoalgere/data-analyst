import { MessageSchema, ChatResponseSchema } from "@/types/chat";
import { env } from "@/lib/env";
import { fetchWithTimeout } from "@/lib/fetch";
import { errorResponse, successResponse, ErrorCodes } from "@/lib/api";

const TIMEOUT_MS = 3000;

export async function POST(request: Request) {
  const requestId = crypto.randomUUID();
  try {
    // STEP 1: Parse and validate incoming JSON
    const body = await request.json();
    const validation = MessageSchema.safeParse(body);

    if (!validation.success) {
      // Return structured validation errors (helps frontend show specific issues)
      return errorResponse(
        ErrorCodes.VALIDATION_ERROR,
        "Invalid request data",
        400,
        validation.error.flatten(),
        requestId
      );
    }

    // STEP 2: Forward to Python backend with timeout
    const backendResponse = await fetchWithTimeout(
      `${env.BACKEND_URL}/chat`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Request-ID": requestId, // Pass ID for log correlation
        },
        body: JSON.stringify(validation.data),
      },
      TIMEOUT_MS
    );

    // STEP 3: Handle non-OK responses from backend
    if (!backendResponse.ok) {
      console.error({ requestId, status: backendResponse.status, msg: "Backend error" });

      // Return 502 Bad Gateway for backend 5xx errors, otherwise pass through status
      return errorResponse(
        ErrorCodes.UPSTREAM_ERROR,
        "Backend service error",
        backendResponse.status >= 500 ? 502 : backendResponse.status,
        undefined,
        requestId
      );
    }

    // STEP 4: Validate backend response shape (catches contract mismatches)
    const data = await backendResponse.json();
    const responseValidation = ChatResponseSchema.safeParse(data);

    if (!responseValidation.success) {
      console.error({ requestId, msg: "Backend response shape mismatch" });
      return errorResponse(
        ErrorCodes.UPSTREAM_ERROR,
        "Invalid backend response",
        502,
        undefined,
        requestId
      );
    }

    // STEP 5: Return success
    return successResponse(responseValidation.data, requestId);

  } catch (error) {
    // Handle timeout specifically
    if (error instanceof Error && error.name === "AbortError") {
      console.error({ requestId, msg: "Backend timeout" });
      return errorResponse(ErrorCodes.TIMEOUT_ERROR, "Request timed out", 504, undefined, requestId);
    }

    // Log unexpected errors with stack trace
    console.error({
      requestId,
      error: error instanceof Error ? error.message : String(error),
      stack: error instanceof Error ? error.stack : undefined,
    });

    return errorResponse(ErrorCodes.INTERNAL_ERROR, "Internal server error", 500, undefined, requestId);
  }
}