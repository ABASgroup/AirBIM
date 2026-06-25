import api from "./index";

export const createInviteLink = (workspaceId, role) => api.post(`/workspaces/${workspaceId}/invites`, { role });
export const revokeInviteLinks = (workspaceId) => api.post(`/workspaces/${workspaceId}/invites/revoke`);
export const validateInviteLink = (token) => api.get(`/invites/${token}`);
export const acceptInviteLink = (token) => api.post(`/invites/${token}/accept`);