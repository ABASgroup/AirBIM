import api from "./index";

export const getWorkspaces = () => api.get("/workspaces/my");
export const getWorkspace = (id) => api.get(`/workspaces/${id}`);
export const getWorkspaceMembers = (id) => api.get(`/workspaces/${id}/memberships/`);
export const createWorkspace = (name) => api.post("/workspace", { name });
export const deleteWorkspace = (id) => api.delete(`/workspace/${id}`);