import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';

const CLI_COMMAND = 'skillforge';

class SkillForgeTerminal {
  private terminal: vscode.Terminal | undefined;

  show(): vscode.Terminal {
    if (!this.terminal) {
      this.terminal = vscode.window.createTerminal('SkillForge');
    }
    this.terminal.show();
    return this.terminal;
  }

  runCommand(command: string): void {
    const term = this.show();
    term.sendText(command);
  }

  dispose(): void {
    if (this.terminal) {
      this.terminal.dispose();
      this.terminal = undefined;
    }
  }
}

function checkCliInstalled(): boolean {
  const config = vscode.workspace.getConfiguration('skillforge');
  const pythonPath = config.get<string>('pythonPath', 'python3');
  try {
    const result = require('child_process').execSync(
      `${pythonPath} -m ${CLI_COMMAND} --help 2>&1 || ${CLI_COMMAND} --help 2>&1`,
      { encoding: 'utf-8', timeout: 5000 }
    );
    return result.length > 0;
  } catch {
    return false;
  }
}

function getCliCommand(): string {
  const config = vscode.workspace.getConfiguration('skillforge');
  const pythonPath = config.get<string>('pythonPath', 'python3');
  const registryUrl = config.get<string>('registryUrl', '');
  const apiKey = config.get<string>('apiKey', '');

  let cmd = `${pythonPath} -m ${CLI_COMMAND}`;

  if (registryUrl) {
    cmd = `SKILLFORGE_REGISTRY_URL=${registryUrl} ${cmd}`;
  }
  if (apiKey) {
    cmd = `SKILLFORGE_API_KEY=${apiKey} ${cmd}`;
  }

  return cmd;
}

function showCliNotInstalled(): void {
  vscode.window.showErrorMessage(
    'SkillForge CLI is not installed. Install it with: pip install skillforge',
    'Install Guide'
  ).then(selection => {
    if (selection === 'Install Guide') {
      vscode.env.openExternal(vscode.Uri.parse('https://skillforge.ai/docs/installation'));
    }
  });
}

async function scaffoldSkill(): Promise<void> {
  const skillName = await vscode.window.showInputBox({
    prompt: 'Enter the skill name',
    placeHolder: 'my-awesome-skill',
    validateInput: (value: string) => {
      if (!value || value.trim().length === 0) {
        return 'Skill name is required';
      }
      if (!/^[a-z0-9_-]+$/.test(value.trim())) {
        return 'Skill name must contain only lowercase letters, numbers, hyphens, and underscores';
      }
      return null;
    }
  });

  if (!skillName) {
    return;
  }

  const workspaceFolders = vscode.workspace.workspaceFolders;
  let defaultUri: vscode.Uri | undefined;

  if (workspaceFolders && workspaceFolders.length > 0) {
    defaultUri = vscode.Uri.joinPath(workspaceFolders[0].uri, skillName);
  }

  const folderUri = await vscode.window.showSaveDialog({
    defaultUri,
    saveLabel: 'Create Skill',
    title: 'Select location for the new skill'
  });

  if (!folderUri) {
    return;
  }

  const folderPath = folderUri.fsPath;

  try {
    fs.mkdirSync(folderPath, { recursive: true });

    const skillYaml = `name: ${skillName}
version: 0.1.0
description: "A SkillForge skill"
author:
  name: "Your Name"
  contact: ""
inputs:
  - name: message
    type: string
    description: "Input message"
    required: true
outputs:
  - name: result
    type: string
    description: "Output result"
permissions:
  network: false
execution:
  mode: direct
  entrypoint: skill.py
  function: run
tags: []
categories: []
`;

    const skillPy = `def run(message: str) -> dict:
    return {"result": f"Received: {message}"}
`;

    fs.writeFileSync(path.join(folderPath, 'skill.yaml'), skillYaml, 'utf-8');
    fs.writeFileSync(path.join(folderPath, 'skill.py'), skillPy, 'utf-8');
    fs.writeFileSync(path.join(folderPath, '__init__.py'), '', 'utf-8');

    const openFolder = await vscode.window.showInformationMessage(
      `Created skill "${skillName}" at ${folderPath}`,
      'Open Folder'
    );

    if (openFolder === 'Open Folder') {
      vscode.commands.executeCommand('vscode.openFolder', vscode.Uri.file(folderPath));
    }
  } catch (error: any) {
    vscode.window.showErrorMessage(`Failed to create skill: ${error.message}`);
  }
}

