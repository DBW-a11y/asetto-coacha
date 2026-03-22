// In Electron, API calls go to the backend's absolute URL.
// In dev (Vite proxy), relative '/api' works fine.
const BACKEND_URL =
  (window as any).electronAPI?.backendURL ?? '';
const BASE = `${BACKEND_URL}/api`;

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(`${BASE}${url}`);
  if (!res.ok) throw new Error(`API error: ${res.status} ${res.statusText}`);
  return res.json();
}

export interface Session {
  id: string;
  track: string;
  car: string;
  started_at: string;
  ended_at: string | null;
  num_laps: number;
  best_lap_time_ms: number | null;
}

export interface Lap {
  id: number;
  session_id: string;
  lap_number: number;
  lap_time_ms: number;
  is_valid: boolean;
}

export interface SessionDetail extends Session {
  laps: Lap[];
}

export interface TelemetryData {
  timestamp_ms: number[];
  throttle: number[];
  brake: number[];
  steering: number[];
  gear: number[];
  speed_kmh: number[];
  rpm: number[];
  normalized_pos: number[];
  [key: string]: number[];
}

export interface LapAnalysis {
  session: Session;
  lap_number: number;
  metrics: Record<string, number>;
  corners: Array<Record<string, number | string>>;
  score: {
    overall: number;
    braking: number;
    throttle: number;
    consistency: number;
    smoothness: number;
  };
  comparison: {
    positions: number[];
    delta_time_ms: number[];
    delta_speed: number[];
    ref_speed: number[];
    target_speed: number[];
    total_delta_ms: number;
  } | null;
}

export interface CompareResult {
  positions: number[];
  delta_time_ms: number[];
  delta_speed: number[];
  ref_speed: number[];
  target_speed: number[];
  ref_throttle: number[];
  target_throttle: number[];
  ref_brake: number[];
  target_brake: number[];
  total_delta_ms: number;
}

export const api = {
  listSessions: () => fetchJson<Session[]>('/sessions/'),
  getSession: (id: string) => fetchJson<SessionDetail>(`/sessions/${id}`),
  getLapTelemetry: (sessionId: string, lap: number, downsample = 1) =>
    fetchJson<TelemetryData>(`/telemetry/${sessionId}/lap/${lap}?downsample=${downsample}`),
  analyzeLap: (sessionId: string, lap: number) =>
    fetchJson<LapAnalysis>(`/analysis/${sessionId}/lap/${lap}`),
  compareLaps: (sessionId: string, ref: number, target: number) =>
    fetchJson<CompareResult>(`/analysis/${sessionId}/compare?ref_lap=${ref}&target_lap=${target}`),
  getCoaching: (sessionId: string, lap: number) =>
    fetchJson<{ advice: string }>(`/coaching/${sessionId}/lap/${lap}`),
  importLd: async (file: File) => {
    const form = new FormData();
    form.append('file', file);
    const res = await fetch(`${BASE}/sessions/import`, { method: 'POST', body: form });
    if (!res.ok) throw new Error(`Import failed: ${res.status} ${res.statusText}`);
    return res.json() as Promise<{ session_id: string; track: string; car: string; num_laps: number }>;
  },
};
