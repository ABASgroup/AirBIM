import api from "./index";

export const getWorkspaces = () => api.get("/workspace");
export const createWorkspace = (name) => api.post("/workspace", { name });
export const deleteWorkspace = (id) => api.delete(`/workspace/${id}`);