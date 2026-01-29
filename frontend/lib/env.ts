/**
 * =============================================================================
 * ENVIRONMENT VARIABLE VALIDATION
 * =============================================================================
 * 
 * WHY VALIDATE ENVIRONMENT VARIABLES?
 * ------------------------------------
 * Environment variables are strings that come from outside your code (shell, .env files).
 * They can be undefined, empty, or malformed. Without validation:
 * - Your app might crash deep in some function with a confusing error
 * - You might silently use wrong values (empty string instead of URL)
 * - Debugging "undefined" errors in production is painful
 * 
 * FAIL-FAST PRINCIPLE:
 * If something is wrong, crash at startup, not 2 hours later when a user hits that code.
 * 
 * WHY ZOD FOR THIS?
 * We're already using Zod for request validation. Using it here too:
 * - Consistent pattern across the codebase
 * - Type-safe access to env vars (no more `process.env.X as string`)
 * - Built-in transforms and defaults
 * 
 * ALTERNATIVE APPROACHES:
 * 1. Manual checks: `if (!process.env.X) throw new Error(...)`
 *    - Verbose, no types, easy to forget
 * 2. Libraries like envalid, env-var
 *    - Good, but adds another dependency when we have Zod
 * 3. t3-env (from create-t3-app)
 *    - Feature-rich but overkill for small projects
 * 
 * Google: "zod environment variables", "fail fast principle", "12 factor app config"
 */

import { z } from "zod";

/**
 * Define the shape of your environment.
 * 
 * KEY CONSIDERATIONS:
 * - Use .url() for URLs to validate format (catches typos like "htpp://")
 * - Use .default() for development fallbacks (so `npm run dev` works without .env)
 * - Use .optional() sparingly - prefer explicit defaults
 * - Document what each variable is for
 */
const envSchema = z.object({
    /**
     * BACKEND_URL: Where your Python backend lives
     * 
     * In development: defaults to localhost:8000
     * In production: MUST be set explicitly (no default = fails if missing)
     * 
     * Note: .default() only applies if the var is undefined/missing,
     * NOT if it's an empty string. Empty string would still fail .url() check.
     */
    BACKEND_URL: z
        .string()
        .url("BACKEND_URL must be a valid URL (e.g., http://localhost:8000)")
        .default("http://localhost:8000"),

    /**
     * NODE_ENV: Standard Node.js environment indicator
     * 
     * We use .enum() to restrict to known values.
     * Unknown values (like "staging") would fail - add them to the enum if needed.
     */
    NODE_ENV: z
        .enum(["development", "production", "test"])
        .default("development"),
});

/**
 * Parse and validate environment variables.
 * 
 * WHEN DOES THIS RUN?
 * When this module is first imported (at application startup).
 * If validation fails, the app crashes immediately with a clear error.
 * 
 * WHAT IF IT FAILS?
 * Zod throws a ZodError with details on which fields failed and why.
 * Example: "BACKEND_URL: Expected string, received undefined"
 */
export const env = envSchema.parse(process.env);

/**
 * TYPE EXPORT:
 * This lets other files know what environment variables are available.
 * Useful for type hints and documentation.
 */
export type Env = z.infer<typeof envSchema>;
