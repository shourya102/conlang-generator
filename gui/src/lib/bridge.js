export async function runBridgeAction(action, payload = {}) {
  if (!window.desktopApi || typeof window.desktopApi.runBridge !== 'function') {
    throw new Error('Desktop bridge is unavailable. Run this UI inside Electron.');
  }
  return window.desktopApi.runBridge(action, payload);
}

export const windowControls = {
  minimize() {
    if (window.desktopApi?.windowControls?.minimize) {
      return window.desktopApi.windowControls.minimize();
    }
    return Promise.resolve(false);
  },
  toggleMaximize() {
    if (window.desktopApi?.windowControls?.toggleMaximize) {
      return window.desktopApi.windowControls.toggleMaximize();
    }
    return Promise.resolve(false);
  },
  close() {
    if (window.desktopApi?.windowControls?.close) {
      return window.desktopApi.windowControls.close();
    }
    return Promise.resolve(false);
  },
  isMaximized() {
    if (window.desktopApi?.windowControls?.isMaximized) {
      return window.desktopApi.windowControls.isMaximized();
    }
    return Promise.resolve(false);
  },
};
