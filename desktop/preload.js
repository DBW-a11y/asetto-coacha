const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  backendPort: 8000,
  backendURL: 'http://127.0.0.1:8000',
});
