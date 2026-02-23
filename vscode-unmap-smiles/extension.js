const vscode = require('vscode');
const cp = require('child_process');
const util = require('util');
const fs = require('fs');
const path = require('path');
const execFile = util.promisify(cp.execFile);

/**
 * Remove atom mapping numbers from SMILES-like text using a regex fallback.
 * Example: "[CH2:1][OH:2]" -> "[CH2][OH]"
 */
function stripAtomMaps(smiles) {
  if (!smiles || typeof smiles !== 'string') return smiles;
  // Replace any :number that appears before a closing bracket inside brackets
  // e.g. [CH2:1] -> [CH2]
  let s = smiles.replace(/\[([^\]]*?):\d+\]/g, '[$1]');
  // In case of multiple mapping occurrences per bracket (rare), remove remaining :digits
  s = s.replace(/:(?:\d+)/g, '');
  return s;
}

async function cleanWithPython(smiles) {
  try {
    const workspaceRoot = (vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders[0].uri.fsPath) || process.cwd();
    const scriptPath = path.join(workspaceRoot, 'tools', 'clean_smiles.py');
    if (!fs.existsSync(scriptPath)) return null;

    // Call python script with the SMILES as an argument
    const python = process.env.PYTHON || 'python';
    const { stdout, stderr } = await execFile(python, [scriptPath, smiles], { cwd: workspaceRoot, timeout: 10000 });
    if (stdout && stdout.trim().length > 0) {
      return stdout.trim();
    }
    return null;
  } catch (err) {
    return null;
  }
}

function activate(context) {
  let disposable = vscode.commands.registerCommand('unmapSmiles.copyUnmapped', async function () {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
      vscode.window.showInformationMessage('No active editor');
      return;
    }

    const sel = editor.selection;
    let text = editor.document.getText(sel);
    if (!text) {
      // try word under cursor
      const wordRange = editor.document.getWordRangeAtPosition(sel.active, /[^\s]+/);
      if (wordRange) text = editor.document.getText(wordRange);
    }

    if (!text) {
      vscode.window.showInformationMessage('No SMILES selected');
      return;
    }

    // First try the Python tool (if present), otherwise fallback to regex
    let cleaned = await cleanWithPython(text);
    let usedPython = true;
    if (!cleaned) {
      cleaned = stripAtomMaps(text);
      usedPython = false;
    }

    try {
      await vscode.env.clipboard.writeText(cleaned);
      vscode.window.showInformationMessage('Copied unmapped SMILES to clipboard' + (usedPython ? ' (via Python)' : ''));
    } catch (e) {
      vscode.window.showErrorMessage('Failed to copy to clipboard: ' + String(e));
    }
  });

  context.subscriptions.push(disposable);
}

function deactivate() {}

module.exports = { activate, deactivate };
