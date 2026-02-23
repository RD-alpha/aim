# Copy Unmapped SMILES — VS Code Extension (local)

This small extension adds a context-menu command to copy the selected SMILES with atom-map numbers removed.

Installation (developer/simple local use):

1. Open the workspace folder `vscode-unmap-smiles` in VS Code.
2. Run the Extension: Open the Debug view and "Run Extension" (Launch Extension) to load a development host window.
3. In an editor, select a SMILES string, right-click and choose "Copy as Unmapped SMILES".

Notes:
- The command removes atom mapping tokens like `:1` inside square brackets, e.g. `[CH2:1]` -> `[CH2]`.
- The extension is a simple local developer extension — to publish/use more widely, package and install it as a VSIX.
