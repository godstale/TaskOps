// IPC channel name constants — shared between main and renderer
export const IPC = {
  // renderer → main (invoke)
  GET_PROJECT_LIST: 'get-project-list',
  GET_ALL_DATA: 'get-all-data',
  SELECT_FOLDER: 'select-folder',
  // main → renderer (send)
  DB_CHANGED: 'db-changed',
} as const
