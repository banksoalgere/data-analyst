/**
 * =============================================================================
 * FETCH UTILITIES
 * =============================================================================
 * 
 * WHY WRAP FETCH?
 * ---------------
 * The native `fetch()` API is great but lacks some production essentials:
 * - No built-in timeout (requests hang forever if server is unresponsive)
 * - No retry logic for transient failures
 * - No request tracing (correlating frontend requests with backend logs)
 * 
 * WHAT THIS FILE PROVIDES:
 * - `fetchWithTimeout`: Adds timeout support using AbortController
 * 
 * WHY NOT USE axios/ky/etc?
 * -------------------------
 * - fetch() is native, zero bundle size impact
 * - Works in Edge Runtime (next.js API routes can run at edge)
 * - AbortController is the standard way to cancel requests
 * - For simple needs, a small wrapper is enough
 * 
 * WHEN TO USE A LIBRARY:
 * - You need request/response interceptors
 * - You need automatic retries with backoff
 * - You need progress events for uploads
 * 
 * Google: "abortcontroller fetch timeout", "fetch vs axios", "edge runtime fetch"
 */

/**
 * Fetch with a timeout.
 * 
 * HOW IT WORKS:
 * 1. Create an AbortController (a "cancel button" for the request)
 * 2. Set a timer that pushes the cancel button after X milliseconds
 * 3. Pass the controller's signal to fetch (links them together)
 * 4. If timeout fires, fetch throws an AbortError
 * 5. If fetch completes first, we clear the timer (cleanup)
 * 
 * WHY try/finally?
 * We MUST clear the timeout even if fetch throws.
 * Without cleanup, timer continues running (memory leak in long-running processes).
 * 
 * @param url - The URL to fetch
 * @param options - Standard fetch options (method, body, headers, etc.)
 * @param timeoutMs - How long to wait before aborting (default: 30 seconds)
 * @returns The fetch Response object
 * @throws AbortError if timeout exceeded, or network errors
 */
export async function fetchWithTimeout(
    url: string,
    options: RequestInit = {},
    timeoutMs: number = 30000
): Promise<Response> {
    /**
     * AbortController is like an "emergency stop" button.
     * - controller.abort() = press the button
     * - controller.signal = a reference that fetch monitors
     * 
     * When abort() is called, any fetch using this signal throws AbortError.
     */
    const controller = new AbortController();

    /**
     * Set up a timer to auto-abort after our timeout.
     * setTimeout returns an ID we can use to cancel it later.
     */
    const timeoutId = setTimeout(() => {
        controller.abort();
    }, timeoutMs);

    try {
        /**
         * Pass the signal to fetch. This links them:
         * - If controller.abort() is called, this fetch will throw
         * - The signal property in options gets merged with any existing options
         */
        const response = await fetch(url, {
            ...options,           // Spread existing options first
            signal: controller.signal,  // Add our abort signal
        });

        return response;
    } finally {
        /**
         * CRITICAL: Always clear the timeout!
         * 
         * Why? If fetch completes in 100ms but timeout is 30s,
         * that timer is still scheduled. In serverless, this might
         * not matter, but in long-running servers it's a memory leak.
         * 
         * `finally` runs whether try succeeds OR throws.
         */
        clearTimeout(timeoutId);
    }
}

/**
 * FUTURE ENHANCEMENTS (not implemented, but good to know):
 * 
 * 1. Retry with exponential backoff:
 *    async function fetchWithRetry(url, options, maxRetries = 3) {
 *      for (let i = 0; i < maxRetries; i++) {
 *        try {
 *          return await fetch(url, options);
 *        } catch (e) {
 *          if (i === maxRetries - 1) throw e;
 *          await sleep(Math.pow(2, i) * 1000); // 1s, 2s, 4s...
 *        }
 *      }
 *    }
 * 
 * 2. Request ID injection (for tracing):
 *    function addRequestId(options) {
 *      const requestId = crypto.randomUUID();
 *      options.headers = { ...options.headers, 'X-Request-ID': requestId };
 *      return requestId;
 *    }
 * 
 * Google: "exponential backoff javascript", "distributed tracing request id"
 */
