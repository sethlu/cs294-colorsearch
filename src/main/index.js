import { app, BrowserWindow, ipcMain } from 'electron'

import '../renderer/store';

/**
 * Set `__static` path to static files in production
 * https://simulatedgreg.gitbooks.io/electron-vue/content/en/using-static-assets.html
 */
if (process.env.NODE_ENV !== 'development') {
  global.__static = require('path').join(__dirname, '/static').replace(/\\/g, '\\\\')
}

const winURL = process.env.NODE_ENV === 'development'
  ? `http://localhost:9080`
  : `file://${__dirname}/index.html`

let mainWindow, colorPickerWindow

function createColorPickerWindow() {
  colorPickerWindow = new BrowserWindow({
    width: 800,
    height: 465,
    useContentSize: true
  })

  colorPickerWindow.loadURL(`${winURL}#color-picker`)

  colorPickerWindow.on('closed', () => {
    colorPickerWindow = null
  })
}

function createMainWindow() {
  /**
   * Initial window options
   */
  mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    useContentSize: true
  })

  mainWindow.loadURL(winURL)

  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

app.on('ready', createMainWindow)

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('activate', () => {
  if (mainWindow === null) {
    createMainWindow()
  }
})

ipcMain.on('focus-color-picker-window', (event, arg) => {
  if (!colorPickerWindow) createColorPickerWindow();
  // colorPickerWindow.focus();
})
