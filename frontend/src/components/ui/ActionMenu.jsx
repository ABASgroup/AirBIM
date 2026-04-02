// Компонент меню действий
import React, { useRef, useEffect } from "react";

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
    const menuHeight = 80;

    const spaceBelow = window.innerHeight - rect.bottom;
    const spaceAbove = rect.top;

    if (spaceBelow < menuHeight && spaceAbove > spaceBelow) {
      return {
        top: rect.top - menuHeight - 8,
        right: window.innerWidth - rect.right,
      };
    }

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
      className="fixed z-50 min-w-40 bg-surface rounded-[5px] border-primary-color border-2"
      style={{ top: pos.top, right: pos.right }}
    >
      <div className="flex flex-col">
        {React.Children.map(children, (child) =>
          React.cloneElement(child, {
            className: `${child.props.className || ""} w-full px-4 py-2 text-left hover:bg-mute-text-color flex items-center gap-2`
          })
        )}
      </div>
    </div>
  );
};