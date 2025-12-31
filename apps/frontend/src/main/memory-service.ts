/**
 * Memory Service
 *
 * Queries the LadybugDB graph database for memories stored by Graphiti.
 * Uses Python subprocess to communicate with the embedded database.
 *
 * LadybugDB stores data in Kuzu format at ~/.auto-claude/memories/<database>/
 */

import { spawn } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';
import { app } from 'electron';
import { findPythonCommand, parsePythonCommand } from './python-detector';
import { getConfiguredPythonPath } from './python-env-manager';
import { getMemoriesDir } from './config-paths';
import type { MemoryEpisode } from '../shared/types';

interface MemoryServiceConfig {
  dbPath: string;
  database: string;
}

// Embedder configuration for semantic search
export interface EmbedderConfig {
  provider: 'openai' | 'google' | 'ollama' | 'voyage' | 'azure_openai';
  // OpenAI
  openaiApiKey?: string;
  openaiEmbeddingModel?: string;
  // Google AI
  googleApiKey?: string;
  googleEmbeddingModel?: string;
  // Ollama
  ollamaBaseUrl?: string;
  ollamaEmbeddingModel?: string;
  ollamaEmbeddingDim?: number;
  // Voyage AI
  voyageApiKey?: string;
  voyageEmbeddingModel?: string;
  // Azure OpenAI
  azureOpenaiApiKey?: string;
  azureOpenaiBaseUrl?: string;
  azureOpenaiEmbeddingDeployment?: string;
}

interface SemanticSearchResult extends MemoryQueryResult {
  search_type: 'semantic' | 'keyword';
  embedder?: string;
}

interface QueryResult {
  success: boolean;
  data?: unknown;
  error?: string;
}

interface MemoryQueryResult {
  memories: Array<{
    id: string;
    name: string;
    type: string;
    timestamp: string;
    content: string;
    description?: string;
    group_id?: string;
    session_number?: number;
    score?: number;
  }>;
  count: number;
  query?: string;
}

interface StatusResult {
  available: boolean;
  ladybugInstalled: boolean;
  databasePath: string;
  database: string;
  databaseExists: boolean;
  connected?: boolean;
  databases?: string[];
  error?: string | null;
}

/**
 * Get the default database path
 * Uses XDG-compliant paths on Linux for AppImage/Flatpak/Snap support
 */
export function getDefaultDbPath(): string {
  return getMemoriesDir();
}

/**
 * Get the path to the query_memory.py script
 */
function getQueryScriptPath(): string | null {
  // Look for the script in backend directory - validate using spec_runner.py marker
  const possiblePaths = [
    // Apps structure: from dist/main -> apps/backend
    path.resolve(__dirname, '..', '..', '..', 'backend', 'query_memory.py'),
    path.resolve(app.getAppPath(), '..', 'backend', 'query_memory.py'),
    path.resolve(process.cwd(), 'apps', 'backend', 'query_memory.py')
  ];

  for (const p of possiblePaths) {
    // Validate backend structure by checking for spec_runner.py marker
    const backendPath = path.dirname(p);
    const specRunnerPath = path.join(backendPath, 'runners', 'spec_runner.py');
    if (fs.existsSync(p) && fs.existsSync(specRunnerPath)) {
      return p;
    }
  }
  return null;
}

/**
 * Execute a Python memory query command
 */
async function executeQuery(
  command: string,
  args: string[],
  timeout: number = 10000
): Promise<QueryResult> {
  const pythonCmd = getConfiguredPythonPath();

  const scriptPath = getQueryScriptPath();
  if (!scriptPath) {
    return { success: false, error: 'query_memory.py script not found' };
  }

  const [pythonExe, baseArgs] = parsePythonCommand(pythonCmd);

  return new Promise((resolve) => {
    const fullArgs = [...baseArgs, scriptPath, command, ...args];
    
    // Pass environment variables to Python subprocess
    // This ensures .env variables are available even if dotenv fails to load
    const env: Record<string, string | undefined> = { ...process.env };
    
    // Get the backend directory for cwd
    const backendDir = path.dirname(scriptPath);
    
    console.log(`[Memory] Executing: ${pythonExe} ${fullArgs.join(' ')}`);
    console.log(`[Memory] Working directory: ${backendDir}`);
    
    const proc = spawn(pythonExe, fullArgs, {
      stdio: ['ignore', 'pipe', 'pipe'],
      timeout,
      env,
      cwd: backendDir,
    });

    let stdout = '';
    let stderr = '';

    proc.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    proc.stderr.on('data', (data) => {
      stderr += data.toString();
      console.error(`[Memory] stderr: ${data.toString().trim()}`);
    });

    proc.on('close', (code) => {
      console.log(`[Memory] Process exited with code ${code}`);
      if (code === 0 && stdout) {
        try {
          const result = JSON.parse(stdout);
          resolve(result);
        } catch {
          console.error(`[Memory] Invalid JSON: ${stdout.substring(0, 500)}`);
          resolve({ success: false, error: `Invalid JSON response: ${stdout}` });
        }
      } else {
        console.error(`[Memory] Failed: ${stderr || `exit code ${code}`}`);
        resolve({
          success: false,
          error: stderr || `Process exited with code ${code}`,
        });
      }
    });

    proc.on('error', (err) => {
      console.error(`[Memory] Process error: ${err.message}`);
      resolve({ success: false, error: err.message });
    });

    // Handle timeout
    setTimeout(() => {
      proc.kill();
      resolve({ success: false, error: 'Query timed out' });
    }, timeout);
  });
}

