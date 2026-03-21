const { app, BrowserWindow } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const http = require('http');

let mainWindow = null;
let pythonProcess = null;

const BACKEND_PORT = 8000;
const BACKEND_URL = `http://127.0.0.1:${BACKEND_PORT}`;
const POLL_INTERVAL_MS = 500;
const POLL_TIMEOUT_MS = 30000;

const isDev = !app.isPackaged;

/**
 * Load .env file from project root and return as environment object.
 */
function loadDotEnv() {
  const envPath = isDev
    ? path.join(__dirname, '..', '.env')
    : path.join(process.resourcesPath, '.env');

  const env = { ...process.env };

  if (fs.existsSync(envPath)) {
    const lines = fs.readFileSync(envPath, 'utf-8').split('\n');
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#')) continue;
      const eqIdx = trimmed.indexOf('=');
      if (eqIdx === -1) continue;
      const key = trimmed.slice(0, eqIdx).trim();
      let value = trimmed.slice(eqIdx + 1).trim();
      // Strip surrounding quotes
      if ((value.startsWith('"') && value.endsWith('"')) ||
          (value.startsWith("'") && value.endsWith("'"))) {
        value = value.slice(1, -1);
      }
      env[key] = value;
    }
  }

  return env;
}

/**
 * Start the Python backend as a child process.
 */
function startBackend() {
  const env = loadDotEnv();

  if (isDev) {
    // Development: run python module directly
    const projectRoot = path.join(__dirname, '..');
    pythonProcess = spawn('python3', ['-m', 'racing_coach.main', 'serve'], {
      cwd: projectRoot,
      env,
      stdio: ['ignore', 'pipe', 'pipe'],
    });
  } else {
    // Production: run PyInstaller binary
    const serverPath = path.join(process.resourcesPath, 'python-backend', 'racing-coach-server');
    pythonProcess = spawn(serverPath, ['serve'], {
      env,
      stdio: ['ignore', 'pipe', 'pipe'],
    });
  }

  pythonProcess.stdout.on('data', (data) => {
    console.log(`[backend] ${data.toString().trim()}`);
  });

  pythonProcess.stderr.on('data', (data) => {
    console.error(`[backend] ${data.toString().trim()}`);
  });

  pythonProcess.on('close', (code) => {
    console.log(`[backend] process exited with code ${code}`);
    pythonProcess = null;
  });

  pythonProcess.on('error', (err) => {
    console.error(`[backend] failed to start: ${err.message}`);
    pythonProcess = null;
  });
}

/**
 * Poll the backend health endpoint until it responds.
 */
function waitForBackend() {
  return new Promise((resolve, reject) => {
    const startTime = Date.now();

    function poll() {
      if (Date.now() - startTime > POLL_TIMEOUT_MS) {
        reject(new Error('Backend failed to start within timeout'));
        return;
      }

      const req = http.get(`${BACKEND_URL}/api/sessions/`, (res) => {
        if (res.statusCode === 200) {
          resolve();
        } else {
          setTimeout(poll, POLL_INTERVAL_MS);
        }
        res.resume(); // consume response data
      });

      req.on('error', () => {
        setTimeout(poll, POLL_INTERVAL_MS);
      });

      req.setTimeout(2000, () => {
        req.destroy();
        setTimeout(poll, POLL_INTERVAL_MS);
      });
    }

    poll();
  });
}

/**
 * Create the main application window.
 */
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
    title: 'Racing Coach',
    show: false,
  });

  // Load the frontend
  if (isDev) {
    // In dev mode, load from the built UI files via backend (which serves static files)
    // or load the dist directly
    const uiDistIndex = path.join(__dirname, '..', 'ui', 'dist', 'index.html');
    if (fs.existsSync(uiDistIndex)) {
      mainWindow.loadFile(uiDistIndex);
    } else {
      // Fallback: load from Vite dev server if UI hasn't been built
      mainWindow.loadURL('http://localhost:5173');
    }
  } else {
    const uiIndex = path.join(process.resourcesPath, 'ui', 'index.html');
    mainWindow.loadFile(uiIndex);
  }

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

/**
 * Kill the Python backend process.
 */
function killBackend() {
  if (pythonProcess) {
    console.log('[backend] shutting down...');
    pythonProcess.kill('SIGTERM');

    // Force kill after 5 seconds if still running
    setTimeout(() => {
      if (pythonProcess) {
        pythonProcess.kill('SIGKILL');
      }
    }, 5000);
  }
}

// App lifecycle
app.whenReady().then(async () => {
  console.log('[app] starting backend...');
  startBackend();

  try {
    await waitForBackend();
    console.log('[app] backend is ready');
  } catch (err) {
    console.error(`[app] ${err.message}`);
    // Still create window — user can see an error or retry
  }

  createWindow();
});

app.on('window-all-closed', () => {
  killBackend();
  app.quit();
});

app.on('before-quit', () => {
  killBackend();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});
