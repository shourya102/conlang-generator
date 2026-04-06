const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('desktopApi', {
  runBridge(action, payload = {}) {
    return ipcRenderer.invoke('bridge:run', { action, payload });
  },
  windowControls: {
    minimize() {
      return ipcRenderer.invoke('window:minimize');
    },
    toggleMaximize() {
      return ipcRenderer.invoke('window:maximize-toggle');
    },
    close() {
      return ipcRenderer.invoke('window:close');
    },
    isMaximized() {
      return ipcRenderer.invoke('window:is-maximized');
    },
  },
});
