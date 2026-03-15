import React from 'react'
import type { Screen } from '../useTaskBoard'

const SCREENS: { id: Screen; label: string; icon: string }[] = [
  { id: 'dashboard', label: 'Dashboard', icon: '📊' },
  { id: 'taskops', label: 'Task Operations', icon: '🔄' },
  { id: 'resources', label: 'Resources', icon: '📁' },
  { id: 'settings', label: 'Settings', icon: '⚙️' },
]

interface Props {
  current: Screen
  onSelect: (s: Screen) => void
  projectName?: string
}

export function Sidebar({ current, onSelect, projectName }: Props) {
  return (
    <div className="w-52 bg-gray-900 border-r border-gray-800 flex flex-col h-full">
      <div className="p-4 border-b border-gray-800">
        <div className="text-xs text-gray-500 uppercase tracking-wider">TaskBoard</div>
        {projectName && (
          <div className="text-sm font-semibold text-white mt-1 truncate">{projectName}</div>
        )}
      </div>
      <nav className="flex-1 p-2">
        {SCREENS.map(s => (
          <button
            key={s.id}
            onClick={() => onSelect(s.id)}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm mb-1 transition-colors
              ${current === s.id
                ? 'bg-blue-600 text-white font-medium'
                : 'text-gray-400 hover:bg-gray-800 hover:text-white'
              }`}
          >
            <span>{s.icon}</span>
            <span>{s.label}</span>
          </button>
        ))}
      </nav>
    </div>
  )
}
