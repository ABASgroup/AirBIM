import api from "./index";

export const getProjects = (workspaceId) => api.get(`/workspace/${workspaceId}/projects`);
export const createProject = (data) => api.post("/workspace/projects", data);
export const deleteProject = (workspaceId, projectId) => api.delete(`/workspace/${workspaceId}/projects/${projectId}`);