import { createPortal } from "react-dom";
import { useState } from "react";
import { Modal } from "@ui/Modal"
import { FilledButton } from "@ui/FilledButton"
import { UnfilledButton } from "@ui/UnfilledButton"
import { Input } from "@ui/Input"

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
          <p>Название пространства</p>
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

        <div className="flex justify-end gap-3 mt-4">
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