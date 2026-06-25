import { useState } from "react";
import { FileSelect, Modal, FilledButton, UnfilledButton, Input } from "@ui";
import { useToast } from "@/context";
import { createStage, uploadAndConvertPointCloud } from "@/api/stage";

export const StageUploadModal = ({ projectId, onClose, onSuccess }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState(null);
  const [stage, setStage] = useState(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const { showToast } = useToast();

  const handleUpload = async (e) => {
    if (e) e.preventDefault();
    if (!selectedFile) return;

    try {
      setIsLoading(true);
      setError(null);

      let stageId = stage?.id;

      if (!stageId) {
        const stageRes = await createStage(projectId, { name, description });
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

        <div className="flex justify-end gap-3 mt-5">
          <UnfilledButton type="button" onClick={onClose}>Отмена</UnfilledButton>
          <FilledButton type="submit">
            Загрузить
          </FilledButton>
        </div>
      </Modal>
    </form>
  );
};