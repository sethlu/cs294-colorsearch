import { app, BrowserWindow, ipcMain, dialog } from 'electron'

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
    width: 900,
    height: 556,
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
    width: 1000,
    height: 600,
    useContentSize: true,
    webPreferences: {
      webSecurity: false // This is terrible
    }
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
  colorPickerWindow.focus();
})

ipcMain.on('choose-directory', (event) => {
  const directories = dialog.showOpenDialog(mainWindow, {
    properties: ['openDirectory']
  })

  event.sender.send('choose-directory', directories[0])
})