/**
 * Execute semantic search with embedder configuration passed via environment
 */
async function executeSemanticQuery(
  args: string[],
  embedderConfig: EmbedderConfig,
  timeout: number = 30000 // Longer timeout for embedding operations
): Promise<QueryResult> {
  const pythonCmd = getConfiguredPythonPath();

  const scriptPath = getQueryScriptPath();
  if (!scriptPath) {
    return { success: false, error: 'query_memory.py script not found' };
  }

  const [pythonExe, baseArgs] = parsePythonCommand(pythonCmd);

  // Build environment with embedder configuration
  const env: Record<string, string | undefined> = { ...process.env };

  // Set the embedder provider
  env.GRAPHITI_EMBEDDER_PROVIDER = embedderConfig.provider;

  // Provider-specific configuration
  switch (embedderConfig.provider) {
    case 'openai':
      if (embedderConfig.openaiApiKey) {
        env.OPENAI_API_KEY = embedderConfig.openaiApiKey;
      }
      if (embedderConfig.openaiEmbeddingModel) {
        env.OPENAI_EMBEDDING_MODEL = embedderConfig.openaiEmbeddingModel;
      }
      break;

    case 'google':
      if (embedderConfig.googleApiKey) {
        env.GOOGLE_API_KEY = embedderConfig.googleApiKey;
      }
      if (embedderConfig.googleEmbeddingModel) {
        env.GOOGLE_EMBEDDING_MODEL = embedderConfig.googleEmbeddingModel;
      }
      break;

    case 'ollama':
      if (embedderConfig.ollamaBaseUrl) {
        env.OLLAMA_BASE_URL = embedderConfig.ollamaBaseUrl;
      }
      if (embedderConfig.ollamaEmbeddingModel) {
        env.OLLAMA_EMBEDDING_MODEL = embedderConfig.ollamaEmbeddingModel;
      }
      if (embedderConfig.ollamaEmbeddingDim) {
        env.OLLAMA_EMBEDDING_DIM = String(embedderConfig.ollamaEmbeddingDim);
      }
      break;

    case 'voyage':
      if (embedderConfig.voyageApiKey) {
        env.VOYAGE_API_KEY = embedderConfig.voyageApiKey;
      }
      if (embedderConfig.voyageEmbeddingModel) {
        env.VOYAGE_EMBEDDING_MODEL = embedderConfig.voyageEmbeddingModel;
      }
      break;

    case 'azure_openai':
      if (embedderConfig.azureOpenaiApiKey) {
        env.AZURE_OPENAI_API_KEY = embedderConfig.azureOpenaiApiKey;
      }
      if (embedderConfig.azureOpenaiBaseUrl) {
        env.AZURE_OPENAI_BASE_URL = embedderConfig.azureOpenaiBaseUrl;
      }
      if (embedderConfig.azureOpenaiEmbeddingDeployment) {
        env.AZURE_OPENAI_EMBEDDING_DEPLOYMENT = embedderConfig.azureOpenaiEmbeddingDeployment;
      }
      break;
  }

  return new Promise((resolve) => {
    const fullArgs = [...baseArgs, scriptPath, 'semantic-search', ...args];
    const proc = spawn(pythonExe, fullArgs, {
      stdio: ['ignore', 'pipe', 'pipe'],
      env,
      timeout,
    });

    let stdout = '';
    let stderr = '';

    proc.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    proc.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    proc.on('close', (code) => {
      if (code === 0 && stdout) {
        try {
          const result = JSON.parse(stdout);
          resolve(result);
        } catch {
          resolve({ success: false, error: `Invalid JSON response: ${stdout}` });
        }
      } else {
        resolve({
          success: false,
          error: stderr || `Process exited with code ${code}`,
        });
      }
    });

    proc.on('error', (err) => {
      resolve({ success: false, error: err.message });
    });

    setTimeout(() => {
      proc.kill();
      resolve({ success: false, error: 'Semantic search timed out' });
    }, timeout);
  });
}

