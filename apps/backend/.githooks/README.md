# Git Hooks for Auto-Claude

This directory contains Git hooks that automatically maintain the project index when project files change.

## Installation

To enable these hooks for your project:

```bash
# From the project root
git config core.hooksPath apps/backend/.githooks

# Make hooks executable (Unix/macOS/Linux)
chmod +x apps/backend/.githooks/*
```

## Available Hooks

### `post-merge`

Automatically refreshes `project_index.json` after `git pull` or `git merge` if any of these files changed:
- `package.json`
- `requirements.txt`
- `pyproject.toml`
- `Cargo.toml`
- `go.mod`
- `supabase/config.toml`
- `supabase/functions/*`
- `supabase/migrations/*`

**Benefits:**
- Agents always see the latest project structure
- New Edge Functions are automatically detected
- Database migrations are tracked
- No manual refresh needed after pulling changes

## How It Works

1. After a merge/pull, Git runs the `post-merge` hook
2. Hook checks if any trigger files were modified
3. If yes, runs the project analyzer to regenerate the index
4. New index is immediately available for the next task

## Troubleshooting

If the hook doesn't run:
1. Check that hooks are enabled: `git config core.hooksPath`
2. Verify hook is executable: `ls -la apps/backend/.githooks/post-merge`
3. Test manually: `./apps/backend/.githooks/post-merge`

## Disabling Hooks

To disable hooks temporarily:

```bash
git config --unset core.hooksPath
```

To re-enable:

```bash
git config core.hooksPath apps/backend/.githooks
```

