import api from "./index";
import axios from 'axios';

export const getBimUploadLink = (projectId, data) => api.post(`/projects/${projectId}/files/bim/upload`, data);
export const confirmBimUpload = (projectId, data) => api.post(`/projects/${projectId}/files/bim/confirm`, data);
export const getBimDownloadLink = (projectId) => api.post(`/projects/${projectId}/files/bim/download`);

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