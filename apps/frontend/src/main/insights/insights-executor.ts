import { spawn, ChildProcess } from 'child_process';
import { existsSync, writeFileSync, unlinkSync } from 'fs';
import path from 'path';
import os from 'os';
import { EventEmitter } from 'events';
import type {
  InsightsChatMessage,
  InsightsChatStatus,
  InsightsStreamChunk,
  InsightsToolUsage,
  InsightsModelConfig
} from '../../shared/types';
import { MODEL_ID_MAP } from '../../shared/constants';
import { InsightsConfig } from './config';
import { detectRateLimit, createSDKRateLimitInfo } from '../rate-limit-detector';

/**
 * Message processor result
 */
interface ProcessorResult {
  fullResponse: string;
  suggestedTask?: InsightsChatMessage['suggestedTask'];
  toolsUsed: InsightsToolUsage[];
}

/**
 * Python process executor for insights
 * Handles spawning and managing the Python insights runner process
 * 
 * MULTI-SESSION MODE (since 31.12.2025):
 * Supports unlimited parallel sessions per project.
 * Sessions are tracked by sessionId, not projectId.
 */
export class InsightsExecutor extends EventEmitter {
  private config: InsightsConfig;
  // Map of sessionId -> ChildProcess (allows multiple sessions per project)
  private activeSessions: Map<string, ChildProcess> = new Map();
  // Track which sessions belong to which project
  private sessionsByProject: Map<string, Set<string>> = new Map();

  constructor(config: InsightsConfig) {
    super();
    this.config = config;
  }

  /**
   * Check if a specific session is currently active
   */
  isSessionActive(sessionId: string): boolean {
    return this.activeSessions.has(sessionId);
  }

  /**
   * Get all active sessions for a project
   */
  getActiveSessionsForProject(projectId: string): string[] {
    return Array.from(this.sessionsByProject.get(projectId) || []);
  }

  /**
   * Get count of all active sessions
   */
  getActiveSessionCount(): number {
    return this.activeSessions.size;
  }

  /**
   * Cancel a specific session by sessionId
   */
  cancelSession(sessionId: string): boolean {
    const existingProcess = this.activeSessions.get(sessionId);
    if (!existingProcess) return false;

    existingProcess.kill();
    this.activeSessions.delete(sessionId);
    
    // Remove from project tracking
    for (const [projectId, sessions] of this.sessionsByProject.entries()) {
      if (sessions.has(sessionId)) {
        sessions.delete(sessionId);
        if (sessions.size === 0) {
          this.sessionsByProject.delete(projectId);
        }
        break;
      }
    }
    
    return true;
  }

  /**
   * Cancel all sessions for a project
   */
  cancelAllSessionsForProject(projectId: string): number {
    const sessions = this.sessionsByProject.get(projectId);
    if (!sessions) return 0;
    
    let cancelled = 0;
    for (const sessionId of sessions) {
      const proc = this.activeSessions.get(sessionId);
      if (proc) {
        proc.kill();
        this.activeSessions.delete(sessionId);
        cancelled++;
      }
    }
    
    this.sessionsByProject.delete(projectId);
    return cancelled;
  }

