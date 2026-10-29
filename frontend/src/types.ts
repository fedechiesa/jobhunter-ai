export interface ProfileInput {
  skills: string[];
  experience_years: number;
  preferred_location: string;
  prefer_remote: boolean;
}

export interface Profile extends ProfileInput {
  id: number;
}

export interface MatchScore {
  id: number;
  job_id: number;
  candidate_id: number;
  score: number;
  skill_score: number;
  experience_score: number;
  location_score: number;
  matched_skills: string[];
  missing_skills: string[];
  algorithm_version: string;
  created_at: string;
}

export interface JobInput {
  title: string;
  company: string;
  description: string;
  location: string;
  remote: boolean;
  required_skills: string[];
  experience_years: number;
  url: string | null;
}

export interface Job extends JobInput {
  id: number;
  source_id: number;
  created_at: string;
  match_score: MatchScore | null;
  provider?: string;
  external_id?: string | null;
  apply_url?: string | null;
  published_at?: string | null;
  first_discovered_at?: string;
  last_seen_at?: string;
  availability?: string;
  discovery_status?: string;
  workplace_type?: string;
  search_priority?: number;
  seniority?: string;
  requirements_inferred?: boolean;
  experience_years_known?: boolean;
}

export interface JobFilters {
  q?: string;
  location?: string;
  provider?: string;
  workplace_type?: string;
  availability?: string;
  discovered_after?: string;
  min_score?: string;
  sort?: string;
}

export interface Source {
  id: number;
  name: string;
  kind: string;
  board_token: string;
  region: string;
  enabled: boolean;
  last_attempt_at: string | null;
  last_success_at: string | null;
  last_error: string | null;
  last_result: Record<string, number | string> | null;
}

export interface SearchPreferences {
  roles: string[];
  technologies: string[];
  locations: string[];
  max_experience_years: number;
  deprioritize_senior: boolean;
}

export interface SyncRun {
  id: number;
  status: string;
  started_at: string;
  finished_at: string | null;
  source_results: Array<{
    source_id: number;
    provider: string;
    board: string;
    status: string;
    fetched?: number;
    new?: number;
    updated?: number;
    unchanged?: number;
    potentially_inactive?: number;
    error?: string;
  }>;
}

export interface SyncStatus {
  running: boolean;
  latest: SyncRun | null;
}
