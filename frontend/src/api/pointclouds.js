import api from "./index";

export const uploadCloud = (stageId, data) => api.post(`/stages/${stageId}/clouds/upload`, data);
export const convertCloud = (stageId, cloudId) => api.post(`/stages/${stageId}/clouds/${cloudId}/convert`);
export const getConvertedLinks = (stageId, cloudId) => api.post(`/stages/${stageId}/clouds/${cloudId}/converted`);