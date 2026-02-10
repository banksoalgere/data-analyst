'use client'

interface TrustPanelProps {
  trust: Record<string, unknown>
}

function getConfidenceTone(score: number) {
  if (score >= 0.8) return "text-emerald-300 border-emerald-800 bg-emerald-950/30"
  if (score >= 0.6) return "text-amber-300 border-amber-800 bg-amber-950/30"
  return "text-red-300 border-red-800 bg-red-950/30"
}

export function TrustPanel({ trust }: TrustPanelProps) {
  const confidence = Number(trust.confidence_score ?? 0)
  const provenance = (trust.provenance ?? {}) as Record<string, unknown>
  const limitations = Array.isArray(trust.limitations) ? trust.limitations : []

  return (
    <div className="mb-3 rounded border border-neutral-800 bg-neutral-950 p-3 space-y-2">
      <div className="flex flex-wrap items-center gap-2">
        <span className={`text-xs border px-2 py-1 rounded ${getConfidenceTone(confidence)}`}>
          confidence {confidence.toFixed(2)}
        </span>
        <span className="text-xs text-neutral-400">
          rows analyzed: {String(provenance.rows_analyzed ?? "n/a")}
        </span>
        <span className="text-xs text-neutral-400">
          rows visualized: {String(provenance.rows_visualized ?? "n/a")}
        </span>
      </div>
      {limitations.length > 0 && (
        <div className="text-xs text-neutral-400">
          limitations: {limitations.map(String).join(" | ")}
        </div>
      )}
    </div>
  )
}

