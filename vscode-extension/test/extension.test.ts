import * as assert from 'assert';
import * as vscode from 'vscode';

suite('SkillForge Extension Test Suite', () => {
  vscode.window.showInformationMessage('Starting SkillForge tests');

  test('Extension should be present', () => {
    const ext = vscode.extensions.getExtension('skillforge.skillforge-vscode');
    assert.ok(ext, 'Extension skillforge.skillforge-vscode should be present');
  });

  test('Extension should activate', async () => {
    const ext = vscode.extensions.getExtension('skillforge.skillforge-vscode');
    if (ext) {
      await ext.activate();
      assert.ok(ext.isActive, 'Extension should be active after activation');
    }
  });

  test('All commands should be registered', async () => {
    const commands = await vscode.commands.getCommands(true);
    const expectedCommands = [
      'skillforge.scaffoldSkill',
      'skillforge.runSkill',
      'skillforge.validateSkill',
      'skillforge.installSkill',
      'skillforge.publishSkill',
      'skillforge.listSkills',
      'skillforge.openDashboard',
      'skillforge.generateOpenApi',
    ];

    for (const cmd of expectedCommands) {
      assert.ok(commands.includes(cmd), `Command ${cmd} should be registered`);
    }
  });

  test('Configuration should have default values', () => {
    const config = vscode.workspace.getConfiguration('skillforge');
    assert.strictEqual(config.get<string>('registryUrl'), 'http://localhost:8000');
    assert.strictEqual(config.get<string>('apiKey'), '');
    assert.strictEqual(config.get<string>('pythonPath'), 'python3');
  });
});
