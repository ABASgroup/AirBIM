// Окно с визуализацией IFC модели
import { IfcViewer } from "@ui";

export const IfcViewerDrawer = ({ url, isOpen, onClose }) => {
  if (!isOpen) {
    return null;
  }

  return (
    <div
      className="fixed top-15 right-0 bg-background-color flex justify-end
      border-border-color border-t-3"
      style={{height: "calc(100vh - 3.75rem)", width: "calc(100vw - 12.5rem)"}}
    >
      <button onClick={onClose} className="absolute top-4 right-4 z-10 cursor-pointer">
        <i className="fa-solid fa-xmark text-2xl text-text-color"></i>
      </button>

      <div style={{ width: "100%", height: "100%" }} className="border-border-color border-l-3">
        <IfcViewer url={url} />
      </div>
    </div>
  );
};