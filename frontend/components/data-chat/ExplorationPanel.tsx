'use client'

import { ExplorationSummary } from "@/types/chat"

interface ExplorationPanelProps {
  exploration: ExplorationSummary
  selectedProbeId?: string | null
  onProbeSelect?: (probeId: string) => void
}

export function ExplorationPanel({
  exploration,
  selectedProbeId,
  onProbeSelect,
}: ExplorationPanelProps) {
  const probes = Array.isArray(exploration.probes) ? exploration.probes : []
  if (!probes.length) return null

  const activeProbeId = selectedProbeId ?? exploration.primary_probe_id ?? probes[0]?.probe_id

  return (
    <div className="mb-3 rounded border border-cyan-900/60 bg-cyan-950/20 p-3 space-y-3">
      <div className="text-xs text-cyan-100 font-medium">
        Multi-step exploration: {exploration.analysis_goal}
      </div>
      <p className="text-[11px] text-cyan-200/80">
        Click any probe to explore its chart and evidence.
      </p>
      <div className="space-y-1.5">
        {probes.map((probe) => {
          const isPrimary = probe.probe_id === exploration.primary_probe_id
          const isActive = probe.probe_id === activeProbeId
          return (
            <button
              key={probe.probe_id}
              type="button"
              onClick={() => onProbeSelect?.(probe.probe_id)}
              className={`w-full rounded border p-2 text-left text-xs transition-colors ${
                isActive
                  ? "border-cyan-500 bg-cyan-900/30 text-cyan-100"
                  : isPrimary
                    ? "border-cyan-800 bg-cyan-950/30 text-cyan-100"
                    : "border-neutral-800 bg-neutral-950 text-neutral-300 hover:border-cyan-700/70 hover:text-white"
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <span className="font-medium leading-5">{probe.question}</span>
                <span className="uppercase tracking-wide shrink-0">{probe.analysis_type}</span>
              </div>
              <div className="mt-1 text-neutral-400">
                rows: {probe.row_count}
                {typeof probe.visualized_row_count === "number" && ` | visualized: ${probe.visualized_row_count}`}
                {isPrimary && " | primary"}
              </div>
              {probe.rationale && <div className="mt-1 text-neutral-400 leading-5">{probe.rationale}</div>}
            </button>
          )
        })}
      </div>
    </div>
  )
}
