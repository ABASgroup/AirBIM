import { useState, useEffect } from "react";
import { Modal } from "@ui/Modal";
import { FilledButton } from "@ui/FilledButton";
import { UnfilledButton } from "@ui/UnfilledButton";
import { Input } from "@ui/Input";
import { Select } from "@ui/Select";
import { createPortal } from "react-dom";

export const ProjectModal = ({ isOpen, onClose, onSubmit, mode = "create", project = null }) => {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState("active");
  useEffect(() => {
    if (isOpen) {
      if (mode === "edit" && project) {
        setName(project.name || "");
        setDescription(project.description || "");
        setStatus(project.status || "active");
      } else {
        setName("");
        setDescription("");
      }
    }
  }, [isOpen, mode, project]);
  const handleSubmit = () => {
    if (name.trim()) {
      onSubmit({ name, description, status });
      setName("");
      setDescription("");
    }
  };
  if (!isOpen) return null;
  const title = mode === "edit" ? "Редактировать проект" : "Создать проект";
  const buttonText = mode === "edit" ? "Сохранить" : "Создать";

  return createPortal(
    <Modal title={title} showBackdrop={true}>
      <div>
        <p>Название проекта</p>
        <Input
          placeholder="Название проекта"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
      </div>
      <div>
        <p>Описание проекта</p>
        <Input
          placeholder="Описание проекта"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
      </div>

      {mode === "edit" && (
        <div>
          <p>Статус проекта</p>
          <Select
            value={status}
            onChange={setStatus}
            options={[
              { value: "active", label: "Активный" },
              { value: "archived", label: "Архивный" }
            ]}
          />
        </div>
      )}

      <div className="flex justify-end gap-3 mt-5">
        <UnfilledButton onClick={onClose}>Отмена</UnfilledButton>
        <FilledButton onClick={handleSubmit}>{buttonText}</FilledButton>
      </div>
    </Modal>,
    document.body
  );
};