async function runSkill(): Promise<void> {
  if (!checkCliInstalled()) {
    showCliNotInstalled();
    return;
  }

  const cli = getCliCommand();
  const terminal = new SkillForgeTerminal();

  try {
    const output = require('child_process').execSync(
      `${cli} registry list 2>&1`,
      { encoding: 'utf-8', timeout: 10000 }
    );

    const skillLines = output.split('\n').filter(line => line.trim().length > 0 && !line.startsWith('┌') && !line.startsWith('│') && !line.startsWith('└') && !line.startsWith('├') && !line.startsWith('─'));
    const skills: string[] = [];

    for (const line of skillLines) {
      const parts = line.split('│').map(p => p.trim()).filter(p => p.length > 0);
      if (parts.length >= 2 && parts[0].length > 0) {
        skills.push(parts[0]);
      }
    }

    if (skills.length === 0) {
      vscode.window.showInformationMessage(
        'No skills installed. Create one with SkillForge: Scaffold New Skill.'
      );
      return;
    }

    const selected = await vscode.window.showQuickPick(skills, {
      placeHolder: 'Select a skill to run'
    });

    if (!selected) {
      return;
    }

    const inputs = await vscode.window.showInputBox({
      prompt: `Enter inputs for "${selected}" (key=value, comma separated)`,
      placeHolder: 'name=World, greeting=Hello'
    });

    if (inputs) {
      const inputArgs = inputs.split(',').map(s => s.trim()).filter(s => s.length > 0).map(s => `--input "${s}"`).join(' ');
      terminal.runCommand(`${cli} skill run "${selected}" ${inputArgs}`);
    } else {
      terminal.runCommand(`${cli} skill run "${selected}"`);
    }
  } catch (error: any) {
    vscode.window.showErrorMessage(`Failed to list skills: ${error.message}`);
  }
}

async function validateSkill(): Promise<void> {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    vscode.window.showWarningMessage('No active editor. Open a skill.yaml file.');
    return;
  }

  if (!checkCliInstalled()) {
    showCliNotInstalled();
    return;
  }

  const documentPath = editor.document.uri.fsPath;
  if (!documentPath.endsWith('skill.yaml') && !documentPath.endsWith('skill.yml')) {
    vscode.window.showWarningMessage('Active file is not a skill manifest. Open skill.yaml or skill.yml.');
    return;
  }

  const cli = getCliCommand();
  const terminal = new SkillForgeTerminal();
  terminal.runCommand(`${cli} skill validate "${path.dirname(documentPath)}"`);
}

async function installSkill(): Promise<void> {
  if (!checkCliInstalled()) {
    showCliNotInstalled();
    return;
  }

  const workspaceFolders = vscode.workspace.workspaceFolders;
  let skillPath = '';

  if (workspaceFolders && workspaceFolders.length > 0) {
    const rootPath = workspaceFolders[0].uri.fsPath;
    const yamlPath = path.join(rootPath, 'skill.yaml');
    const ymlPath = path.join(rootPath, 'skill.yml');

    if (fs.existsSync(yamlPath) || fs.existsSync(ymlPath)) {
      skillPath = rootPath;
    }
  }

  if (!skillPath) {
    const folder = await vscode.window.showOpenDialog({
      canSelectFiles: false,
      canSelectFolders: true,
      canSelectMany: false,
      openLabel: 'Select skill folder'
    });

    if (!folder || folder.length === 0) {
      return;
    }

    skillPath = folder[0].fsPath;
  }

  const cli = getCliCommand();
  const terminal = new SkillForgeTerminal();
  terminal.runCommand(`${cli} registry install "${skillPath}"`);
  vscode.window.showInformationMessage(`Installing skill from ${skillPath}...`);
}

