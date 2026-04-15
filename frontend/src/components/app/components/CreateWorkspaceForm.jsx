// Окно создания воркспейсов
import { createPortal } from "react-dom";
import { useState } from "react";
import { Modal, FilledButton, UnfilledButton, Input } from "@ui"

export const CreateWorkspaceForm = ({ isOpen, onClose, onCreate }) => {
  const [workspaceName, setWorkspaceName] = useState("");
  const handleSubmit = () => {
    if (workspaceName.trim()) {
      onCreate(workspaceName);
      setWorkspaceName("");
    }
  };

  if (!isOpen) {
    return null;
  }

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <Modal title="Создать новое пространство" showBackdrop>
        <div>
          <label>Название пространства</label>
          <Input
            type="text"
            placeholder="Название пространства"
            value={workspaceName}
            onChange={(e) => setWorkspaceName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                handleSubmit();
              }
            }}
          />
        </div>

        <div className="flex justify-end gap-3 mt-5">
          <UnfilledButton onClick={onClose}>
            Отмена
          </UnfilledButton>
          <FilledButton onClick={handleSubmit}>
            Создать
          </FilledButton>
        </div>
      </Modal>
    </div>,
    document.body
  );
};