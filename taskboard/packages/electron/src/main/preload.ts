import { contextBridge, ipcRenderer } from 'electron'
import { IPC } from './ipc'

contextBridge.exposeInMainWorld('taskboard', {
  selectFolder: () => ipcRenderer.invoke(IPC.SELECT_FOLDER),
  getProjectList: (root: string) => ipcRenderer.invoke(IPC.GET_PROJECT_LIST, root),
  getAllData: (dbPath: string) => ipcRenderer.invoke(IPC.GET_ALL_DATA, dbPath),
  onDbChanged: (cb: (dbPath: string) => void) =>
    ipcRenderer.on(IPC.DB_CHANGED, (_, dbPath) => cb(dbPath)),
  offDbChanged: () => ipcRenderer.removeAllListeners(IPC.DB_CHANGED),
})
