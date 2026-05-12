import { apiPost } from "./client";

export function triggerScan(projectId: string) {
  return apiPost<{ task_id: string }>(`/api/projects/${projectId}/scan`);
}

export function triggerEvaluate(projectId: string) {
  return apiPost<{ task_id: string }>(`/api/projects/${projectId}/evaluate`);
}

export function triggerLoop(projectId: string, maxIterations = 200) {
  return apiPost<{ task_id: string }>(`/api/projects/${projectId}/loop`, { max_iterations: maxIterations });
}
