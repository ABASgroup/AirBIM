import { useRef, useEffect } from "react";

export const ActionMenu = ({ isOpen, onClose, buttonRef, children }) => {
  const menuRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target) &&
        buttonRef.current && !buttonRef.current.contains(event.target)) {
        onClose();
      }
    };
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isOpen, onClose, buttonRef]);

  if (!isOpen) return null;

  const getPosition = () => {
    if (!buttonRef.current) return {};
    const rect = buttonRef.current.getBoundingClientRect();
    return {
      top: rect.bottom + 8,
      right: window.innerWidth - rect.right,
    };
  };

  const pos = getPosition();

  return (
    <div
      ref={menuRef}
      onClick={(e) => e.stopPropagation()}
      className="fixed z-50 min-w-40 bg-surface rounded-[5px] border-primary-color border-2 py-2"
      style={{ top: pos.top, right: pos.right }}
    >
      {children}
    </div>
  );
};