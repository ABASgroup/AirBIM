import api from "./index";

export const getWorkspaces = () => api.get("/workspaces/my");
export const getWorkspace = (id) => api.get(`/workspaces/${id}`);
export const getWorkspaceMembers = (id) => api.get(`/workspaces/${id}/memberships/`);
export const createWorkspace = (name) => api.post("/workspaces", { name });
export const deleteWorkspace = (id) => api.delete(`/workspaces/${id}`);
export const getWorkspaceAccess = (id) => api.get(`/workspaces/${id}/access`);

export const removeWorkspaceMember = (workspaceId, userId) => 
    api.delete(`/workspaces/${workspaceId}/memberships/${userId}`);
export const changeUserRole = (workspaceId, userId, role) =>
     api.patch(`/workspaces/${workspaceId}/memberships/${userId}/role?role=${role}`);