const { app, BrowserWindow, ipcMain, Menu } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

const DEV_PROJECT_ROOT = path.resolve(__dirname, '..', '..');
const RUNTIME_ROOT = app.isPackaged
  ? path.join(process.resourcesPath, 'backend')
  : DEV_PROJECT_ROOT;
const BRIDGE_PATH = path.join(RUNTIME_ROOT, 'src', 'gui_bridge.py');
const WINDOW_ICON_CANDIDATES = app.isPackaged
  ? [
      path.join(process.resourcesPath, 'icon.ico'),
      path.join(process.resourcesPath, 'app', 'icon.ico'),
    ]
  : [path.join(DEV_PROJECT_ROOT, 'icon.ico')];
const WINDOW_ICON = WINDOW_ICON_CANDIDATES.find((iconPath) => fs.existsSync(iconPath));

function resolvePythonCommand() {
  const configuredPython = process.env.CONLANG_STUDIO_PYTHON;
  if (configuredPython && fs.existsSync(configuredPython)) {
    return { command: configuredPython, prefixArgs: [] };
  }

  const packagedPython = path.join(process.resourcesPath, 'python', 'python.exe');
  if (app.isPackaged && fs.existsSync(packagedPython)) {
    return { command: packagedPython, prefixArgs: [] };
  }

  const venvPython = path.join(DEV_PROJECT_ROOT, '.venv', 'Scripts', 'python.exe');
  if (fs.existsSync(venvPython)) {
    return { command: venvPython, prefixArgs: [] };
  }

  if (process.platform === 'win32') {
    return { command: 'py', prefixArgs: ['-3'] };
  }

  return { command: 'python3', prefixArgs: [] };
}

function parseBridgeOutput(stdoutText, stderrText) {
  const trimmed = String(stdoutText || '').trim();
  if (!trimmed) {
    return {
      ok: false,
      error: 'Python bridge returned empty output.',
      stdout: stdoutText,
      stderr: stderrText,
    };
  }

  try {
    return JSON.parse(trimmed);
  } catch (_error) {
    const lines = trimmed.split(/\r?\n/).filter(Boolean);
    for (let idx = lines.length - 1; idx >= 0; idx -= 1) {
      try {
        return JSON.parse(lines[idx]);
      } catch (_lineError) {
      }
    }

    return {
      ok: false,
      error: 'Unable to parse bridge response as JSON.',
      stdout: stdoutText,
      stderr: stderrText,
    };
  }
}

function runPythonAction(action, payload = {}) {
  return new Promise((resolve) => {
    if (!fs.existsSync(BRIDGE_PATH)) {
      resolve({
        ok: false,
        error: `Python bridge not found at ${BRIDGE_PATH}.`,
      });
      return;
    }

    const py = resolvePythonCommand();
    const args = [...py.prefixArgs, BRIDGE_PATH, '--action', action];

    const child = spawn(py.command, args, {
      cwd: RUNTIME_ROOT,
      windowsHide: true,
    });

    let stdout = '';
    let stderr = '';

    child.stdout.on('data', (chunk) => {
      stdout += chunk.toString();
    });

    child.stderr.on('data', (chunk) => {
      stderr += chunk.toString();
    });

    child.on('error', (error) => {
      resolve({
        ok: false,
        error: `Failed to launch python bridge: ${error.message}`,
        stdout,
        stderr,
      });
    });

    child.on('close', () => {
      const parsed = parseBridgeOutput(stdout, stderr);
      if (stderr && !parsed.stderr) {
        parsed.stderr = stderr;
      }
      resolve(parsed);
    });

    try {
      child.stdin.write(JSON.stringify(payload));
      child.stdin.end();
    } catch (error) {
      resolve({
        ok: false,
        error: `Failed to send payload to bridge: ${error.message}`,
        stdout,
        stderr,
      });
    }
  });
}

function createMainWindow() {
  const mainWindow = new BrowserWindow({
    width: 1480,
    height: 940,
    minWidth: 1120,
    minHeight: 720,
    frame: false,
    titleBarStyle: 'hidden',
    backgroundColor: '#0f1115',
    ...(process.platform === 'win32' && WINDOW_ICON ? { icon: WINDOW_ICON } : {}),
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  const devServerUrl = process.env.VITE_DEV_SERVER_URL;
  if (devServerUrl) {
    mainWindow.loadURL(devServerUrl);
  } else {
    mainWindow.loadFile(path.join(__dirname, '..', 'dist', 'index.html'));
  }

  return mainWindow;
}

app.whenReady().then(() => {
  Menu.setApplicationMenu(null);

  ipcMain.handle('bridge:run', async (_event, request) => {
    const action = request && request.action ? request.action : '';
    const payload = request && request.payload ? request.payload : {};
    if (!action) {
      return { ok: false, error: 'Action is required.' };
    }
    return runPythonAction(action, payload);
  });

  ipcMain.handle('window:minimize', (event) => {
    const win = BrowserWindow.fromWebContents(event.sender);
    if (win) {
      win.minimize();
    }
    return true;
  });

  ipcMain.handle('window:maximize-toggle', (event) => {
    const win = BrowserWindow.fromWebContents(event.sender);
    if (!win) {
      return false;
    }
    if (win.isMaximized()) {
      win.unmaximize();
      return false;
    }
    win.maximize();
    return true;
  });

  ipcMain.handle('window:close', (event) => {
    const win = BrowserWindow.fromWebContents(event.sender);
    if (win) {
      win.close();
    }
    return true;
  });

  ipcMain.handle('window:is-maximized', (event) => {
    const win = BrowserWindow.fromWebContents(event.sender);
    return win ? win.isMaximized() : false;
  });

  createMainWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
