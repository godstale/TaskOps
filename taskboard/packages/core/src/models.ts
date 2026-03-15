// taskboard/packages/core/src/models.ts

export type TaskStatus = 'todo' | 'in_progress' | 'interrupted' | 'done' | 'cancelled'
export type TaskType = 'project' | 'epic' | 'task' | 'objective'
export type OperationType = 'start' | 'progress' | 'complete' | 'error' | 'interrupt'
export type ResourceType = 'input' | 'output' | 'reference' | 'intermediate'

export interface Task {
  id: string
  project_id: string
  type: TaskType
  title: string
  description?: string
  status: TaskStatus
  parent_id?: string
  todo?: string
  interrupt?: string
  milestone_target?: string
  due_date?: string
  seq_order?: number
  parallel_group?: string
  depends_on?: string[]   // DB에서 JSON 파싱 후
  created_at: string
  updated_at: string
}

export interface Operation {
  id: number
  task_id: string
  operation_type: OperationType
  agent_platform?: string
  summary?: string
  details?: string
  subagent_used?: number
  subagent_result?: string
  started_at?: string
  completed_at?: string
  created_at: string
}

export interface Resource {
  id: number
  task_id: string
  file_path: string
  description?: string
  res_type: ResourceType
  created_at: string
}

export interface Setting {
  key: string
  value: string
  description?: string
  updated_at: string
}

export interface ProjectInfo {
  id: string
  title: string
  status: TaskStatus
  created_at: string
}

export interface EpicWithTasks {
  epic: Task
  tasks: TaskWithChildren[]
}

export interface TaskWithChildren {
  task: Task
  children: Task[]   // SubTask 목록
}

export interface ProjectSummary {
  project: ProjectInfo
  totalEpics: number
  totalTasks: number
  tasksByStatus: Record<TaskStatus, number>
}
