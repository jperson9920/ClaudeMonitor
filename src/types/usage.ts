// Type definitions for usage payload

export type ComponentStatus = 'ok' | 'partial' | 'error';

export interface Component {
  id: string;
  name: string;
  usage_percent: number;
  tokens_used?: number | null;
  tokens_limit?: number | null;
  reset_time?: string | null;
  raw_reset_text?: string | null;
  last_updated: string;
  status: ComponentStatus;
}

export interface UsagePayload {
  components: Component[];
  found_components: number;
  status: ComponentStatus;
  diagnostics?: any;
  scraped_at?: string | null;
}