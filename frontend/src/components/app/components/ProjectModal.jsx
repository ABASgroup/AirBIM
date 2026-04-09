// Модальное окно для создания и редактирования проектов
import { useState } from "react";
import { Modal, FilledButton, UnfilledButton, Input, Select, FileSelect } from "@ui";
import { createPortal } from "react-dom";

export const ProjectModal = ({ isOpen, onClose, onSubmit, mode = "create", project = null }) => {
  const modalKey = `${mode}-${project?.id || project?.name || "new"}`;

  if (!isOpen) return null;

  return createPortal(
    <ProjectModalContent
      key={modalKey}
      isOpen={isOpen}
      onClose={onClose}
      onSubmit={onSubmit}
      mode={mode}
      project={project}
    />,
    document.body
  );
};

const ProjectModalContent = ({ onClose, onSubmit, mode, project }) => {
  const initialName = mode === "edit" ? project?.name || "" : "";
  const initialDescription = mode === "edit" ? project?.description || "" : "";
  const initialStatus = mode === "edit" ? project?.status || "active" : "active";
  const initialFile = mode === "edit" ? project?.file || null : null;

  const [formState, setFormState] = useState(() => ({
    name: initialName,
    description: initialDescription,
    status: initialStatus,
    projectFile: initialFile,
  }));

  const setName = (value) => setFormState((current) => ({ ...current, name: value }));
  const setDescription = (value) => setFormState((current) => ({ ...current, description: value }));
  const setStatus = (value) => setFormState((current) => ({ ...current, status: value }));
  const setProjectFile = (value) => setFormState((current) => ({ ...current, projectFile: value }));

  const handleSubmit = () => {
    if (formState.name.trim()) {
      onSubmit({
        name: formState.name,
        description: formState.description,
        status: formState.status,
        file: formState.projectFile,
      });
      setFormState({
        name: "",
        description: "",
        status: "active",
        projectFile: null,
      });
    }
  };

  const title = mode === "edit" ? "Редактировать проект" : "Создать проект";
  const buttonText = mode === "edit" ? "Сохранить" : "Создать";

  return (
    <Modal title={title} showBackdrop={true}>
      <div>
        <p>Название проекта</p>
        <Input
          placeholder="Название проекта"
          value={formState.name}
          onChange={(e) => setName(e.target.value)}
        />
      </div>
      <div>
        <p>Описание проекта</p>
        <Input
          placeholder="Описание проекта"
          value={formState.description}
          onChange={(e) => setDescription(e.target.value)}
        />
      </div>


      {mode === "edit" && (
        <div>
          <p>Статус проекта</p>
          <Select
            value={formState.status}
            onChange={setStatus}
            options={[
              { value: "active", label: "Активный" },
              { value: "archived", label: "Архивный" },
            ]}
          />
        </div>
      ) || (
          <div>
            <p>Файл плана (BIM)</p>
            <FileSelect
              value={formState.projectFile}
              onChange={setProjectFile}
              placeholder="Выберите файл"
              extensions={[".ifc"]}
              isMultiple={false}
            />
          </div>
        )}

      <div className="flex justify-end gap-3 mt-5">
        <UnfilledButton onClick={onClose}>Отмена</UnfilledButton>
        <FilledButton onClick={handleSubmit}>{buttonText}</FilledButton>
      </div>
    </Modal>
  );
};