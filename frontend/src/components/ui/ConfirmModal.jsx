// Окно подтверждения действия
import { Modal, FilledButton, UnfilledButton } from "@ui";

export const ConfirmModal = ({
  isOpen, title, message, onConfirm, onCancel, confirmLabel = "Подтвердить", cancelLabel = "Отмена"
}) => {
  if (!isOpen) return null;
  return (
    <Modal title={title} onClose={onCancel} showBackdrop>
      <div>
        <p className="text-center text-text-color">{message}</p>
        <div className="flex justify-center gap-2">
          <UnfilledButton onClick={onCancel}>
            {cancelLabel}
          </UnfilledButton>
          <FilledButton onClick={onConfirm}>
            {confirmLabel}
          </FilledButton>
        </div>
      </div>
    </Modal>
  );
};