import { useState } from "react";
import { FileSelect, Modal, FilledButton, UnfilledButton, Input } from "@ui";
import { useToast } from "@/context";
import { createStage, uploadPointCloud } from "@/api/stage";
import { CleanScanModal } from "./CleanScanModal";

export const StageUploadModal = ({ projectId, onClose, onSuccess }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [stage, setStage] = useState(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [cleanStep, setCleanStep] = useState(null);
  const { showToast } = useToast();

  const handleUpload = async (e) => {
    if (e) e.preventDefault();
    if (!selectedFile) return;

    try {
      setIsLoading(true);

      let stageId = stage?.id;

      if (!stageId) {
        const stageRes = await createStage(projectId, { name, description });
        setStage(stageRes.data);
        stageId = stageRes.data.id;
      }

      const result = await uploadPointCloud(
        stageId,
        selectedFile,
        (progress) => {
          setUploadProgress(Math.round((progress.loaded / progress.total) * 100));
        }
      );

      setCleanStep({
        stageId,
        bounds: result.bounds,
        pointCloudId: result.pointCloudId,
      });
    } catch (err) {
      showToast({
        type: "warning",
        title: "Ошибка загрузки",
        err,
      });
    } finally {
      setIsLoading(false);
      setUploadProgress(0);
    }
  };

  const handleCleanSuccess = (task) => {
    showToast({
      type: "primary",
      title: "Очистка запущена",
      message: task?.id
        ? `Файл будет очищен и сконвертирован: ${task.id}`
        : "Очистка и конвертация запущены",
    });
    onSuccess?.(task);
    onClose?.();
  };

  if (cleanStep) {
    return (
      <CleanScanModal
        stageId={cleanStep.stageId}
        bounds={cleanStep.bounds}
        onClose={onClose}
        onSuccess={handleCleanSuccess}
      />
    );
  }

  return (
    <form onSubmit={handleUpload}>
      <Modal title="Создание нового этапа" showBackdrop={true}>
        <div>
          <label>Название этапа</label>
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Cтроительство фундамента"
            required={true}
          />
        </div>

        <div>
          <label>Описание</label>
          <Input
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Краткое описание этапа (необязательно)"
          />
        </div>
        <div>
          <label>Выберите LAS/LAZ файл</label>
          <FileSelect
            value={selectedFile}
            onChange={setSelectedFile}
            extensions={["las", "laz"]}
            placeholder="Выберите файл"
            required={true}
          />
        </div>

        {isLoading && (
          <p className="text-sm text-mute-text-color mt-2">
            Загрузка{uploadProgress ? `: ${uploadProgress}%` : "..."}
          </p>
        )}

        <div className="flex justify-end gap-3 mt-5">
          <UnfilledButton type="button" onClick={onClose} disabled={isLoading}>
            Отмена
          </UnfilledButton>
          <FilledButton type="submit" disabled={isLoading || !selectedFile}>
            {isLoading ? "Загрузка..." : "Загрузить"}
          </FilledButton>
        </div>
      </Modal>
    </form>
  );
};
