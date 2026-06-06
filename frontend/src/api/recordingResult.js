import api from "./index";

export const getProjectResults = (projectId) => api.get(`/projects/${projectId}/results`);
export const getRecordingResult = (resultId) => api.get(`/recording_results/${resultId}`);
export const getRecordingResultExcel = (resultId) => api.get(`/recording_results/${resultId}/excel`);
export const getRecordingResultPdf = (resultId) => api.get(`/recording_results/${resultId}/pdf`);
export const getFileDownloadLink = (fileId) => api.post(`/files/${fileId}/download`);
