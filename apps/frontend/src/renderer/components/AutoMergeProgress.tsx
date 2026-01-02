/**
 * Auto-Merge Progress Component
 * ==============================
 *
 * Shows real-time progress of auto-merge process when task is moved to "Done"
 */

import { useEffect, useState } from 'react';
import { IPC_CHANNELS } from '../../shared/constants';
import { CheckCircle2, XCircle, AlertCircle, Loader2, GitMerge, Upload } from 'lucide-react';

interface AutoMergeProgressProps {
  taskId: string;
}

interface AutoMergeState {
  active: boolean;
  message: string;
  progress: number; // 0-100
  error?: string;
  result?: {
    merged: boolean;
    pushed: boolean;
    commitCount?: number;
    aiValidation?: {
      quality: number;
      issues: string[];
    };
    mergeCommit?: string;
  };
}

export function AutoMergeProgress({ taskId }: AutoMergeProgressProps) {
  const [state, setState] = useState<AutoMergeState>({
    active: false,
    message: '',
    progress: 0
  });

  useEffect(() => {
    // Listen for auto-merge progress updates
    const handleProgress = (_event: unknown, data: { taskId: string; message: string; progress: number }) => {
      if (data.taskId === taskId) {
        setState({
          active: true,
          message: data.message,
          progress: data.progress
        });
      }
    };

    const handleComplete = (_event: unknown, data: { taskId: string; result: NonNullable<AutoMergeState['result']> }) => {
      if (data.taskId === taskId) {
        setState({
          active: false,
          message: 'Auto-merge complete!',
          progress: 100,
          result: data.result
        });
      }
    };

    const handleFailed = (_event: unknown, data: { taskId: string; error: string; aiValidation?: AutoMergeState['result']  ['aiValidation'] }) => {
      if (data.taskId === taskId) {
        setState({
          active: false,
          message: 'Auto-merge failed',
          progress: 0,
          error: data.error,
          result: data.aiValidation ? { merged: false, pushed: false, aiValidation: data.aiValidation } : undefined
        });
      }
    };

    window.electronAPI.on(IPC_CHANNELS.TASK_AUTO_MERGE_PROGRESS, handleProgress);
    window.electronAPI.on(IPC_CHANNELS.TASK_AUTO_MERGE_COMPLETE, handleComplete);
    window.electronAPI.on(IPC_CHANNELS.TASK_AUTO_MERGE_FAILED, handleFailed);

    return () => {
      window.electronAPI.off(IPC_CHANNELS.TASK_AUTO_MERGE_PROGRESS, handleProgress);
      window.electronAPI.off(IPC_CHANNELS.TASK_AUTO_MERGE_COMPLETE, handleComplete);
      window.electronAPI.off(IPC_CHANNELS.TASK_AUTO_MERGE_FAILED, handleFailed);
    };
  }, [taskId]);

  // Don't render if not active and no result
  if (!state.active && !state.result && !state.error) {
    return null;
  }

  return (
    <div className="rounded-lg border border-border bg-card p-4 mt-4">
      <div className="flex items-start gap-3">
        {/* Icon */}
        <div className="flex-shrink-0 mt-0.5">
          {state.active ? (
            <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />
          ) : state.error ? (
            <XCircle className="h-5 w-5 text-destructive" />
          ) : state.result?.merged ? (
            <CheckCircle2 className="h-5 w-5 text-success" />
          ) : (
            <AlertCircle className="h-5 w-5 text-warning" />
          )}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-medium mb-1">
            {state.active ? 'Auto-Merging to Main...' : state.error ? 'Auto-Merge Failed' : 'Auto-Merge Complete'}
          </h4>

          {/* Message */}
          <p className="text-sm text-muted-foreground mb-2">
            {state.message}
          </p>

          {/* Progress Bar (when active) */}
          {state.active && (
            <div className="w-full bg-secondary rounded-full h-2 mb-3">
              <div
                className="bg-primary h-2 rounded-full transition-all duration-300"
                style={{ width: `${state.progress}%` }}
              />
            </div>
          )}

          {/* Error Details */}
          {state.error && (
            <div className="bg-destructive/10 border border-destructive/20 rounded p-3 text-sm">
              <p className="text-destructive font-medium mb-1">Error:</p>
              <p className="text-destructive/80">{state.error}</p>

              {state.result?.aiValidation && state.result.aiValidation.issues.length > 0 && (
                <div className="mt-3">
                  <p className="text-destructive font-medium mb-2">AI Validation Issues:</p>
                  <ul className="list-disc list-inside space-y-1">
                    {state.result.aiValidation.issues.map((issue, idx) => (
                      <li key={idx} className="text-destructive/80">{issue}</li>
                    ))}
                  </ul>
                  <p className="text-destructive/70 text-xs mt-2">
                    Quality Score: {state.result.aiValidation.quality}/100
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Success Details */}
          {state.result && !state.error && (
            <div className="bg-success/10 border border-success/20 rounded p-3 text-sm space-y-2">
              {/* Merge Status */}
              {state.result.merged && (
                <div className="flex items-center gap-2 text-success">
                  <GitMerge className="h-4 w-4" />
                  <span>
                    Merged {state.result.commitCount || 0} commit(s) to main
                  </span>
                </div>
              )}

              {/* Push Status */}
              {state.result.pushed && (
                <div className="flex items-center gap-2 text-success">
                  <Upload className="h-4 w-4" />
                  <span>Pushed to GitHub</span>
                </div>
              )}

              {/* AI Validation */}
              {state.result.aiValidation && (
                <div className="pt-2 border-t border-success/20">
                  <p className="text-success/80 text-xs">
                    AI Validation: {state.result.aiValidation.quality}/100 Quality Score
                  </p>
                  {state.result.aiValidation.issues.length === 0 && (
                    <p className="text-success/70 text-xs">✓ No issues found</p>
                  )}
                </div>
              )}

              {/* Merge Commit */}
              {state.result.mergeCommit && (
                <div className="pt-2 border-t border-success/20">
                  <p className="text-success/70 text-xs font-mono">
                    {state.result.mergeCommit.substring(0, 8)}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
