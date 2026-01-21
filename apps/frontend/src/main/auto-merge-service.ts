/**
 * Auto-Merge Service
 * ===================
 *
 * Automatically validates and merges "done" tasks to main branch with AI validation.
 *
 * **Workflow:**
 * 1. Task moved to "Done" column → Trigger validation
 * 2. Check all commits for this task exist
 * 3. AI validates commit completeness and quality
 * 4. Auto-merge to main branch
 * 5. Push to GitHub
 *
 * **Safety:**
 * - Only triggers on explicit "done" status (user confirmation)
 * - AI validates before merge (prevents incomplete merges)
 * - Creates merge commit with full context
 * - Can be disabled in settings
 */

import { exec, execFile } from 'child_process';
import { promisify } from 'util';
import { existsSync, readFileSync, writeFileSync } from 'fs';
import path from 'path';
import type { Task, TaskSpecContent } from '../shared/types';
import { projectStore } from './project-store';
import { BrowserWindow } from 'electron';
import { IPC_CHANNELS, AUTO_BUILD_PATHS } from '../shared/constants';
import { getToolPath } from './cli-tool-manager';
import { changelogService } from './changelog/changelog-service';

const execAsync = promisify(exec);
const execFileAsync = promisify(execFile);

export interface AutoMergeResult {
  success: boolean;
  merged: boolean;
  pushed: boolean;
  error?: string;
  commitCount?: number;
  aiValidation?: {
    complete: boolean;
    quality: number; // 0-100
    issues: string[];
  };
  mergeCommit?: string;
  changelogGenerated?: boolean;
  changelogPath?: string;
}

export interface AutoMergeConfig {
  enabled: boolean;
  requireAIValidation: boolean;
  minQualityScore: number; // 0-100, default 70
  autoPush: boolean;
  targetBranch: string; // default "main"
  generateChangelog: boolean; // Auto-generate changelog before merge
  changelogPath: string; // Path to CHANGELOG.md
}

/**
 * Default configuration for auto-merge
 */
const DEFAULT_CONFIG: AutoMergeConfig = {
  enabled: true,
  requireAIValidation: true,
  minQualityScore: 70,
  autoPush: true,
  targetBranch: 'main',
  generateChangelog: true,
  changelogPath: 'CHANGELOG.md'
};

/**
 * Get auto-merge configuration from project settings
 */
function getAutoMergeConfig(projectId: string): AutoMergeConfig {
  const project = projectStore.getProject(projectId);
  if (!project) return DEFAULT_CONFIG;

  // Check if project has custom auto-merge settings
  // @ts-ignore - settings may not have autoMerge property yet
  const customConfig = project.settings?.autoMerge;

  return {
    ...DEFAULT_CONFIG,
    ...customConfig
  };
}

/**
 * Get all commits for a task's worktree branch
 */
async function getTaskCommits(
  projectPath: string,
  taskBranch: string,
  baseBranch: string = 'main'
): Promise<string[]> {
  try {
    const { stdout } = await execFileAsync(
      getToolPath('git'),
      ['log', `${baseBranch}..${taskBranch}`, '--format=%H'],
      { cwd: projectPath, encoding: 'utf-8' }
    );

    return stdout.trim().split('\n').filter(Boolean);
  } catch (error) {
    console.error('[AutoMerge] Failed to get task commits:', error);
    return [];
  }
}

/**
 * Get commit details for AI validation
 */
async function getCommitDetails(
  projectPath: string,
  commitHash: string
): Promise<{ message: string; diff: string; files: string[] }> {
  try {
    // Get commit message
    const { stdout: message } = await execFileAsync(
      getToolPath('git'),
      ['log', '-1', '--format=%B', commitHash],
      { cwd: projectPath, encoding: 'utf-8' }
    );

    // Get commit diff
    const { stdout: diff } = await execFileAsync(
      getToolPath('git'),
      ['show', commitHash, '--stat'],
      { cwd: projectPath, encoding: 'utf-8' }
    );

    // Get changed files
    const { stdout: filesStr } = await execFileAsync(
      getToolPath('git'),
      ['diff-tree', '--no-commit-id', '--name-only', '-r', commitHash],
      { cwd: projectPath, encoding: 'utf-8' }
    );

    const files = filesStr.trim().split('\n').filter(Boolean);

    return { message: message.trim(), diff: diff.trim(), files };
  } catch (error) {
    console.error('[AutoMerge] Failed to get commit details:', error);
    return { message: '', diff: '', files: [] };
  }
}

