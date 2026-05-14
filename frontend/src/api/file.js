import api from "./index";
import axios from 'axios';

export const getBimUploadLink = (projectId, data) => api.post(`/projects/${projectId}/bim/upload`, data);
export const confirmBimUpload = (fileId, data) => api.post(`/files/${fileId}/confirm`, data);
export const getBimDownloadLink = (fileId) => api.post(`/files/${fileId}/download`);
export const getProjectBim = (projectId) => api.get(`/projects/${projectId}/bim`);

export const uploadFileWithPresignedLink = async (presignedUrl, file, onProgress) => {
  try {
    await axios.put(presignedUrl, file, {
      headers: {
        "Content-Type": file.type,
      },
      onUploadProgress: onProgress,
    });
    return { success: true };
  } catch (error) {
    return { success: false, error };
  }
};