import { FullMessage } from "@/types/chat";

export type AnalyzeProgressPhase =
  | "plan_ready"
  | "probe_started"
  | "probe_completed"
  | "synthesis_started"
  | "synthesis_completed";

export interface AnalyzeProgressEvent {
  type: "progress";
  phase?: AnalyzeProgressPhase | string;
  probe_id?: unknown;
  question?: unknown;
  row_count?: unknown;
  probe_count?: unknown;
  analysis_goal?: unknown;
  primary_probe_id?: unknown;
}

export interface AnalyzeErrorEvent {
  type: "error";
  detail?: unknown;
}

export interface AnalyzeResultEvent {
  type: "result";
  conversation_id?: unknown;
  payload?: unknown;
}

export type AnalyzeStreamEvent =
  | AnalyzeProgressEvent
  | AnalyzeErrorEvent
  | AnalyzeResultEvent;

export function splitSseFrames(buffer: string): {
  frames: string[];
  remainder: string;
} {
  const chunks = buffer.split("\n\n");
  const remainder = chunks.pop() ?? "";
  return { frames: chunks, remainder };
}

export function parseSseDataLine(frame: string): string | null {
  const line = frame
    .split("\n")
    .find((entry) => entry.startsWith("data: "));
  if (!line) return null;
  const payload = line.slice(6).trim();
  return payload || null;
}

export function parseAnalyzeStreamEvent(payload: string): AnalyzeStreamEvent | null {
  try {
    const parsed = JSON.parse(payload) as Record<string, unknown>;
    const type = typeof parsed.type === "string" ? parsed.type : "";
    if (type === "progress") {
      return parsed as unknown as AnalyzeProgressEvent;
    }
    if (type === "error") {
      return parsed as unknown as AnalyzeErrorEvent;
    }
    if (type === "result") {
      return parsed as unknown as AnalyzeResultEvent;
    }
    return null;
  } catch {
    return null;
  }
}

export function formatProgressMessage(event: AnalyzeProgressEvent): string {
  const phase = typeof event.phase === "string" ? event.phase : "";
  if (phase === "plan_ready") {
    const probeCount = typeof event.probe_count === "number" ? event.probe_count : "?";
    const goal = typeof event.analysis_goal === "string" ? event.analysis_goal : "analysis";
    return `Planned ${probeCount} probes for ${goal}`;
  }
  if (phase === "probe_started") {
    const probeId = typeof event.probe_id === "string" ? event.probe_id : "probe";
    const question = typeof event.question === "string" ? event.question : "running probe";
    return `Running ${probeId}: ${question}`;
  }
  if (phase === "probe_completed") {
    const probeId = typeof event.probe_id === "string" ? event.probe_id : "probe";
    const rowCount = typeof event.row_count === "number" ? event.row_count : "?";
    return `Completed ${probeId} (${rowCount} rows)`;
  }
  if (phase === "synthesis_completed") {
    const primaryProbe =
      typeof event.primary_probe_id === "string" ? event.primary_probe_id : "primary probe";
    return `Synthesized final answer using ${primaryProbe}`;
  }
  if (phase === "synthesis_started") {
    return "Synthesizing final answer with probe evidence...";
  }
  return "Analyzing data...";
}

export function buildAssistantMessageFromAnalyzePayload(payload: Record<string, unknown>): FullMessage {
  return {
    id: crypto.randomUUID(),
    role: "assistant",
    message: String(payload.insight ?? ""),
    chartData: Array.isArray(payload.data) ? (payload.data as Record<string, unknown>[]) : [],
    chartConfig: (payload.chart_config ?? undefined) as FullMessage["chartConfig"],
    chartOptions: Array.isArray(payload.chart_options)
      ? (payload.chart_options as FullMessage["chartOptions"])
      : [],
    trust: (payload.trust ?? undefined) as FullMessage["trust"],
    sql: typeof payload.sql === "string" ? payload.sql : undefined,
    analysisType: typeof payload.analysis_type === "string" ? payload.analysis_type : undefined,
    followUpQuestions: Array.isArray(payload.follow_up_questions)
      ? payload.follow_up_questions
          .filter((item): item is string => typeof item === "string")
          .slice(0, 3)
      : [],
    exploration: (payload.exploration ?? undefined) as FullMessage["exploration"],
  };
}
