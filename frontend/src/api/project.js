import api from "./index";

export const getProjects = (workspaceId) => api.get(`/workspace/${workspaceId}/projects`);
export const createProject = (workspaceId, data) => api.post(`/workspace/${workspaceId}/projects`, data);
export const deleteProject = (projectId) => api.delete(`/projects/${projectId}`);
export const updateProject = (projectId, data) => api.patch(`/projects/${projectId}`, data);