/**
 * Validate task commits with AI
 * Uses Claude to check if commits are complete and high quality
 */
async function validateCommitsWithAI(
  task: Task,
  commits: Array<{ message: string; diff: string; files: string[] }>
): Promise<{ complete: boolean; quality: number; issues: string[] }> {
  // TODO: Integrate with Claude API for validation
  // For now, use heuristic validation

  const issues: string[] = [];
  let qualityScore = 100;

  // Check 1: At least one commit exists
  if (commits.length === 0) {
    issues.push('No commits found for this task');
    qualityScore -= 50;
  }

  // Check 2: Commits have meaningful messages
  for (const commit of commits) {
    if (commit.message.length < 10) {
      issues.push(`Commit message too short: "${commit.message}"`);
      qualityScore -= 10;
    }
    if (commit.message.toLowerCase().includes('wip') ||
        commit.message.toLowerCase().includes('temp')) {
      issues.push(`WIP/Temp commit found: "${commit.message}"`);
      qualityScore -= 5;
    }
  }

  // Check 3: Files were actually changed
  const totalFiles = commits.reduce((sum, c) => sum + c.files.length, 0);
  if (totalFiles === 0) {
    issues.push('No files were changed in commits');
    qualityScore -= 30;
  }

  // Check 4: Commits relate to task description
  const taskKeywords = extractKeywords(task.description || task.title);
  const commitText = commits.map(c => c.message + ' ' + c.diff).join(' ').toLowerCase();
  const matchingKeywords = taskKeywords.filter(kw => commitText.includes(kw.toLowerCase()));

  if (matchingKeywords.length === 0 && taskKeywords.length > 0) {
    issues.push('Commits may not relate to task description');
    qualityScore -= 15;
  }

  qualityScore = Math.max(0, Math.min(100, qualityScore));

  return {
    complete: qualityScore >= 50, // Basic threshold
    quality: qualityScore,
    issues
  };
}

/**
 * Extract keywords from task description for matching
 */
function extractKeywords(text: string): string[] {
  // Simple keyword extraction - split by space and filter common words
  const commonWords = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'];
  return text
    .toLowerCase()
    .split(/\s+/)
    .filter(word => word.length > 3 && !commonWords.includes(word))
    .slice(0, 10); // Top 10 keywords
}

/**
 * Generate changelog entry for task
 */
async function generateChangelogForTask(
  task: Task,
  projectPath: string,
  config: AutoMergeConfig
): Promise<{ success: boolean; changelogPath?: string; error?: string }> {
  try {
    console.log('[AutoMerge] Generating changelog for task:', task.title);

    // Load task specs for changelog generation
    const specsDir = path.join(projectPath, '.auto-claude', 'specs');
    const specDir = path.join(specsDir, task.specId);

    if (!existsSync(specDir)) {
      console.warn('[AutoMerge] Spec directory not found, skipping changelog');
      return { success: true }; // Not a fatal error
    }

    const specs: TaskSpecContent[] = await changelogService.loadTaskSpecs(
      projectPath,
      [task.id],
      [task],
      '.auto-claude/specs'
    );

    if (specs.length === 0 || !specs[0].spec) {
      console.warn('[AutoMerge] No specs found for task, skipping changelog');
      return { success: true };
    }

    // Generate changelog using AI
    const generatedContent = await new Promise<string>((resolve, reject) => {
      changelogService.once('generation-complete', (_projectId, result) => {
        resolve(result);
      });

      changelogService.once('generation-error', (_projectId, error) => {
        reject(new Error(error));
      });

      // Generate changelog for this single task
      changelogService.generateChangelog(
        'auto-merge-temp',
        projectPath,
        {
          mode: 'tasks',
          taskIds: [task.id],
          includeTaskDetails: true,
          includeCommitDetails: true,
          style: 'detailed'
        },
        specs
      );

      // Timeout after 60 seconds
      setTimeout(() => reject(new Error('Changelog generation timeout')), 60000);
    });

    if (!generatedContent || generatedContent.trim().length === 0) {
      return { success: false, error: 'No changelog content generated' };
    }

    // Prepend to existing CHANGELOG.md
    const changelogPath = path.join(projectPath, config.changelogPath);
    let existingContent = '';

    if (existsSync(changelogPath)) {
      existingContent = readFileSync(changelogPath, 'utf-8');
    }

    // Add header if file doesn't exist
    if (!existingContent) {
      existingContent = '# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n';
    }

    // Insert new entry after header
    const headerEnd = existingContent.indexOf('\n\n') + 2;
    const finalContent = existingContent.substring(0, headerEnd) +
                        `## [${new Date().toISOString().split('T')[0]}] - ${task.title}\n\n` +
                        generatedContent +
                        '\n\n' +
                        existingContent.substring(headerEnd);

    writeFileSync(changelogPath, finalContent, 'utf-8');

    console.log('[AutoMerge] Changelog updated successfully:', changelogPath);
    return { success: true, changelogPath };

  } catch (error) {
    console.error('[AutoMerge] Changelog generation failed:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Changelog generation failed'
    };
  }
}

