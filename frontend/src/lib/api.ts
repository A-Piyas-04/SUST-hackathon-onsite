export function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
}

export type HealthResponse = {
  status: string;
  app: string;
  environment: string;
  contract_version: string;
  request_id: string | null;
  database: {
    connected: boolean;
    schema_ok: boolean;
    ready: boolean;
    migration_count: number;
    error: string | null;
  };
};

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${getApiBaseUrl()}/health`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`Health check failed with status ${response.status}`);
  }
  return response.json() as Promise<HealthResponse>;
}
