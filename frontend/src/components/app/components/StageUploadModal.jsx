import { useState } from "react";
import { FileSelect, Modal, FilledButton, UnfilledButton } from "@ui";
import { useToast } from "@/context";
import { createStage, uploadAndConvertPointCloud } from "@/api/stage";

export const StageUploadModal = ({ projectId, onClose, onSuccess }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState(null);
  const [stage, setStage] = useState(null);
  const { showToast } = useToast();

  const handleUpload = async () => {
    if (!selectedFile) return;

    try {
      setIsLoading(true);
      setError(null);

      let stageId = stage?.id;

      if (!stageId) {
        const stageRes = await createStage(projectId);
        setStage(stageRes.data);
        stageId = stageRes.data.id;
      }

      const result = await uploadAndConvertPointCloud(
        stageId,
        selectedFile,
        (progress) => {
          setUploadProgress(Math.round((progress.loaded / progress.total) * 100));
        }
      );

      showToast({
        type: "primary",
        title: "Успешная загрузка",
        message: "Файл загружен, конверсия файла запущена",
      });

      onSuccess?.(result);
      onClose?.();
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

  return (
    <Modal title="Создание нового этапа" showBackdrop={true}>
      <div>
        <label>Выберите LAS/LAZ файл</label>
        <FileSelect
          value={selectedFile}
          onChange={setSelectedFile}
          extensions={["las", "laz"]}
          placeholder="Выберите файл с облака"
          disabled={isLoading}
        />
      </div>

      <div className="flex justify-end gap-3 mt-5">
        <UnfilledButton onClick={onClose}>Отмена</UnfilledButton>
        <FilledButton onClick={handleUpload} disabled={!selectedFile || isLoading}>
          {isLoading ? "Загрузка..." : "Загрузить"}
        </FilledButton>
      </div>
    </Modal>
  );
};