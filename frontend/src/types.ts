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
}
