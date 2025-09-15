const vscode = require('vscode');
const fs = require('fs');
const os = require('os');
const path = require('path');
const crypto = require('crypto');
const { exec } = require('child_process');

function execPromise(cmd) {
  return new Promise((resolve, reject) => {
    exec(cmd, { windowsHide: true }, (err, stdout, stderr) => {
      if (err) reject(stderr || err);
      else resolve(stdout);
    });
  });
}

function saveClipboardToTemp(tmpPath) {
  const platform = process.platform;
  if (platform === 'win32') {
    const safe = tmpPath.replace(/\\/g, '\\\\');
    const ps = `Add-Type -AssemblyName System.Windows.Forms; $img = [System.Windows.Forms.Clipboard]::GetImage(); if ($img -eq $null) { exit 2 }; $img.Save('${safe}','Png')`;
    return execPromise(`powershell -noprofile -command "${ps}"`);
  } else if (platform === 'darwin') {
    return execPromise(`pngpaste '${tmpPath}'`);
  } else {
    return execPromise(`bash -lc "xclip -selection clipboard -t image/png -o > '${tmpPath}'"`);
  }
}

async function pasteImageHash() {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    vscode.window.showErrorMessage('没有打开编辑器窗口');
    return;
  }

  const config = vscode.workspace.getConfiguration('pasteImageHash');
  const destPattern = config.get('path') || '${currentFileDir}/images';
  const algorithm = config.get('algorithm') || 'md5';

  const currentFileDir = path.dirname(editor.document.uri.fsPath);
  const workspaceFolders = vscode.workspace.workspaceFolders || [];
  const projectRoot = (workspaceFolders[0] && workspaceFolders[0].uri.fsPath) || currentFileDir;
  const destDir = destPattern
    .replace(/\$\{currentFileDir\}/g, currentFileDir)
    .replace(/\$\{projectRoot\}/g, projectRoot);

  await fs.promises.mkdir(destDir, { recursive: true }).catch(() => {});

  const tmpPath = path.join(os.tmpdir(), `pasteimg_${Date.now()}.png`);
  try {
    await saveClipboardToTemp(tmpPath);
  } catch (err) {
    vscode.window.showErrorMessage('读取剪贴板失败，请安装依赖工具 (Win: PowerShell, mac: pngpaste, linux: xclip)');
    return;
  }

  let buf = await fs.promises.readFile(tmpPath);
  const hash = crypto.createHash(algorithm).update(buf).digest('hex');
  const fileName = `${hash}.png`;
  const destPath = path.join(destDir, fileName);

  await fs.promises.rename(tmpPath, destPath).catch(async () => {
    await fs.promises.copyFile(tmpPath, destPath);
    await fs.promises.unlink(tmpPath).catch(()=>{});
  });

  let rel = path.relative(currentFileDir, destPath).replace(/\\/g, '/');
  if (!rel.startsWith('.')) rel = './' + rel;

  const insertPattern = config.get('insertPattern') || '![${imageFileNameWithoutExt}](${imageFilePath})';
  const imageFileNameWithoutExt = path.basename(fileName, path.extname(fileName));
  const imageFilePath = rel;

  const insertText = insertPattern
    .replace(/\$\{imageFilePath\}/g, imageFilePath)
    .replace(/\$\{imageFileName\}/g, fileName)
    .replace(/\$\{imageFileNameWithoutExt\}/g, imageFileNameWithoutExt);

  await editor.edit(editBuilder => {
    editBuilder.insert(editor.selection.active, insertText);
  });

  vscode.window.showInformationMessage(`粘贴成功：${fileName}`);
}

function activate(context) {
  const disposable = vscode.commands.registerCommand('pasteImageHash.paste', pasteImageHash);
  context.subscriptions.push(disposable);
}
function deactivate() {}
module.exports = { activate, deactivate };
