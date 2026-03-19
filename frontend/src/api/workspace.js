import api from "./index";

export const getWorkspaces = () => api.get("/workspace");
export const createWorkspace = (name) => api.post("/workspace", { name });