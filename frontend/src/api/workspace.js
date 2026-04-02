import api from "./index";

export const getWorkspaces = () => api.get("/workspaces/my");
export const getWorkspace = (id) => api.get(`/workspaces/${id}`);
export const getWorkspaceMembers = (id) => api.get(`/workspaces/${id}/memberships/`);
export const createWorkspace = (name) => api.post("/workspaces", { name });
export const deleteWorkspace = (id) => api.delete(`/workspaces/${id}`);
export const getWorkspaceAccess = (id) => api.get(`/workspaces/${id}/access`);