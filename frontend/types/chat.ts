import { z } from "zod"

export const MessageSchema = z.object({
  message: z.string().trim().min(1, "Message cannot be empty").max(10000, "Message too long"),
})

export const ChatResponseSchema = z.object({
  message: z.string(),
})

export const RoleSchema = z.enum(["user", "assistant"])

export const ChartConfigSchema = z.object({
  type: z.enum(["line", "bar", "scatter", "pie", "area"]),
  xKey: z.string(),
  yKey: z.string(),
  groupBy: z.string().optional(),
})

export const TrustLayerSchema = z
  .object({
    confidence_score: z.number().optional(),
    limitations: z.array(z.string()).optional(),
    provenance: z.record(z.string(), z.unknown()).optional(),
  })
  .passthrough()

export const ActionDraftSchema = z
  .object({
    action_id: z.string(),
    type: z.string(),
    title: z.string(),
    description: z.string(),
    status: z.string(),
    payload: z.record(z.string(), z.unknown()).optional(),
    execution: z.record(z.string(), z.unknown()).optional(),
  })
  .passthrough()

export const FullMessageSchema = z.object({
  id: z.string().uuid(),
  role: RoleSchema,
  message: z.string(),
  createdAt: z.string().optional(),
  chartData: z.array(z.record(z.string(), z.unknown())).optional(),
  chartConfig: ChartConfigSchema.optional(),
  chartOptions: z.array(ChartConfigSchema).optional(),
  trust: TrustLayerSchema.optional(),
  sql: z.string().optional(),
  analysisType: z.string().optional(),
  followUpQuestions: z.array(z.string()).optional(),
  actionDrafts: z.array(ActionDraftSchema).optional(),
})

export type MessageInput = z.infer<typeof MessageSchema>
export type ChatResponse = z.infer<typeof ChatResponseSchema>
export type Role = z.infer<typeof RoleSchema>
export type ChartConfig = z.infer<typeof ChartConfigSchema>
export type TrustLayer = z.infer<typeof TrustLayerSchema>
export type ActionDraft = z.infer<typeof ActionDraftSchema>
export type FullMessage = z.infer<typeof FullMessageSchema>

export interface APISuccessResponse<T> {
  success: true
  data: T
}

export interface APIErrorResponse {
  success: false
  error: {
    code: string
    message: string
    details?: unknown
    requestId?: string
  }
}

export type APIResponse<T> = APISuccessResponse<T> | APIErrorResponse
