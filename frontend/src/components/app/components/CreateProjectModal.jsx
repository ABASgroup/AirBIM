import { useState } from "react";
import { Modal } from "@ui/Modal";
import { FilledButton } from "@ui/FilledButton";
import { UnfilledButton } from "@ui/UnfilledButton";
import { Input } from "@ui/Input";
import { createPortal } from "react-dom";

export const CreateProjectModal = ({ isOpen, onClose, onCreate, workspaceId }) => {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const handleSubmit = () => {
    if (name.trim()) {
      onCreate({ workspace_id: workspaceId, name, description: description, status: "active" });
      setName("");
      setDescription("");
    }
  };

  if (!isOpen) return null;

  return createPortal(
    <Modal title="Создать проект" showBackdrop={true}>
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

      <div className="flex justify-end gap-3 mt-5">
        <UnfilledButton onClick={onClose}>Отмена</UnfilledButton>
        <FilledButton onClick={handleSubmit}>Создать</FilledButton>
      </div>
    </Modal>,
    document.body
  );
};