/**
 * Memory Service for querying graph memories from LadybugDB
 */
export class MemoryService {
  private config: MemoryServiceConfig;
  
  // Prevent parallel queries that can cause database lock issues
  private pendingEpisodicQuery: Promise<MemoryEpisode[]> | null = null;
  private pendingEntityQuery: Promise<MemoryEpisode[]> | null = null;

  constructor(config: MemoryServiceConfig) {
    this.config = config;
  }

  /**
   * Get the full path to the database
   */
  private getDbFullPath(): string {
    return path.join(this.config.dbPath, this.config.database);
  }

  /**
   * Check if the database exists
   */
  databaseExists(): boolean {
    const dbPath = this.getDbFullPath();
    return fs.existsSync(dbPath);
  }

  /**
   * List all available databases
   */
  listDatabases(): string[] {
    try {
      const basePath = this.config.dbPath;
      if (!fs.existsSync(basePath)) {
        return [];
      }

      return fs.readdirSync(basePath).filter((name) => {
        if (name.startsWith('.')) return false;
        return true; // Include both files and directories
      });
    } catch (error) {
      console.error('Failed to list databases:', error);
      return [];
    }
  }

  /**
   * Query episodic memories from the database
   * Uses deduplication to prevent parallel queries causing database locks
   */
  async getEpisodicMemories(limit: number = 20): Promise<MemoryEpisode[]> {
    // If a query is already in progress, wait for it instead of starting a new one
    if (this.pendingEpisodicQuery) {
      console.log('[Memory] Reusing pending episodic query');
      return this.pendingEpisodicQuery;
    }
    
    this.pendingEpisodicQuery = this._executeEpisodicQuery(limit);
    try {
      return await this.pendingEpisodicQuery;
    } finally {
      this.pendingEpisodicQuery = null;
    }
  }
  
  private async _executeEpisodicQuery(limit: number): Promise<MemoryEpisode[]> {
    const result = await executeQuery('get-memories', [
      this.config.dbPath,
      this.config.database,
      '--limit',
      String(limit),
    ]);

    if (!result.success || !result.data) {
      console.error('Failed to get memories:', result.error);
      return [];
    }

    const data = result.data as MemoryQueryResult;
    return data.memories.map((m) => ({
      id: m.id,
      type: this.mapMemoryType(m.type),
      timestamp: m.timestamp,
      content: m.content,
      session_number: m.session_number,
    }));
  }

  /**
   * Query entity memories (patterns, gotchas, etc.) from the database
   * Uses deduplication to prevent parallel queries causing database locks
   */
  async getEntityMemories(limit: number = 20): Promise<MemoryEpisode[]> {
    // If a query is already in progress, wait for it instead of starting a new one
    if (this.pendingEntityQuery) {
      console.log('[Memory] Reusing pending entity query');
      return this.pendingEntityQuery;
    }
    
    this.pendingEntityQuery = this._executeEntityQuery(limit);
    try {
      return await this.pendingEntityQuery;
    } finally {
      this.pendingEntityQuery = null;
    }
  }
  
  private async _executeEntityQuery(limit: number): Promise<MemoryEpisode[]> {
    const result = await executeQuery('get-entities', [
      this.config.dbPath,
      this.config.database,
      '--limit',
      String(limit),
    ]);

    if (!result.success || !result.data) {
      console.error('Failed to get entities:', result.error);
      return [];
    }

    const data = result.data as { entities: MemoryQueryResult['memories']; count: number };
    return data.entities.map((e) => ({
      id: e.id,
      type: this.mapMemoryType(e.type),
      timestamp: e.timestamp,
      content: e.content,
    }));
  }

  /**
   * Get all memories from the database
   */
  async getAllMemories(limit: number = 20): Promise<MemoryEpisode[]> {
    const [episodic, entities] = await Promise.all([
      this.getEpisodicMemories(limit),
      this.getEntityMemories(limit),
    ]);

    const memories = [...episodic, ...entities];

    // Sort by timestamp descending
    memories.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

    return memories.slice(0, limit);
  }

  /**
   * Search memories in the database (keyword search)
   */
  async searchMemories(searchQuery: string, limit: number = 20): Promise<MemoryEpisode[]> {
    const result = await executeQuery('search', [
      this.config.dbPath,
      this.config.database,
      searchQuery,
      '--limit',
      String(limit),
    ]);

    if (!result.success || !result.data) {
      console.error('Failed to search memories:', result.error);
      return [];
    }

    const data = result.data as MemoryQueryResult;
    return data.memories.map((m) => ({
      id: m.id,
      type: this.mapMemoryType(m.type),
      timestamp: m.timestamp,
      content: m.content,
      session_number: m.session_number,
      score: m.score,
    }));
  }

