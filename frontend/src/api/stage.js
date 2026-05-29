import api from "./index";
import { uploadFileWithPresignedLink } from "./file";

export const createStage = (projectId) => api.post(`/projects/${projectId}/stages`);
export const getProjectStages = (projectId) => api.get(`/projects/${projectId}/stages`);
export const getStage = (stageId) => api.get(`/stages/${stageId}`);
export const getPointCloudUploadLink = (stageId, data) => api.post(`/stages/${stageId}/clouds/upload`, data);
export const convertPointCloud = (stageId, pointCloudId) => api.post(`/stages/${stageId}/clouds/${pointCloudId}/convert`);
export const getConvertedPointCloudLinks = (stageId, pointCloudId) => api.post(`/stages/${stageId}/clouds/${pointCloudId}/converted`);
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
    const pointCloudId = uploadLinkRes.data.point_cloud.id;

    await uploadPointCloudFile(presignedUrl, file, onProgress);

    const convertRes = await convertPointCloud(stageId, pointCloudId);
    const taskId = convertRes.data.split(": ")[1]; // "started: {task_id}"

    return {
      pointCloudId,
      taskId,
      success: true,
    };
  } catch (error) {
    throw error;
  }
};