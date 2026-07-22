export type NewsPeriod = '1d' | '7d' | '30d';

export interface SourceLink {
  title: string;
  url: string;
  source: string;
  published_at: string | null;
  related_symbols?: string[];
}

export interface SummaryResponse {
  symbol: string;
  company_name?: string | null;
  logo_url?: string | null;
  summary: string;
  bullets: string[];
  sources: SourceLink[];
  period: NewsPeriod;
  generated_at: string;
  cached: boolean;
}