  /**
   * Semantic search using embeddings
   *
   * Uses the configured embedder to create vector embeddings and perform
   * similarity search. Falls back to keyword search if embedder fails.
   *
   * @param searchQuery The search query
   * @param embedderConfig Configuration for the embedding provider
   * @param limit Maximum number of results
   * @returns Memories with relevance scores
   */
  async searchMemoriesSemantic(
    searchQuery: string,
    embedderConfig: EmbedderConfig,
    limit: number = 20
  ): Promise<{ memories: MemoryEpisode[]; searchType: 'semantic' | 'keyword' }> {
    const result = await executeSemanticQuery(
      [this.config.dbPath, this.config.database, searchQuery, '--limit', String(limit)],
      embedderConfig
    );

    if (!result.success || !result.data) {
      console.error('Semantic search failed, falling back to keyword:', result.error);
      // Fall back to keyword search
      const memories = await this.searchMemories(searchQuery, limit);
      return { memories, searchType: 'keyword' };
    }

    const data = result.data as SemanticSearchResult;
    const memories = data.memories.map((m) => ({
      id: m.id,
      type: this.mapMemoryType(m.type),
      timestamp: m.timestamp,
      content: m.content,
      session_number: m.session_number,
      score: m.score,
    }));

    return {
      memories,
      searchType: data.search_type || 'semantic',
    };
  }

  /**
   * Test connection to the database
   */
  async testConnection(): Promise<{ success: boolean; message: string }> {
    const result = await executeQuery('get-status', [this.config.dbPath, this.config.database]);

    if (!result.success) {
      return {
        success: false,
        message: result.error || 'Failed to check database status',
      };
    }

    const data = result.data as StatusResult;

    if (!data.available) {
      return {
        success: false,
        message: 'LadybugDB (real_ladybug) not installed. Requires Python 3.12+',
      };
    }

    if (!data.databaseExists) {
      return {
        success: false,
        message: `Database not found at ${data.databasePath}/${data.database}`,
      };
    }

    if (!data.connected) {
      return {
        success: false,
        message: data.error || 'Failed to connect to database',
      };
    }

    const dbCount = data.databases?.length || 0;
    return {
      success: true,
      message: `Connected to LadybugDB with ${dbCount} databases`,
    };
  }

  /**
   * Close the database connection (no-op for subprocess model)
   */
  async close(): Promise<void> {
    // No persistent connection to close with subprocess model
  }

  /**
   * Map string type to MemoryEpisode type
   */
  private mapMemoryType(type: string): MemoryEpisode['type'] {
    switch (type) {
      case 'session_insight':
        return 'session_insight';
      case 'pattern':
        return 'pattern';
      case 'gotcha':
        return 'gotcha';
      case 'codebase_discovery':
        return 'codebase_discovery';
      case 'task_outcome':
        return 'task_outcome';
      default:
        return 'session_insight';
    }
  }
}

// Singleton instance for reuse
let serviceInstance: MemoryService | null = null;

/**
 * Get or create a Memory service instance
 */
export function getMemoryService(config: MemoryServiceConfig): MemoryService {
  if (
    !serviceInstance ||
    serviceInstance['config'].dbPath !== config.dbPath ||
    serviceInstance['config'].database !== config.database
  ) {
    serviceInstance = new MemoryService(config);
  }
  return serviceInstance;
}

/**
 * Close the singleton service instance
 */
export async function closeMemoryService(): Promise<void> {
  if (serviceInstance) {
    await serviceInstance.close();
    serviceInstance = null;
  }
}

/**
 * Check if Python with LadybugDB is available
 */
export function isKuzuAvailable(): boolean {
  // Use getConfiguredPythonPath which prefers venv Python
  // (has dependencies installed) over system Python
  const pythonCmd = getConfiguredPythonPath();
  if (!pythonCmd) {
    return false;
  }

  // Check if query script exists
  const scriptPath = getQueryScriptPath();
  return scriptPath !== null;
}

/**
 * Get memory service status
 */
export interface MemoryServiceStatus {
  kuzuInstalled: boolean;
  databasePath: string;
  databaseExists: boolean;
  databases: string[];
}

export function getMemoryServiceStatus(dbPath?: string): MemoryServiceStatus {
  const basePath = dbPath || getDefaultDbPath();

  const databases = fs.existsSync(basePath)
    ? fs.readdirSync(basePath).filter((name) => !name.startsWith('.'))
    : [];

  // Use getConfiguredPythonPath which prefers venv Python
  const pythonCmd = getConfiguredPythonPath();
  const pythonAvailable = pythonCmd !== null && pythonCmd !== 'python';
  const scriptAvailable = getQueryScriptPath() !== null;

  return {
    kuzuInstalled: pythonAvailable && scriptAvailable,
    databasePath: basePath,
    databaseExists: databases.length > 0,
    databases,
  };
}
