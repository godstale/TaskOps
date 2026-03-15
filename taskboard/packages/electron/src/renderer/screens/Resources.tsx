import React from 'react'
import type { Resource } from '@taskboard/core'

const TYPE_STYLES: Record<string, { bg: string; text: string; label: string }> = {
  input: { bg: 'bg-blue-900/50', text: 'text-blue-300', label: 'Input' },
  output: { bg: 'bg-green-900/50', text: 'text-green-300', label: 'Output' },
  reference: { bg: 'bg-gray-800', text: 'text-gray-400', label: 'Reference' },
  intermediate: { bg: 'bg-yellow-900/50', text: 'text-yellow-300', label: 'Intermediate' },
}

interface Props {
  resources: Resource[]
}

export function Resources({ resources }: Props) {
  return (
    <div className="p-6">
      <h2 className="text-xl font-bold text-white mb-4">
        Resources <span className="text-gray-500 text-sm font-normal">({resources.length})</span>
      </h2>

      {resources.length === 0 ? (
        <div className="text-gray-500 text-center py-12">No resources recorded</div>
      ) : (
        <div className="space-y-2">
          {resources.map(r => {
            const style = TYPE_STYLES[r.res_type] ?? TYPE_STYLES.reference
            return (
              <div
                key={r.id}
                className={`${style.bg} border border-gray-800 rounded-lg p-4 flex items-start gap-4`}
              >
                <span className={`${style.text} text-xs font-medium w-24 flex-shrink-0 uppercase tracking-wide mt-0.5`}>
                  {style.label}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-mono text-gray-200 truncate">{r.file_path}</div>
                  {r.description && (
                    <div className="text-xs text-gray-500 mt-1">{r.description}</div>
                  )}
                  <div className="text-xs text-gray-600 mt-1 font-mono">{r.task_id}</div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
