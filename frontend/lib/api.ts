/**
 * =============================================================================
 * API RESPONSE HELPERS
 * =============================================================================
 * 
 * WHY STANDARDIZED RESPONSES?
 * ---------------------------
 * When every API route returns a different shape, frontend code becomes messy:
 * 
 * BAD (inconsistent):
 *   Route A: { data: {...} }
 *   Route B: { result: {...} }
 *   Route C: { user: {...}, error?: string }
 * 
 * GOOD (standardized):
 *   All routes: { success: true, data: {...} } OR { success: false, error: {...} }
 * 
 * WHY THE `success` DISCRIMINATOR?
 * --------------------------------
 * TypeScript can narrow types based on a discriminator field.
 * 
 * const response = await fetch('/api/thing').then(r => r.json());
 * if (response.success) {
 *   // TypeScript KNOWS response.data exists here
 *   console.log(response.data.name);
 * } else {
 *   // TypeScript KNOWS response.error exists here
 *   console.log(response.error.message);
 * }
 * 
 * Without `success`, you'd need: `if ('data' in response)` which is fragile.
 * 
 * ALTERNATIVE APPROACHES:
 * 1. HTTP status only (no body on errors)
 *    - Simple, but no error details
 * 2. RFC 7807 Problem Details
 *    - Industry standard, but more complex
 * 3. GraphQL-style { data, errors } arrays
 *    - Good for multiple errors, overkill for REST
 * 
 * Google: "typescript discriminated unions", "api response patterns", "rfc 7807"
 */

import { NextResponse } from "next/server";

/**
 * Error codes for machine-readable error identification.
 * 
 * WHY STRING ENUMS?
 * - Human-readable in logs/network tab
 * - Self-documenting
 * - Easy to add new codes without breaking clients
 * 
 * ALTERNATIVE: Numeric codes (HTTP status style)
 * - More compact but less readable
 */
export const ErrorCodes = {
    VALIDATION_ERROR: "VALIDATION_ERROR",
    UPSTREAM_ERROR: "UPSTREAM_ERROR",
    TIMEOUT_ERROR: "TIMEOUT_ERROR",
    INTERNAL_ERROR: "INTERNAL_ERROR",
} as const;

export type ErrorCode = (typeof ErrorCodes)[keyof typeof ErrorCodes];

/**
 * Create a standardized error response.
 * 
 * @param code - Machine-readable error code (for frontend switch statements)
 * @param message - Human-readable message (for displaying to users or logging)
 * @param status - HTTP status code
 * @param details - Optional structured error details (validation errors, etc.)
 * @param requestId - Optional request ID for log correlation
 */
export function errorResponse(
    code: ErrorCode,
    message: string,
    status: number,
    details?: unknown,
    requestId?: string
) {
    /**
     * NOTE: We return { success: false, error: {...} }
     * This matches our APIErrorResponse type from types/chat.ts
     */
    return NextResponse.json(
        {
            success: false as const,  // `as const` makes TypeScript treat this as literal `false`
            error: {
                code,
                message,
                details,
                requestId,
            },
        },
        { status }
    );
}

/**
 * Create a standardized success response.
 * 
 * @param data - The actual response data
 * @param requestId - Optional request ID for log correlation
 */
export function successResponse<T>(data: T, requestId?: string) {
    /**
     * Generic <T> lets TypeScript know what type `data` is.
     * If you call successResponse({ name: "Josh" }), TypeScript knows
     * the response has { success: true, data: { name: string } }
     */
    const response: { success: true; data: T; requestId?: string } = {
        success: true as const,  // `as const` for literal type
        data,
    };

    // Only include requestId if provided (keeps responses clean)
    if (requestId) {
        response.requestId = requestId;
    }

    return NextResponse.json(response);
}

/**
 * USAGE EXAMPLE (in your route.ts):
 * 
 * import { errorResponse, successResponse, ErrorCodes } from "@/lib/api";
 * 
 * // On error:
 * return errorResponse(
 *   ErrorCodes.VALIDATION_ERROR,
 *   "Message is required",
 *   400,
 *   validationErrors
 * );
 * 
 * // On success:
 * return successResponse({ message: "Hello!" });
 */