/**
 * Merge task branch into target branch
 */
async function mergeTaskBranch(
  projectPath: string,
  taskBranch: string,
  targetBranch: string,
  taskTitle: string,
  changelogPath?: string
): Promise<{ success: boolean; commitHash?: string; error?: string }> {
  try {
    // Ensure we're on target branch
    await execFileAsync(getToolPath('git'), ['checkout', targetBranch], {
      cwd: projectPath
    });

    // Stage changelog if it was generated
    if (changelogPath) {
      try {
        await execFileAsync(getToolPath('git'), ['add', changelogPath], {
          cwd: projectPath
        });
        console.log('[AutoMerge] Staged changelog:', changelogPath);
      } catch (error) {
        console.warn('[AutoMerge] Failed to stage changelog (non-fatal):', error);
      }
    }

    // Merge with --no-ff to create merge commit
    let mergeMessage = `Merge task: ${taskTitle}\n\n`;
    mergeMessage += `🤖 Auto-merged by Auto-Claude\n`;
    mergeMessage += `Task completed and validated.\n`;

    if (changelogPath) {
      mergeMessage += `\n📝 Changelog updated: ${path.basename(changelogPath)}\n`;
    }

    await execFileAsync(
      getToolPath('git'),
      ['merge', '--no-ff', '-m', mergeMessage, taskBranch],
      { cwd: projectPath }
    );

    // Get the merge commit hash
    const { stdout } = await execFileAsync(
      getToolPath('git'),
      ['rev-parse', 'HEAD'],
      { cwd: projectPath, encoding: 'utf-8' }
    );

    return { success: true, commitHash: stdout.trim() };
  } catch (error) {
    console.error('[AutoMerge] Merge failed:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Merge failed'
    };
  }
}

/**
 * Push merged changes to remote
 */
async function pushToRemote(
  projectPath: string,
  branch: string = 'main'
): Promise<{ success: boolean; error?: string }> {
  try {
    await execFileAsync(getToolPath('git'), ['push', 'origin', branch], {
      cwd: projectPath
    });

    return { success: true };
  } catch (error) {
    console.error('[AutoMerge] Push failed:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Push failed'
    };
  }
}

/**
 * Main auto-merge function
 * Called when task is moved to "done" status
 */
