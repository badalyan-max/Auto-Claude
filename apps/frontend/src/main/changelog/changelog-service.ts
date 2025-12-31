import { EventEmitter } from 'events';
import * as path from 'path';
import { existsSync, readFileSync, writeFileSync } from 'fs';
import { app } from 'electron';
import { AUTO_BUILD_PATHS, DEFAULT_CHANGELOG_PATH } from '../../shared/constants';
import { getToolPath } from '../cli-tool-manager';
import type {
  ChangelogTask,
  TaskSpecContent,
  ChangelogGenerationRequest,
  ChangelogSaveRequest,
  ChangelogSaveResult,
  ExistingChangelog,
  Task,
  ImplementationPlan,
  GitBranchInfo,
  GitTagInfo
} from '../../shared/types';
import { ChangelogGenerator } from './generator';
import { VersionSuggester } from './version-suggester';
import { parseExistingChangelog } from './parser';
import {
  getBranches,
  getTags,
  getCurrentBranch,
  getDefaultBranch,
  getCommits,
  getBranchDiffCommits
} from './git-integration';
import { getValidatedPythonPath } from '../python-detector';
import { getConfiguredPythonPath } from '../python-env-manager';

/**
 * Main changelog service - orchestrates all changelog operations
 * Delegates to specialized modules for specific concerns
 */
export class ChangelogService extends EventEmitter {
  // Python path will be configured by pythonEnvManager after venv is ready
  private _pythonPath: string | null = null;
  private claudePath: string;
  private autoBuildSourcePath: string = '';
  private cachedEnv: Record<string, string> | null = null;
  private debugEnabled: boolean | null = null;
  private generator: ChangelogGenerator | null = null;
  private versionSuggester: VersionSuggester | null = null;

  constructor() {
    super();
    // Use centralized CLI tool manager for Claude detection
    this.claudePath = getToolPath('claude');
    this.debug('ChangelogService initialized with Claude CLI:', this.claudePath);
  }

  /**
   * Check if debug mode is enabled
   * Checks DEBUG from auto-claude/.env and DEBUG from process.env
   */
  private isDebugEnabled(): boolean {
    // Cache the result after first check
    if (this.debugEnabled !== null) {
      return this.debugEnabled;
    }

    // Check process.env first
    if (
      process.env.DEBUG === 'true' ||
      process.env.DEBUG === '1' ||
      process.env.DEBUG === 'true' ||
      process.env.DEBUG === '1'
    ) {
      this.debugEnabled = true;
      return true;
    }

    // Check auto-claude .env file
    const env = this.loadAutoBuildEnv();
    this.debugEnabled = env.DEBUG === 'true' || env.DEBUG === '1';
    return this.debugEnabled;
  }

  /**
   * Debug logging - only logs when DEBUG=true in auto-claude/.env or DEBUG is set
   */
  private debug(...args: unknown[]): void {
    if (this.isDebugEnabled()) {
      console.warn('[ChangelogService]', ...args);
    }
  }

  configure(pythonPath?: string, autoBuildSourcePath?: string): void {
    if (pythonPath) {
      this._pythonPath = getValidatedPythonPath(pythonPath, 'ChangelogService');
    }
    if (autoBuildSourcePath) {
      this.autoBuildSourcePath = autoBuildSourcePath;
    }
  }

  /**
   * Get the configured Python path.
   * Returns explicitly configured path, or falls back to getConfiguredPythonPath()
   * which uses the venv Python if ready.
   */
  private get pythonPath(): string {
    if (this._pythonPath) {
      return this._pythonPath;
    }
    return getConfiguredPythonPath();
  }

  /**
   * Get the auto-claude source path (detects automatically if not configured)
   */
  private getAutoBuildSourcePath(): string | null {
    if (this.autoBuildSourcePath && existsSync(this.autoBuildSourcePath)) {
      return this.autoBuildSourcePath;
    }

    const possiblePaths = [
      // Apps structure: from out/main -> apps/backend
      path.resolve(__dirname, '..', '..', '..', 'backend'),
      path.resolve(app.getAppPath(), '..', 'backend'),
      path.resolve(process.cwd(), 'apps', 'backend')
    ];

    for (const p of possiblePaths) {
      if (existsSync(p) && existsSync(path.join(p, 'runners', 'spec_runner.py'))) {
        return p;
      }
    }
    return null;
  }

