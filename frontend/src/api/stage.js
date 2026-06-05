import api from "./index";
import { uploadFileWithPresignedLink, confirmBimUpload } from "./file";

export const createStage = (projectId) => api.post(`/projects/${projectId}/stages`, {
  start_date: new Date().toISOString()
});
export const getProjectStages = (projectId) => api.get(`/projects/${projectId}/stages`);
export const getStage = (stageId) => api.get(`/stages/${stageId}`);
export const getPointCloudUploadLink = (stageId, data) => api.post(`/stages/${stageId}/clouds/upload`, data);
export const convertPointCloud = (stageId, pointCloudId) => api.post(`/stages/${stageId}/clouds/${pointCloudId}/convert`);
export const getConvertedPointCloudLinks = (stageId) => api.post(`/stages/${stageId}/clouds/converted`);
export const deleteStage = (stageId) => api.delete(`/stages/${stageId}`);

export const uploadPointCloudFile = async (presignedUrl, file, onProgress) => {
  await uploadFileWithPresignedLink(presignedUrl, file, onProgress);
};

export const uploadAndConvertPointCloud = async (stageId, file, onProgress) => {
  try {
    const uploadLinkRes = await getPointCloudUploadLink(stageId, {
      filename: file.name,
      size: file.size,
      content_type: file.type || "application/octet-stream",
    });

    const presignedUrl = uploadLinkRes.data.url;
    const pointCloudFileId = uploadLinkRes.data.file.id;

    await uploadPointCloudFile(presignedUrl, file, onProgress);

    // IMPORTANT: confirm upload to trigger server-side task creation
    const confirmRes = await confirmBimUpload(pointCloudFileId, {
      filename: file.name,
      size: file.size,
      content_type: file.type || "application/octet-stream",
    });

    const taskId = confirmRes?.data?.task?.id ?? null;

    return {
      pointCloudId: pointCloudFileId,
      taskId,
      success: true,
    };
  } catch (error) {
    throw error;
  }
};