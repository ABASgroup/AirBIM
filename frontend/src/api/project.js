import api from "./index";

export const getProjects = (workspaceId) => api.get(`/workspaces/${workspaceId}/projects`);
export const getProject = (projectId) => api.get(`/projects/${projectId}`);
export const createProject = (workspaceId, data) => api.post(`/workspaces/${workspaceId}/projects`, data);
export const deleteProject = (projectId) => api.delete(`/projects/${projectId}`);
export const updateProject = (projectId, data) => api.patch(`/projects/${projectId}`, data);

export const checkStagesProgress = (projectId, stage1Id, stage2Id, tolerance = 0.05) =>
  api.post(`/projects/${projectId}/stages/progress`, null, {
    params: { stage_1_id: stage1Id, stage_2_id: stage2Id, tolerance },
  });