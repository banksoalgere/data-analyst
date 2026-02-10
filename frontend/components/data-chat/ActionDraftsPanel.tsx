'use client'

import { ActionDraft } from "@/types/chat"

interface ActionDraftsPanelProps {
  drafts: ActionDraft[]
  approvingByAction: Record<string, boolean>
  onApprove: (actionId: string) => void
}

export function ActionDraftsPanel({
  drafts,
  approvingByAction,
  onApprove,
}: ActionDraftsPanelProps) {
  if (!drafts.length) return null

  return (
    <div className="mt-3 space-y-2">
      {drafts.map((action) => {
        const actionId = action.action_id
        const status = action.status ?? "pending_approval"
        const execution = action.execution

        return (
          <div key={actionId} className="rounded border border-neutral-800 bg-neutral-950 p-3">
            <div className="flex items-center justify-between gap-2">
              <div>
                <div className="text-sm text-white">{action.title || "Untitled action"}</div>
                <div className="text-xs text-neutral-400">
                  {action.type || "unknown"} • {status}
                </div>
              </div>
              <button
                type="button"
                className="text-xs border border-neutral-700 px-2 py-1 rounded text-neutral-300 hover:text-white hover:border-neutral-500 transition-colors disabled:opacity-50"
                onClick={() => onApprove(actionId)}
                disabled={status === "executed" || Boolean(approvingByAction[actionId])}
              >
                {status === "executed"
                  ? "Executed"
                  : approvingByAction[actionId]
                    ? "Executing..."
                    : "Approve & Execute"}
              </button>
            </div>
            <div className="text-xs text-neutral-300 mt-2">{action.description || ""}</div>
            {execution !== undefined && execution !== null && (
              <pre className="mt-2 bg-black/40 border border-neutral-700 text-neutral-300 text-xs p-2 overflow-auto rounded">
                {JSON.stringify(execution, null, 2)}
              </pre>
            )}
          </div>
        )
      })}
    </div>
  )
}