  /**
   * Load environment variables from auto-claude .env file
   */
  private loadAutoBuildEnv(): Record<string, string> {
    const autoBuildSource = this.getAutoBuildSourcePath();
    if (!autoBuildSource) return {};

    const envPath = path.join(autoBuildSource, '.env');
    if (!existsSync(envPath)) return {};

    try {
      const envContent = readFileSync(envPath, 'utf-8');
      const envVars: Record<string, string> = {};

      // Handle both Unix (\n) and Windows (\r\n) line endings
      for (const line of envContent.split(/\r?\n/)) {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith('#')) continue;

        const eqIndex = trimmed.indexOf('=');
        if (eqIndex > 0) {
          const key = trimmed.substring(0, eqIndex).trim();
          let value = trimmed.substring(eqIndex + 1).trim();

          if ((value.startsWith('"') && value.endsWith('"')) ||
              (value.startsWith("'") && value.endsWith("'"))) {
            value = value.slice(1, -1);
          }

          envVars[key] = value;
        }
      }

      return envVars;
    } catch {
      return {};
    }
  }

  /**
   * Get or create the generator instance
   */
  private getGenerator(): ChangelogGenerator {
    if (!this.generator) {
      const autoBuildSource = this.getAutoBuildSourcePath();
      if (!autoBuildSource) {
        throw new Error('Auto-build source path not found');
      }

      // Verify claude CLI is available
      if (this.claudePath !== 'claude' && !existsSync(this.claudePath)) {
        throw new Error(`Claude CLI not found. Please ensure Claude Code is installed. Looked for: ${this.claudePath}`);
      }

      const autoBuildEnv = this.loadAutoBuildEnv();

      this.generator = new ChangelogGenerator(
        this.pythonPath,
        this.claudePath,
        autoBuildSource,
        autoBuildEnv,
        this.isDebugEnabled()
      );

      // Forward events from generator
      this.generator.on('generation-complete', (projectId, result) => {
        this.emit('generation-complete', projectId, result);
      });

      this.generator.on('generation-progress', (projectId, progress) => {
        this.emit('generation-progress', projectId, progress);
      });

      this.generator.on('generation-error', (projectId, error) => {
        this.emit('generation-error', projectId, error);
      });

      this.generator.on('rate-limit', (projectId, rateLimitInfo) => {
        this.emit('rate-limit', projectId, rateLimitInfo);
      });
    }

    return this.generator;
  }

  /**
   * Get or create the version suggester instance
   */
  private getVersionSuggester(): VersionSuggester {
    if (!this.versionSuggester) {
      const autoBuildSource = this.getAutoBuildSourcePath();
      if (!autoBuildSource) {
        throw new Error('Auto-build source path not found');
      }

      // Verify claude CLI is available
      if (this.claudePath !== 'claude' && !existsSync(this.claudePath)) {
        throw new Error(`Claude CLI not found. Please ensure Claude Code is installed. Looked for: ${this.claudePath}`);
      }

      this.versionSuggester = new VersionSuggester(
        this.pythonPath,
        this.claudePath,
        autoBuildSource,
        this.isDebugEnabled()
      );
    }

    return this.versionSuggester;
  }

  // ============================================
  // Task Management
  // ============================================

  /**
   * Get completed tasks from a project
   */
  getCompletedTasks(projectPath: string, tasks: Task[], specsBaseDir?: string): ChangelogTask[] {
    const specsDir = path.join(projectPath, specsBaseDir || AUTO_BUILD_PATHS.SPECS_DIR);

    return tasks
      .filter(task => task.status === 'done' && !task.metadata?.archivedAt)
      .map(task => {
        const specDir = path.join(specsDir, task.specId);
        const hasSpecs = existsSync(specDir) && existsSync(path.join(specDir, AUTO_BUILD_PATHS.SPEC_FILE));

        return {
          id: task.id,
          specId: task.specId,
          title: task.title,
          description: task.description,
          completedAt: task.updatedAt,
          hasSpecs
        };
      })
      .sort((a, b) => new Date(b.completedAt).getTime() - new Date(a.completedAt).getTime());
  }

  /**
   * Load spec files for given tasks with enriched context
   */
  async loadTaskSpecs(projectPath: string, taskIds: string[], tasks: Task[], specsBaseDir?: string): Promise<TaskSpecContent[]> {
    const specsDir = path.join(projectPath, specsBaseDir || AUTO_BUILD_PATHS.SPECS_DIR);
    console.log('[ChangelogService] loadTaskSpecs called', { projectPath, specsDir, taskCount: taskIds.length });
    this.debug('loadTaskSpecs called', { projectPath, specsDir, taskCount: taskIds.length });

    const results: TaskSpecContent[] = [];

    for (const taskId of taskIds) {
      const task = tasks.find(t => t.id === taskId);
      if (!task) {
        this.debug('Task not found:', taskId);
        continue;
      }

      const specDir = path.join(specsDir, task.specId);
      this.debug('Loading spec for task', { taskId, specId: task.specId, specDir });

      const content: TaskSpecContent = {
        taskId,
        specId: task.specId
      };

      try {
        // Load spec.md
        const specPath = path.join(specDir, AUTO_BUILD_PATHS.SPEC_FILE);
        if (existsSync(specPath)) {
          content.spec = readFileSync(specPath, 'utf-8');
          this.debug('Loaded spec.md', { specId: task.specId, length: content.spec.length });
        }

        // Load requirements.json
        const requirementsPath = path.join(specDir, AUTO_BUILD_PATHS.REQUIREMENTS);
        if (existsSync(requirementsPath)) {
          content.requirements = JSON.parse(readFileSync(requirementsPath, 'utf-8'));
        }

        // Load qa_report.md
        const qaReportPath = path.join(specDir, AUTO_BUILD_PATHS.QA_REPORT);
        if (existsSync(qaReportPath)) {
          content.qaReport = readFileSync(qaReportPath, 'utf-8');
        }

        // Load implementation_plan.json
        const planPath = path.join(specDir, AUTO_BUILD_PATHS.IMPLEMENTATION_PLAN);
        if (existsSync(planPath)) {
          content.implementationPlan = JSON.parse(readFileSync(planPath, 'utf-8')) as ImplementationPlan;
        }

        // NEW: Load git commits for this task
        content.gitCommits = this.loadTaskCommits(projectPath, specDir);
        console.log(`[ChangelogService] Task ${task.specId}: Loaded ${content.gitCommits?.length || 0} commits`);

        // NEW: Load memory/session insights
        content.sessionInsights = this.loadTaskMemories(specDir);
        console.log(`[ChangelogService] Task ${task.specId}: Loaded ${content.sessionInsights?.length || 0} session insights`);

        // NEW: Load changed files summary
        content.changedFiles = this.loadChangedFiles(projectPath, specDir);
        console.log(`[ChangelogService] Task ${task.specId}: Loaded ${content.changedFiles?.length || 0} changed files`);

      } catch (error) {
        content.error = error instanceof Error ? error.message : 'Failed to load spec files';
        this.debug('Error loading spec', { specId: task.specId, error: content.error });
      }

      results.push(content);
    }

    this.debug('loadTaskSpecs complete', { loadedCount: results.length });
    return results;
  }

  /**
   * Load git commits associated with a task
   * Tries multiple strategies to find commits for this task
   */
  private loadTaskCommits(projectPath: string, specDir: string): string[] {
    try {
      const { execSync } = require('child_process');
      const specId = path.basename(specDir);
      const commits: string[] = [];

      // Strategy 1: Try to find commits from auto-claude branch
      try {
        const branchName = `auto-claude/${specId}`;
        
        // Check if branch exists
        const branchExists = execSync(
          `git rev-parse --verify ${branchName}`,
          { cwd: projectPath, encoding: 'utf-8', timeout: 5000, stdio: 'pipe' }
        ).toString().trim();
        
        if (branchExists) {
          // Get commits from the branch (compared to main)
          const branchCommits = execSync(
            `git log --oneline main..${branchName} --no-merges`,
            { cwd: projectPath, encoding: 'utf-8', timeout: 5000 }
          ).toString().trim();
          
          if (branchCommits) {
            commits.push(...branchCommits.split('\n').filter(line => line.trim()));
          }
        }
      } catch {
        // Branch strategy failed, try next
      }

      // Strategy 2: Search commit messages for spec ID
      if (commits.length === 0) {
        try {
          const searchCommits = execSync(
            `git log --oneline --all --grep="${specId}" --no-merges`,
            { cwd: projectPath, encoding: 'utf-8', timeout: 5000 }
          ).toString().trim();
          
          if (searchCommits) {
            commits.push(...searchCommits.split('\n').filter(line => line.trim()));
          }
        } catch {
          // Search strategy failed
        }
      }

      // Strategy 3: Get recent commits from main (last 50) and filter by file paths from plan
      if (commits.length === 0) {
        try {
          const planPath = path.join(specDir, 'implementation_plan.json');
          if (existsSync(planPath)) {
            const plan = JSON.parse(readFileSync(planPath, 'utf-8'));
            const filesToModify: string[] = [];
            
            // Extract files from plan
            if (plan.phases && Array.isArray(plan.phases)) {
              for (const phase of plan.phases) {
                if (phase.subtasks && Array.isArray(phase.subtasks)) {
                  for (const subtask of phase.subtasks) {
                    if (subtask.files_to_modify && Array.isArray(subtask.files_to_modify)) {
                      filesToModify.push(...subtask.files_to_modify);
                    }
                  }
                }
              }
            }
            
            // If we have files, search for commits that touched them
            if (filesToModify.length > 0) {
              const fileCommits = execSync(
                `git log --oneline -n 50 --no-merges -- ${filesToModify.slice(0, 10).join(' ')}`,
                { cwd: projectPath, encoding: 'utf-8', timeout: 5000 }
              ).toString().trim();
              
              if (fileCommits) {
                commits.push(...fileCommits.split('\n').filter(line => line.trim()));
              }
            }
          }
        } catch {
          // File-based search failed
        }
      }

      return commits.slice(0, 20); // Limit to 20 commits
    } catch {
      return [];
    }
  }

  /**
   * Load session insights/memories for a task
   */
  private loadTaskMemories(specDir: string): Array<{ session: number; insights: any }> {
    try {
      const memoryDir = path.join(specDir, 'memory', 'session_insights');
      if (!existsSync(memoryDir)) {
        return [];
      }

      const { readdirSync } = require('fs');
      const sessionFiles = readdirSync(memoryDir)
        .filter((f: string) => f.startsWith('session_') && f.endsWith('.json'))
        .sort();

      const insights: Array<{ session: number; insights: any }> = [];
      
      for (const file of sessionFiles) {
        try {
          const sessionPath = path.join(memoryDir, file);
          const sessionData = JSON.parse(readFileSync(sessionPath, 'utf-8'));
          insights.push({
            session: sessionData.session_number,
            insights: {
              what_worked: sessionData.what_worked || [],
              patterns: sessionData.discoveries?.patterns_found || [],
              gotchas: sessionData.discoveries?.gotchas_encountered || []
            }
          });
        } catch {
          // Skip invalid session files
        }
      }

      return insights;
    } catch {
      return [];
    }
  }

  /**
   * Load summary of changed files for a task
   * Uses git to find files changed in the task branch
   */
  private loadChangedFiles(projectPath: string, specDir: string): string[] {
    try {
      const { execSync } = require('child_process');
      const specId = path.basename(specDir);

      // Strategy 1: Try worktree branch
      try {
        const worktreePath = path.join(projectPath, '.worktrees', specId);
        const branchName = `auto-claude/${specId}`;
        
        if (existsSync(worktreePath)) {
          const changedFiles = execSync(
            `git diff --name-only main...${branchName}`,
            { cwd: projectPath, encoding: 'utf-8', timeout: 5000 }
          ).toString().trim();
          
          if (changedFiles) {
            return changedFiles.split('\n').filter(line => line.trim());
          }
        }
      } catch {
        // Worktree strategy failed
      }

      // Strategy 2: Check implementation plan for file list
      try {
        const planPath = path.join(specDir, 'implementation_plan.json');
        if (existsSync(planPath)) {
          const plan = JSON.parse(readFileSync(planPath, 'utf-8'));
          const files: string[] = [];
          
          // Extract files from subtasks
          if (plan.phases && Array.isArray(plan.phases)) {
            for (const phase of plan.phases) {
              if (phase.subtasks && Array.isArray(phase.subtasks)) {
                for (const subtask of phase.subtasks) {
                  if (subtask.files_to_modify && Array.isArray(subtask.files_to_modify)) {
                    files.push(...subtask.files_to_modify);
                  }
                }
              }
            }
          }
          
          if (files.length > 0) {
            return [...new Set(files)]; // Deduplicate
          }
        }
      } catch {
        // Plan reading failed
      }

      return [];
    } catch {
      return [];
    }
  }

  // ============================================
  // Git Data Retrieval
  // ============================================

  getBranches(projectPath: string): GitBranchInfo[] {
    return getBranches(projectPath, this.isDebugEnabled());
  }

  getTags(projectPath: string): GitTagInfo[] {
    return getTags(projectPath, this.isDebugEnabled());
  }

  getCurrentBranch(projectPath: string): string {
    return getCurrentBranch(projectPath);
  }

  getDefaultBranch(projectPath: string): string {
    return getDefaultBranch(projectPath);
  }

  getCommits(projectPath: string, options: import('../../shared/types').GitHistoryOptions): import('../../shared/types').GitCommit[] {
    return getCommits(projectPath, options, this.isDebugEnabled());
  }

  getBranchDiffCommits(projectPath: string, options: import('../../shared/types').BranchDiffOptions): import('../../shared/types').GitCommit[] {
    return getBranchDiffCommits(projectPath, options, this.isDebugEnabled());
  }

  // ============================================
  // Changelog Generation
  // ============================================

  generateChangelog(
    projectId: string,
    projectPath: string,
    request: ChangelogGenerationRequest,
    specs?: TaskSpecContent[]
  ): void {
    try {
      const generator = this.getGenerator();
      generator.generate(projectId, projectPath, request, specs);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to initialize generator';
      this.debug('ERROR:', errorMessage);
      this.emit('generation-error', projectId, errorMessage);
    }
  }

  cancelGeneration(projectId: string): boolean {
    if (this.generator) {
      return this.generator.cancel(projectId);
    }
    return false;
  }

  // ============================================
  // File Operations
  // ============================================

  /**
   * Save changelog to file
   */
  saveChangelog(
    projectPath: string,
    request: ChangelogSaveRequest
  ): ChangelogSaveResult {
    const filePath = request.filePath
      ? path.join(projectPath, request.filePath)
      : path.join(projectPath, DEFAULT_CHANGELOG_PATH);

    let finalContent = request.content;

    if (request.mode === 'prepend' && existsSync(filePath)) {
      const existing = readFileSync(filePath, 'utf-8');
      // Add separator between new and existing content
      finalContent = `${request.content}\n\n${existing}`;
    } else if (request.mode === 'append' && existsSync(filePath)) {
      const existing = readFileSync(filePath, 'utf-8');
      finalContent = `${existing}\n\n${request.content}`;
    }

    writeFileSync(filePath, finalContent, 'utf-8');

    return {
      filePath,
      bytesWritten: Buffer.byteLength(finalContent, 'utf-8')
    };
  }

  /**
   * Read existing changelog file
   */
  readExistingChangelog(projectPath: string): ExistingChangelog {
    const filePath = path.join(projectPath, DEFAULT_CHANGELOG_PATH);

    if (!existsSync(filePath)) {
      return { exists: false };
    }

    return parseExistingChangelog(filePath);
  }

  /**
   * Suggest next version based on task types (rule-based)
   */
  suggestVersion(specs: TaskSpecContent[], currentVersion?: string): string {
    // Default starting version
    if (!currentVersion) {
      return '1.0.0';
    }

    const parts = currentVersion.split('.').map(Number);
    if (parts.length !== 3 || parts.some(isNaN)) {
      return '1.0.0';
    }

    const [major, minor, patch] = parts;

    // Analyze specs for version increment decision
    let hasBreakingChanges = false;
    let hasNewFeatures = false;

    for (const spec of specs) {
      const content = (spec.spec || '').toLowerCase();

      if (content.includes('breaking change') || content.includes('breaking:')) {
        hasBreakingChanges = true;
      }

      if (spec.implementationPlan?.workflow_type === 'new_feature' ||
          content.includes('new feature') ||
          content.includes('## added')) {
        hasNewFeatures = true;
      }
    }

    if (hasBreakingChanges) {
      return `${major + 1}.0.0`;
    } else if (hasNewFeatures) {
      return `${major}.${minor + 1}.0`;
    } else {
      return `${major}.${minor}.${patch + 1}`;
    }
  }

  /**
   * Suggest version using AI analysis of git commits
   */
  async suggestVersionFromCommits(
    projectPath: string,
    commits: import('../../shared/types').GitCommit[],
    currentVersion?: string
  ): Promise<{ version: string; reason: string }> {
    try {
      // Default starting version
      if (!currentVersion) {
        return { version: '1.0.0', reason: 'Initial version' };
      }

      const parts = currentVersion.split('.').map(Number);
      if (parts.length !== 3 || parts.some(isNaN)) {
        return { version: '1.0.0', reason: 'Invalid current version, resetting to 1.0.0' };
      }

      // Use AI to analyze commits and suggest version bump
      const suggester = this.getVersionSuggester();
      const suggestion = await suggester.suggestVersionBump(commits, currentVersion);

      this.debug('AI version suggestion', suggestion);

      return {
        version: suggestion.version,
        reason: suggestion.reason
      };
    } catch (error) {
      this.debug('Error in AI version suggestion, falling back to patch bump', error);
      // Fallback to patch bump if AI fails
      const [major, minor, patch] = (currentVersion || '1.0.0').split('.').map(Number);
      return {
        version: `${major}.${minor}.${patch + 1}`,
        reason: 'Patch version bump (AI analysis failed)'
      };
    }
  }
}

// Export singleton instance
export const changelogService = new ChangelogService();