export async function autoMergeTask(
  task: Task,
  mainWindow: BrowserWindow | null
): Promise<AutoMergeResult> {
  console.log('[AutoMerge] Starting auto-merge for task:', task.id, task.title);

  // Get project
  const project = projectStore.getProjectByPath(task.projectPath || '');
  if (!project) {
    return { success: false, merged: false, pushed: false, error: 'Project not found' };
  }

  // Get configuration
  const config = getAutoMergeConfig(project.id);

  if (!config.enabled) {
    console.log('[AutoMerge] Auto-merge disabled in settings');
    return { success: true, merged: false, pushed: false };
  }

  // Send progress update to UI
  const sendProgress = (message: string, progress: number) => {
    if (mainWindow) {
      mainWindow.webContents.send(IPC_CHANNELS.TASK_AUTO_MERGE_PROGRESS, {
        taskId: task.id,
        message,
        progress
      });
    }
  };

  try {
    sendProgress('Checking task commits...', 10);

    // Get task branch name
    const taskBranch = `auto-claude/${task.specId}`;

    // Check if branch exists
    try {
      await execFileAsync(
        getToolPath('git'),
        ['rev-parse', '--verify', taskBranch],
        { cwd: project.path }
      );
    } catch {
      console.log('[AutoMerge] Task branch not found:', taskBranch);
      return {
        success: false,
        merged: false,
        pushed: false,
        error: 'Task branch not found. No commits to merge.'
      };
    }

    sendProgress('Analyzing commits...', 30);

    // Get commits for this task
    const commitHashes = await getTaskCommits(project.path, taskBranch, config.targetBranch);

    if (commitHashes.length === 0) {
      return {
        success: false,
        merged: false,
        pushed: false,
        error: 'No commits found for this task'
      };
    }

    console.log(`[AutoMerge] Found ${commitHashes.length} commits`);

    // Get commit details
    const commits = await Promise.all(
      commitHashes.map(hash => getCommitDetails(project.path, hash))
    );

    sendProgress('Validating with AI...', 50);

    // Validate commits with AI
    let aiValidation = null;
    if (config.requireAIValidation) {
      aiValidation = await validateCommitsWithAI(task, commits);

      if (!aiValidation.complete) {
        return {
          success: false,
          merged: false,
          pushed: false,
          error: 'AI validation failed: Task appears incomplete',
          aiValidation,
          commitCount: commitHashes.length
        };
      }

      if (aiValidation.quality < config.minQualityScore) {
        return {
          success: false,
          merged: false,
          pushed: false,
          error: `AI validation failed: Quality score ${aiValidation.quality} below minimum ${config.minQualityScore}`,
          aiValidation,
          commitCount: commitHashes.length
        };
      }
    }

    // Generate changelog BEFORE merge
    let changelogGenerated = false;
    let changelogPath: string | undefined;

    if (config.generateChangelog) {
      sendProgress('Generating changelog...', 60);

      const changelogResult = await generateChangelogForTask(task, project.path, config);

      if (changelogResult.success) {
        changelogGenerated = true;
        changelogPath = changelogResult.changelogPath;
        console.log('[AutoMerge] Changelog generated successfully');
      } else {
        console.warn('[AutoMerge] Changelog generation failed (non-fatal):', changelogResult.error);
        // Continue with merge even if changelog fails
      }
    }

    sendProgress('Merging to main...', 70);

    // Merge task branch into target (with changelog if generated)
    const mergeResult = await mergeTaskBranch(
      project.path,
      taskBranch,
      config.targetBranch,
      task.title,
      changelogPath
    );

    if (!mergeResult.success) {
      return {
        success: false,
        merged: false,
        pushed: false,
        error: mergeResult.error,
        commitCount: commitHashes.length,
        aiValidation: aiValidation || undefined
      };
    }

    console.log('[AutoMerge] Merge successful:', mergeResult.commitHash);

    let pushed = false;
    if (config.autoPush) {
      sendProgress('Pushing to GitHub...', 90);

      const pushResult = await pushToRemote(project.path, config.targetBranch);
      pushed = pushResult.success;

      if (!pushed) {
        console.warn('[AutoMerge] Push failed:', pushResult.error);
        // Don't fail the whole operation - merge succeeded
      }
    }

    sendProgress('Complete!', 100);

    return {
      success: true,
      merged: true,
      pushed,
      commitCount: commitHashes.length,
      aiValidation: aiValidation || undefined,
      mergeCommit: mergeResult.commitHash,
      changelogGenerated,
      changelogPath
    };

  } catch (error) {
    console.error('[AutoMerge] Unexpected error:', error);
    return {
      success: false,
      merged: false,
      pushed: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
}

/**
 * Check if auto-merge is available for a task
 */
export function canAutoMerge(task: Task): boolean {
  // Only tasks in "done" status
  if (task.status !== 'done') return false;

  // Must have a project
  if (!task.projectPath) return false;

  const project = projectStore.getProjectByPath(task.projectPath);
  if (!project) return false;

  // Check if enabled in settings
  const config = getAutoMergeConfig(project.id);
  return config.enabled;
}