  /**
   * Execute insights query
   */
  async execute(
    projectId: string,
    projectPath: string,
    message: string,
    conversationHistory: Array<{ role: string; content: string }>,
    modelConfig?: InsightsModelConfig
  ): Promise<ProcessorResult> {
    // Cancel any existing session
    this.cancelSession(projectId);

    const autoBuildSource = this.config.getAutoBuildSourcePath();
    if (!autoBuildSource) {
      throw new Error('Auto Claude source not found');
    }

    const runnerPath = path.join(autoBuildSource, 'runners', 'insights_runner.py');
    if (!existsSync(runnerPath)) {
      throw new Error('insights_runner.py not found in auto-claude directory');
    }

    // Emit thinking status
    this.emit('status', projectId, {
      phase: 'thinking',
      message: 'Processing your message...'
    } as InsightsChatStatus);

    // Get process environment
    const processEnv = this.config.getProcessEnv();

    // Write conversation history to temp file to avoid Windows command-line length limit
    const historyFile = path.join(
      os.tmpdir(),
      `insights-history-${projectId}-${Date.now()}.json`
    );

    let historyFileCreated = false;
    try {
      writeFileSync(historyFile, JSON.stringify(conversationHistory), 'utf-8');
      historyFileCreated = true;
    } catch (err) {
      console.error('[Insights] Failed to write history file:', err);
      throw new Error('Failed to write conversation history to temp file');
    }

    // Build command arguments
    const args = [
      runnerPath,
      '--project-dir', projectPath,
      '--message', message,
      '--history-file', historyFile
    ];

    // Add model config if provided
    if (modelConfig) {
      const modelId = MODEL_ID_MAP[modelConfig.model] || MODEL_ID_MAP['sonnet'];
      args.push('--model', modelId);
      args.push('--thinking-level', modelConfig.thinkingLevel);
    }

    // Spawn Python process
    const proc = spawn(this.config.getPythonPath(), args, {
      cwd: autoBuildSource,
      env: processEnv
    });

    this.activeSessions.set(projectId, proc);

    return new Promise((resolve, reject) => {
      let fullResponse = '';
      let suggestedTask: InsightsChatMessage['suggestedTask'] | undefined;
      const toolsUsed: InsightsToolUsage[] = [];
      let allInsightsOutput = '';

      proc.stdout?.on('data', (data: Buffer) => {
        const text = data.toString();
        // Collect output for rate limit detection (keep last 10KB)
        allInsightsOutput = (allInsightsOutput + text).slice(-10000);

        // Process output lines
        const lines = text.split('\n');
        for (const line of lines) {
          if (line.startsWith('__TASK_SUGGESTION__:')) {
            this.handleTaskSuggestion(projectId, line, (task) => {
              suggestedTask = task;
            });
          } else if (line.startsWith('__TOOL_START__:')) {
            this.handleToolStart(projectId, line, toolsUsed);
          } else if (line.startsWith('__TOOL_END__:')) {
            this.handleToolEnd(projectId, line);
          } else if (line.trim()) {
            fullResponse += line + '\n';
            this.emit('stream-chunk', projectId, {
              type: 'text',
              content: line + '\n'
            } as InsightsStreamChunk);
          }
        }
      });

      proc.stderr?.on('data', (data: Buffer) => {
        const text = data.toString();
        // Collect stderr for rate limit detection too
        allInsightsOutput = (allInsightsOutput + text).slice(-10000);
        console.error('[Insights]', text);
      });

      proc.on('close', (code) => {
        this.activeSessions.delete(projectId);

        // Cleanup temp file
        if (historyFileCreated && existsSync(historyFile)) {
          try {
            unlinkSync(historyFile);
          } catch (cleanupErr) {
            console.error('[Insights] Failed to cleanup history file:', cleanupErr);
          }
        }

        // Check for rate limit if process failed
        if (code !== 0) {
          this.handleRateLimit(projectId, allInsightsOutput);
        }

        if (code === 0) {
          this.emit('stream-chunk', projectId, {
            type: 'done'
          } as InsightsStreamChunk);

          this.emit('status', projectId, {
            phase: 'complete'
          } as InsightsChatStatus);

          resolve({
            fullResponse: fullResponse.trim(),
            suggestedTask,
            toolsUsed
          });
        } else {
          const error = `Process exited with code ${code}`;
          this.emit('stream-chunk', projectId, {
            type: 'error',
            error
          } as InsightsStreamChunk);

          this.emit('error', projectId, error);
          reject(new Error(error));
        }
      });

      proc.on('error', (err) => {
        this.activeSessions.delete(projectId);

        // Cleanup temp file
        if (historyFileCreated && existsSync(historyFile)) {
          try {
            unlinkSync(historyFile);
          } catch (cleanupErr) {
            console.error('[Insights] Failed to cleanup history file:', cleanupErr);
          }
        }

        this.emit('error', projectId, err.message);
        reject(err);
      });
    });
  }

  /**
   * Handle task suggestion from output
   */
  private handleTaskSuggestion(
    projectId: string,
    line: string,
    onTaskFound: (task: InsightsChatMessage['suggestedTask']) => void
  ): void {
    try {
      const taskJson = line.substring('__TASK_SUGGESTION__:'.length);
      const suggestedTask = JSON.parse(taskJson);
      onTaskFound(suggestedTask);
      this.emit('stream-chunk', projectId, {
        type: 'task_suggestion',
        suggestedTask
      } as InsightsStreamChunk);
    } catch {
      // Not valid JSON, treat as normal text (should not emit here as it's already handled)
    }
  }

  /**
   * Handle tool start marker
   */
  private handleToolStart(
    projectId: string,
    line: string,
    toolsUsed: InsightsToolUsage[]
  ): void {
    try {
      const toolJson = line.substring('__TOOL_START__:'.length);
      const toolData = JSON.parse(toolJson);
      // Accumulate tool usage for persistence
      toolsUsed.push({
        name: toolData.name,
        input: toolData.input,
        timestamp: new Date()
      });
      this.emit('stream-chunk', projectId, {
        type: 'tool_start',
        tool: {
          name: toolData.name,
          input: toolData.input
        }
      } as InsightsStreamChunk);
    } catch {
      // Ignore parse errors for tool markers
    }
  }

  /**
   * Handle tool end marker
   */
  private handleToolEnd(projectId: string, line: string): void {
    try {
      const toolJson = line.substring('__TOOL_END__:'.length);
      const toolData = JSON.parse(toolJson);
      this.emit('stream-chunk', projectId, {
        type: 'tool_end',
        tool: {
          name: toolData.name
        }
      } as InsightsStreamChunk);
    } catch {
      // Ignore parse errors for tool markers
    }
  }

  /**
   * Handle rate limit detection
   */
  private handleRateLimit(projectId: string, output: string): void {
    const rateLimitDetection = detectRateLimit(output);
    if (rateLimitDetection.isRateLimited) {
      console.warn('[Insights] Rate limit detected:', {
        projectId,
        resetTime: rateLimitDetection.resetTime,
        limitType: rateLimitDetection.limitType,
        suggestedProfile: rateLimitDetection.suggestedProfile?.name
      });

      const rateLimitInfo = createSDKRateLimitInfo('other', rateLimitDetection, {
        projectId
      });
      this.emit('sdk-rate-limit', rateLimitInfo);
    }
  }
}
