import { apiGet, apiPost, apiDelete } from "./client";

export interface ProjectConfig {
  id: string;
  name: string;
  path: string;
  maven_bin: string;
  maven_settings: string;
  coverage_targets: { line: number; branch: number };
  batch_size: number;
  created_at: string;
  status: string;
  summary?: ProjectSummary;
}

export interface ProjectSummary {
  phase: string;
  initialized: boolean;
  methods: { total: number; pass: number; fail: number; pending: number; in_progress: number };
  coverage: { line: number; branch: number; method: number };
  targets_met: boolean;
}

export interface ClassList {
  classes: Array<{
    name: string;
    package: string;
    type: string;
    methods: Array<{ name: string; signature: string; test_status: string }>;
  }>;
}

export interface CoverageReport {
  overall_coverage: {
    line: number;
    branch: number;
    method: number;
    per_class: Array<{ class: string; line_coverage: number; branch_coverage: number }>;
  };
}

export function listProjects(): Promise<ProjectConfig[]> {
  return apiGet<ProjectConfig[]>("/api/projects");
}

export function getProject(id: string): Promise<ProjectConfig> {
  return apiGet<ProjectConfig>(`/api/projects/${id}`);
}

export function createProject(data: Partial<ProjectConfig>): Promise<ProjectConfig> {
  return apiPost<ProjectConfig>("/api/projects", data);
}

export function deleteProject(id: string): Promise<void> {
  return apiDelete(`/api/projects/${id}`);
}

export function getStatus(id: string): Promise<ProjectSummary> {
  return apiGet<ProjectSummary>(`/api/projects/${id}/status`);
}

export function getClasses(id: string): Promise<ClassList> {
  return apiGet<ClassList>(`/api/projects/${id}/classes`);
}

export function getCoverage(id: string): Promise<CoverageReport> {
  return apiGet<CoverageReport>(`/api/projects/${id}/coverage`);
}

export function getCoverageHistory(id: string): Promise<Array<{ timestamp: string; line_coverage: number; branch_coverage: number }>> {
  return apiGet<Array<{ timestamp: string; line_coverage: number; branch_coverage: number }>>(`/api/projects/${id}/coverage/history`);
}
