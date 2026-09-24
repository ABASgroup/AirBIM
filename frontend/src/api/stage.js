import api from "./index";
import { uploadFileWithPresignedLink, confirmBimUpload } from "./file";

export const createStage = (projectId, data = {}) => api.post(`/projects/${projectId}/stages`, {
  start_date: data.start_date ?? new Date().toISOString(),
  name: data.name,
  description: data.description,
});
export const getProjectStages = (projectId) => api.get(`/projects/${projectId}/stages`);
export const getStage = (stageId) => api.get(`/stages/${stageId}`);
export const getPointCloudUploadLink = (stageId, data) => api.post(`/stages/${stageId}/clouds/upload`, data);
export const deleteStage = (stageId) => api.delete(`/stages/${stageId}`);
export const updateStage = (stageId, data) => api.patch(`/stages/${stageId}`, data);

export const compareStage = (stageId, tolerance = 0.05) =>
  api.post(`/stages/${stageId}/compare`, null, { params: { tolerance } });

export const cleanPointCloud = (stageId, config) =>
  api.post(`/stages/${stageId}/clouds/clean`, config);

export const uploadPointCloudFile = async (presignedUrl, file, onProgress) => {
  await uploadFileWithPresignedLink(presignedUrl, file, onProgress);
};

/** Upload LAS/LAZ and confirm; returns bounds (does not start Potree). */
export const uploadPointCloud = async (stageId, file, onProgress) => {
  const uploadLinkRes = await getPointCloudUploadLink(stageId, {
    filename: file.name,
    size: file.size,
    content_type: file.type || "application/octet-stream",
  });

  const presignedUrl = uploadLinkRes.data.url;
  const pointCloudFileId = uploadLinkRes.data.file.id;

  await uploadPointCloudFile(presignedUrl, file, onProgress);

  const confirmRes = await confirmBimUpload(pointCloudFileId, {
    filename: file.name,
    size: file.size,
    content_type: file.type || "application/octet-stream",
  });

  const { file: confirmedFile, point_cloud_id: pointCloudId, bounds } = confirmRes.data;

  if (!pointCloudId || !bounds?.min_xyz || !bounds?.max_xyz) {
    throw new Error(
      "Сервер не вернул границы облака точек. Обновите бэкенд или повторите загрузку."
    );
  }

  return {
    file: confirmedFile,
    pointCloudId,
    bounds,
    success: true,
  };
};

/** @deprecated use uploadPointCloud + cleanPointCloud */
export const uploadAndConvertPointCloud = uploadPointCloud;
