import api from "./index";

export const getProjects = (workspaceId) => api.get(`/workspaces/${workspaceId}/projects`);
export const getProject = (projectId) => api.get(`/projects/${projectId}`);
export const createProject = (workspaceId, data) => api.post(`/workspaces/${workspaceId}/projects`, data);
export const deleteProject = (projectId) => api.delete(`/projects/${projectId}`);
export const updateProject = (projectId, data) => api.patch(`/projects/${projectId}`, data);