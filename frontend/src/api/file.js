import api from "./index";

export const getBimUploadLink = (projectId) => api.post(`/projects/${projectId}/files/bim/upload`);
export const confirmBimUpload = (projectId) => api.post(`/projects/${projectId}/files/bim/confirm`);