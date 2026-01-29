/**
 * =============================================================================
 * CHAT TYPES & VALIDATION SCHEMAS
 * =============================================================================
 * 
 * This file defines both TypeScript types AND Zod validation schemas for chat.
 * 
 * KEY DESIGN DECISION: Co-locating schemas with types
 * ----------------------------------------------------
 * We use `z.infer<typeof Schema>` to derive TypeScript types from Zod schemas.
 * This ensures our runtime validation (Zod) and compile-time types (TypeScript)
 * can NEVER drift apart. If you change the schema, the type updates automatically.
 * 
 * Alternative approaches considered:
 * 1. Separate files (types.ts + schemas.ts) - More files, risk of drift
 * 2. Inline schemas in route.ts - Can't reuse validation elsewhere
 * 3. Type-first with manual schema - Duplicate definitions, drift risk
 * 
 * Google: "zod infer typescript", "runtime type validation javascript"
 */

import { z } from "zod";

// =============================================================================
// ZOD SCHEMAS (Source of Truth)
// =============================================================================

/**
 * Schema for validating incoming chat messages from the frontend.
 * 
 * Design decisions:
 * - `min(1)` prevents empty strings (not just checking truthy)
 * - `max(10000)` prevents payload bombing / abuse
 * - `trim()` normalizes whitespace to prevent " " being valid
 * 
 * Google: "zod string validation", "api input validation best practices"
 */

export const MessageSchema = z.object({
    message: z
        .string()
        .trim()                              // Remove leading/trailing whitespace
        .min(1, "Message cannot be empty")   // Custom error message
        .max(10000, "Message too long"),     // Prevent abuse
});

/**
 * Schema for the backend's response structure.
 * 
 * Even though we trust our own backend more than user input,
 * validating responses catches:
 * - Backend bugs returning wrong shape
 * - Backend version mismatches during deploys
 * - Corrupted responses from network issues
 * 
 * Google: "validate api responses", "contract testing"
 */
export const ChatResponseSchema = z.object({
    message: z.string(),
    // Add more fields as your backend response grows
});

/**
 * Role union for message authorship.
 * Using z.enum creates both runtime validation AND TypeScript union.
 * 
 * Google: "zod enum vs union", "typescript literal types"
 */
export const RoleSchema = z.enum(["user", "assistant"]);

/**
 * Chart configuration schema for data visualization
 */
export const ChartConfigSchema = z.object({
    type: z.enum(["line", "bar", "scatter", "pie", "area"]),
    xKey: z.string(),
    yKey: z.string(),
    groupBy: z.string().optional(),
});

/**
 * Full message structure for chat history/display.
 * Uses uuid() for id to ensure valid format, not just any string.
 *
 * Google: "zod uuid validation", "chat message data structures"
 */
export const FullMessageSchema = z.object({
    id: z.string().uuid(),
    role: RoleSchema,
    message: z.string(),
    createdAt: z.string().datetime().optional(), // ISO 8601 format
    chartData: z.array(z.record(z.any())).optional(), // Optional chart data
    chartConfig: ChartConfigSchema.optional(), // Optional chart configuration
});

// =============================================================================
// TYPESCRIPT TYPES (Derived from Schemas)
// =============================================================================

/**
 * TypeScript types derived from Zod schemas using z.infer<>.
 * 
 * Why this pattern?
 * - Single source of truth (schema defines both runtime + compile-time)
 * - Changes to schema automatically update types
 * - IDE autocomplete works perfectly
 * - No manual type maintenance
 * 
 * Google: "zod typescript integration", "derive types from schema"
 */
export type MessageInput = z.infer<typeof MessageSchema>;
export type ChatResponse = z.infer<typeof ChatResponseSchema>;
export type Role = z.infer<typeof RoleSchema>;
export type FullMessage = z.infer<typeof FullMessageSchema>;

// =============================================================================
// API RESPONSE WRAPPER TYPES
// =============================================================================

/**
 * Standardized API response structure.
 * 
 * Design decision: Discriminated union with `success` field
 * --------------------------------------------------------
 * Frontend can do: `if (response.success) { use response.data }`
 * TypeScript narrows the type automatically (discriminated union).
 * 
 * Alternative: Just return data or error at top level
 * Drawback: Harder to distinguish success from error programmatically
 * 
 * Google: "typescript discriminated unions", "api response design patterns"
 */
export interface APISuccessResponse<T> {
    success: true;
    data: T;
}

export interface APIErrorResponse {
    success: false;
    error: {
        code: string;           // Machine-readable: "VALIDATION_ERROR"
        message: string;        // Human-readable: "Message cannot be empty"
        details?: unknown;      // Optional structured error info
        requestId?: string;     // For log correlation
    };
}

export type APIResponse<T> = APISuccessResponse<T> | APIErrorResponse;