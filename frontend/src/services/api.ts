const BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

export interface SystemStatus {
  status: string;
  database: string;
  cache: string;
}

export interface AIResponse {
  response: string;
  source: string;
}

export interface MCPToolsResponse {
  tools: Array<{
    name: string;
    description: string;
  }>;
}

let activeToken: string | null = "mock-admin"; // Default to Administrator

export const api = {
  setAuthToken(token: string | null) {
    activeToken = token;
  },

  getHeaders(): HeadersInit {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json'
    };
    if (activeToken) {
      headers['Authorization'] = `Bearer ${activeToken}`;
    }
    return headers;
  },

  async getStatus(): Promise<SystemStatus> {
    const res = await fetch(`${BASE_URL}/status`, {
      headers: api.getHeaders()
    });
    if (!res.ok) throw new Error('Failed to fetch status');
    return res.json();
  },

  async queryAI(prompt: string): Promise<AIResponse> {
    const res = await fetch(`${BASE_URL}/query-ai`, {
      method: 'POST',
      headers: api.getHeaders(),
      body: JSON.stringify({ prompt })
    });
    if (!res.ok) {
      const errText = await res.text();
      try {
        const errObj = JSON.parse(errText);
        throw new Error(errObj.detail || 'Failed to query AI');
      } catch {
        throw new Error(errText || 'Failed to query AI');
      }
    }
    return res.json();
  },

  async listMCPTools(serverUrl?: string): Promise<MCPToolsResponse> {
    const url = serverUrl 
      ? `${BASE_URL}/mcp/tools?server_url=${encodeURIComponent(serverUrl)}`
      : `${BASE_URL}/mcp/tools`;
    const res = await fetch(url, {
      headers: api.getHeaders()
    });
    if (!res.ok) throw new Error('Failed to fetch MCP tools');
    return res.json();
  },

  async orchestrate(prompt: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/agents/orchestrate`, {
      method: 'POST',
      headers: api.getHeaders(),
      body: JSON.stringify({ prompt })
    });
    if (!res.ok) {
      const errText = await res.text();
      try {
        const errObj = JSON.parse(errText);
        throw new Error(errObj.detail || 'Failed to run agent orchestration');
      } catch {
        throw new Error(errText || 'Failed to run agent orchestration');
      }
    }
    return res.json();
  },

  async listScenarios(): Promise<any> {
    const res = await fetch(`${BASE_URL}/simulation/scenarios`, {
      headers: api.getHeaders()
    });
    if (!res.ok) throw new Error('Failed to fetch simulation scenarios');
    return res.json();
  },

  async getScenario(id: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/simulation/scenarios/${id}`, {
      headers: api.getHeaders()
    });
    if (!res.ok) throw new Error('Failed to fetch simulation scenario');
    return res.json();
  }
};
