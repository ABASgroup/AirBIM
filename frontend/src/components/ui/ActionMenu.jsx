// Компонент меню действий
import React, { useRef, useEffect } from "react";
import { createPortal } from "react-dom";
import { useFloating, offset, flip, shift, autoUpdate, } from "@floating-ui/react-dom";

export const ActionMenu = ({ isOpen, onClose, buttonRef, children }) => {
  const { x, y, strategy, refs } = useFloating({
    open: isOpen,
    onOpenChange: onClose,
    placement: "right-start",
    whileElementsMounted: autoUpdate,
    middleware: [
      offset(10),
      flip({
        fallbackPlacements: ["left-start", "bottom-end", "top-end"],
      }),
      shift({ padding: 5 }),
    ],
  });

  useEffect(() => {
    if (buttonRef.current) {
      refs.setReference(buttonRef.current);
    }
  }, [buttonRef, refs]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (refs.floating.current && !refs.floating.current.contains(event.target) &&
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

  const menu = (
    <div
      ref={refs.setFloating}
      onMouseDown={(e) => e.stopPropagation()}
      onClick={(e) => e.stopPropagation()}
      className="fixed z-70 min-w-30 bg-surface/70 backdrop-blur-md border-2 border-text-color/20
      rounded-[5px] shadow-bottom py-1 px-1"
      style={{ position: strategy, top: y ?? 0, left: x ?? 0, width: "max-content" }}
    >
      <div className="flex flex-col [&_i]:text-text-color">
        {React.Children.map(children, (child) => {
          if (!React.isValidElement(child)) return child;
          
          return React.cloneElement(child, {
            className: `${child.props.className || ""} 
            w-full py-1 text-left hover:bg-black/30 flex items-center gap-2 rounded-[5px]`,
            onClick: (e) => {
              child.props.onClick?.(e);
              onClose();
            }
          })
        })}
      </div>
    </div>
  );

  return createPortal(menu, document.body);
};