async function publishSkill(): Promise<void> {
  if (!checkCliInstalled()) {
    showCliNotInstalled();
    return;
  }

  const config = vscode.workspace.getConfiguration('skillforge');
  const registryUrl = config.get<string>('registryUrl', '');

  if (!registryUrl) {
    vscode.window.showWarningMessage(
      'Registry URL not configured. Set skillforge.registryUrl in settings.',
      'Open Settings'
    ).then(selection => {
      if (selection === 'Open Settings') {
        vscode.commands.executeCommand('workbench.action.openSettings', 'skillforge.registryUrl');
      }
    });
    return;
  }

  const workspaceFolders = vscode.workspace.workspaceFolders;
  if (!workspaceFolders || workspaceFolders.length === 0) {
    vscode.window.showWarningMessage('Open a skill workspace folder before publishing.');
    return;
  }

  const rootPath = workspaceFolders[0].uri.fsPath;
  const cli = getCliCommand();
  const terminal = new SkillForgeTerminal();
  terminal.runCommand(`${cli} registry publish "${rootPath}" --registry-url "${registryUrl}"`);
  vscode.window.showInformationMessage(`Publishing skill from ${rootPath}...`);
}

async function listSkills(): Promise<void> {
  if (!checkCliInstalled()) {
    showCliNotInstalled();
    return;
  }

  const cli = getCliCommand();
  const terminal = new SkillForgeTerminal();
  terminal.runCommand(`${cli} registry list`);
}

async function openDashboard(): Promise<void> {
  vscode.env.openExternal(vscode.Uri.parse('http://127.0.0.1:7860'));
}

async function generateOpenApi(): Promise<void> {
  if (!checkCliInstalled()) {
    showCliNotInstalled();
    return;
  }

  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    vscode.window.showWarningMessage('No active editor. Open a skill.yaml file.');
    return;
  }

  const documentPath = editor.document.uri.fsPath;
  if (!documentPath.endsWith('skill.yaml') && !documentPath.endsWith('skill.yml')) {
    vscode.window.showWarningMessage('Active file is not a skill manifest.');
    return;
  }

  const workspaceFolders = vscode.workspace.workspaceFolders;
  if (!workspaceFolders || workspaceFolders.length === 0) {
    vscode.window.showWarningMessage('Open a workspace to generate OpenAPI spec.');
    return;
  }

  const outputPath = path.join(workspaceFolders[0].uri.fsPath, 'openapi.json');

  const cli = getCliCommand();
  const terminal = new SkillForgeTerminal();
  terminal.runCommand(`${cli} registry publish "${path.dirname(documentPath)}" --dry-run --output "${outputPath}"`);
  vscode.window.showInformationMessage(`Generating OpenAPI spec to ${outputPath}...`);
}

export function activate(context: vscode.ExtensionContext): void {
  const disposables: vscode.Disposable[] = [
    vscode.commands.registerCommand('skillforge.scaffoldSkill', scaffoldSkill),
    vscode.commands.registerCommand('skillforge.runSkill', runSkill),
    vscode.commands.registerCommand('skillforge.validateSkill', validateSkill),
    vscode.commands.registerCommand('skillforge.installSkill', installSkill),
    vscode.commands.registerCommand('skillforge.publishSkill', publishSkill),
    vscode.commands.registerCommand('skillforge.listSkills', listSkills),
    vscode.commands.registerCommand('skillforge.openDashboard', openDashboard),
    vscode.commands.registerCommand('skillforge.generateOpenApi', generateOpenApi),
  ];

  context.subscriptions.push(...disposables);
}

export function deactivate(): void {
}
