import React, { useMemo } from 'react'
import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls,
  MarkerType,
  NodeTypes,
} from 'reactflow'
import 'reactflow/dist/style.css'
import type { EpicWithTasks, Task, Operation } from '@taskboard/core'

interface AllData {
  epics: EpicWithTasks[]
  operations: Operation[]
  workflowOrder: Task[]
  [key: string]: any
}

interface Props {
  data: AllData
  selectedTaskId: string | null
  onSelectTask: (id: string | null) => void
}

const OP_COLOR: Record<string, string> = {
  start: '#06b6d4',
  progress: '#6b7280',
  complete: '#22c55e',
  error: '#ef4444',
  interrupt: '#f59e0b',
}

function OperationNode({ data }: { data: any }) {
  return (
    <div
      className="bg-gray-800 border rounded-lg px-4 py-2 min-w-48"
      style={{ borderColor: data.color }}
    >
      <div className="flex items-center gap-2 mb-1">
        <span
          className="w-2 h-2 rounded-full flex-shrink-0"
          style={{ backgroundColor: data.color }}
        />
        <span className="text-xs font-medium text-white uppercase tracking-wide">
          {data.operationType}
        </span>
        <span className="text-xs text-gray-500 ml-auto">{data.time}</span>
      </div>
      {data.agent && (
        <div className="text-xs text-blue-400">{data.agent}</div>
      )}
      {data.summary && (
        <div className="text-xs text-gray-300 mt-1">{data.summary}</div>
      )}
    </div>
  )
}

const nodeTypes: NodeTypes = { operation: OperationNode }

export function TaskOperations({ data, selectedTaskId, onSelectTask }: Props) {
  const allTasks = data.epics.flatMap(e => e.tasks.map(t => t.task))

  const selectedTask = selectedTaskId
    ? allTasks.find(t => t.id === selectedTaskId)
    : allTasks[0] ?? null

  const taskOps = selectedTask
    ? data.operations.filter(o => o.task_id === selectedTask.id)
    : []

  // Find parent epic for breadcrumb
  const parentEpic = selectedTask
    ? data.epics.find(e => e.tasks.some(t => t.task.id === selectedTask?.id))
    : null

  // Build ReactFlow nodes and edges
  const { nodes, edges } = useMemo(() => {
    const nodes: Node[] = taskOps.map((op, i) => ({
      id: String(op.id),
      type: 'operation',
      position: { x: 100, y: i * 100 },
      data: {
        operationType: op.operation_type,
        color: OP_COLOR[op.operation_type] ?? '#6b7280',
        time: op.created_at?.slice(11, 16) ?? '',
        agent: op.agent_platform,
        summary: op.summary,
      },
    }))

    const edges: Edge[] = taskOps.slice(0, -1).map((op, i) => ({
      id: `e${op.id}-${taskOps[i + 1].id}`,
      source: String(op.id),
      target: String(taskOps[i + 1].id),
      markerEnd: { type: MarkerType.ArrowClosed },
      style: { stroke: '#374151' },
    }))

    return { nodes, edges }
  }, [taskOps])

  return (
    <div className="h-full flex flex-col">
      {/* Breadcrumb header */}
      {selectedTask && (
        <div className="px-4 py-2 border-b border-gray-800 bg-gray-900 flex items-center gap-2 text-sm">
          {parentEpic && (
            <>
              <span className="text-gray-500">{parentEpic.epic.id}</span>
              <span className="text-gray-600">›</span>
            </>
          )}
          <span className="text-white font-medium">
            [{selectedTask.id}] {selectedTask.title}
          </span>
          <span className={`ml-2 text-xs px-2 py-0.5 rounded-full ${
            selectedTask.status === 'done' ? 'bg-green-900 text-green-300' :
            selectedTask.status === 'in_progress' ? 'bg-yellow-900 text-yellow-300' :
            'bg-gray-800 text-gray-400'
          }`}>
            {selectedTask.status}
          </span>
        </div>
      )}

      <div className="flex flex-1 overflow-hidden">
        {/* Task selector sidebar */}
        <div className="w-56 border-r border-gray-800 overflow-y-auto bg-gray-900 flex-shrink-0">
          <div className="p-3">
            <h3 className="text-xs text-gray-500 uppercase tracking-wider mb-2">Tasks</h3>
            {allTasks.map(t => (
              <button
                key={t.id}
                onClick={() => onSelectTask(t.id)}
                className={`w-full text-left px-3 py-2 rounded-lg mb-1 text-sm transition-colors ${
                  t.id === selectedTask?.id
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                }`}
              >
                <div className="font-mono text-xs opacity-70">{t.id}</div>
                <div className="truncate">{t.title}</div>
              </button>
            ))}
          </div>
        </div>

        {/* ReactFlow canvas */}
        <div className="flex-1 bg-gray-950">
          {taskOps.length === 0 ? (
            <div className="h-full flex items-center justify-center text-gray-600">
              <p>No operations recorded for this task.</p>
            </div>
          ) : (
            <ReactFlow
              nodes={nodes}
              edges={edges}
              nodeTypes={nodeTypes}
              fitView
              attributionPosition="bottom-left"
            >
              <Background color="#1f2937" />
              <Controls />
            </ReactFlow>
          )}
        </div>
      </div>
    </div>
  )
}
