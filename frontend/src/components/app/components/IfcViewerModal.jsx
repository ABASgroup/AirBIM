// Окно с визуализацией IFC модели
import { Modal, IfcViewer } from "@ui";

export const IfcViewerModal = ({ url, isOpen, onClose, showBackdrop }) => {
  if (!isOpen) {
    return null;
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} showBackdrop>
      <div style={{ width: "80vw", height: "80vh" }}>
        <IfcViewer url={url} />
      </div>
    </Modal>
  );
};