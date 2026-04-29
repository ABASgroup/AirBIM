// Компонент меню действий
import React, { useRef, useEffect } from "react";
import { createPortal } from "react-dom";

export const ActionMenu = ({ isOpen, onClose, buttonRef, children }) => {
  const menuRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target) &&
        buttonRef.current && !buttonRef.current.contains(event.target)
      ) {
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

  const menu = (
    <div
      ref={menuRef}
      onMouseDown={(e) => e.stopPropagation()}
      onClick={(e) => e.stopPropagation()}
      className="fixed z-70 min-w-30 bg-surface/70 backdrop-blur-md border-2 border-text-color/20
      rounded-[5px] shadow-bottom py-1 px-1"
      style={{ top: pos.top, right: pos.right }}
    >
      <div className="flex flex-col [&_i]:text-text-color">
        {React.Children.map(children, (child) =>
          React.cloneElement(child, {
            className: `${child.props.className || ""} 
            w-full py-1 text-left hover:bg-black/30 flex items-center gap-2 rounded-[5px]`
          })
        )}
      </div>
    </div>
  );

  return createPortal(menu, document.body);
};