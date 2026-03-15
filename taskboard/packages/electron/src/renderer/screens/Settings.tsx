import React from 'react'
import type { Setting } from '@taskboard/core'

interface Props {
  settings: Setting[]
}

export function Settings({ settings }: Props) {
  return (
    <div className="p-6">
      <h2 className="text-xl font-bold text-white mb-4">Settings</h2>

      {settings.length === 0 ? (
        <div className="text-gray-500 text-center py-12">No settings found</div>
      ) : (
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-800">
                <th className="text-left text-xs text-gray-500 uppercase tracking-wider px-4 py-3">Key</th>
                <th className="text-left text-xs text-gray-500 uppercase tracking-wider px-4 py-3">Value</th>
                <th className="text-left text-xs text-gray-500 uppercase tracking-wider px-4 py-3">Description</th>
              </tr>
            </thead>
            <tbody>
              {settings.map((s, i) => (
                <tr
                  key={s.key}
                  className={`${i < settings.length - 1 ? 'border-b border-gray-800' : ''} hover:bg-gray-800/50 transition-colors`}
                >
                  <td className="px-4 py-3 font-mono text-sm text-cyan-400">{s.key}</td>
                  <td className="px-4 py-3 font-mono text-sm text-yellow-300">{s.value}</td>
                  <td className="px-4 py-3 text-sm text-gray-500">{s.description ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
