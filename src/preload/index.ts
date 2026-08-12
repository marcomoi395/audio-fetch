import { contextBridge, ipcRenderer } from 'electron'
import { createPreloadApi } from './api'
import { installPreloadApi } from './install'

const audioFetch = createPreloadApi(ipcRenderer)

if (!process.contextIsolated) throw new Error('Audio Fetch requires context isolation')

installPreloadApi((key, api) => contextBridge.exposeInMainWorld(key, api), audioFetch)
