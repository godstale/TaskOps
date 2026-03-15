import React, { useState } from 'react'

interface Props {
  onSelect: (dbPath: string) => void
}

export function ProjectSelect({ onSelect }: Props) {
  const [projects, setProjects] = useState<Array<{ name: string; dbPath: string }> | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSelectFolder = async () => {
    setLoading(true)
    const folder = await window.taskboard.selectFolder()
    if (!folder) { setLoading(false); return }
    const list = await window.taskboard.getProjectList(folder)
    setProjects(list)
    setLoading(false)
  }

  return (
    <div className="max-w-md w-full p-8">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">TaskBoard</h1>
        <p className="text-gray-400">Visualize your TaskOps projects</p>
      </div>

      {!projects ? (
        <button
          onClick={handleSelectFolder}
          disabled={loading}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 text-white font-medium py-3 px-6 rounded-lg transition-colors"
        >
          {loading ? 'Loading...' : 'Select TaskOps Folder'}
        </button>
      ) : projects.length === 0 ? (
        <div className="text-center">
          <p className="text-yellow-400 mb-4">No projects found in selected folder.</p>
          <button
            onClick={() => setProjects(null)}
            className="text-blue-400 hover:text-blue-300 underline"
          >
            Choose another folder
          </button>
        </div>
      ) : (
        <div>
          <h2 className="text-sm text-gray-400 uppercase tracking-wider mb-3">Select a project</h2>
          <div className="space-y-2">
            {projects.map(p => (
              <button
                key={p.dbPath}
                onClick={() => onSelect(p.dbPath)}
                className="w-full text-left bg-gray-800 hover:bg-gray-700 border border-gray-700 text-white py-3 px-4 rounded-lg transition-colors"
              >
                <div className="font-medium">{p.name}</div>
                <div className="text-xs text-gray-500 truncate">{p.dbPath}</div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
