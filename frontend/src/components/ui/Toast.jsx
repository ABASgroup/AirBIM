// Всплывающее справа вверху уведомление
import { useEffect, useState, useRef } from "react";

export const Toast = ({ type = "primary", title, message, onClose, duration = 5000 }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [isFading, setIsFading] = useState(false);
  const onCloseRef = useRef(onClose);

  useEffect(() => {
    onCloseRef.current = onClose;
  }, [onClose]);

  useEffect(() => {
    const appearTimer = setTimeout(() => setIsVisible(true), 10);
    const fadeTimer = setTimeout(() => {
      setIsFading(true);
    }, duration);
    const closeTimer = setTimeout(() => {
      if (onCloseRef.current) onCloseRef.current();
    }, duration + 1000);

    return () => {
      clearTimeout(appearTimer);
      clearTimeout(fadeTimer);
      clearTimeout(closeTimer);
    };
  }, [duration]);

  const colors = {
    warning: {
      border: "border-warning",
      text: "text-warning",
      emoji: "fa-circle-exclamation text-warning"
    },
    primary: {
      border: "border-primary",
      text: "text-primary",
      emoji: "fa-check text-primary"
    }
  };

  const config = colors[type] || colors.primary;

  return (
    <div className={`bg-background-color rounded-[5px] overflow-hidden min-w-[300px] max-w-[400px]
            border-l-5 ${config.border} bg-surface/50 backdrop-blur-md transition-all duration-1000 ease-in-out
            ${isFading ? "opacity-0 translate-x-[120%]" : isVisible ? "opacity-100 translate-x-0" : "opacity-0 translate-x-[120%]"}`}>
      <div className="flex items-start p-3 gap-3">
        <div className="flex-1 pl-1">
          <h4 className={`font-semibold ${config.text} my-3`}>
            <i className={`fa-solid ${config.emoji}`}></i>
            {" "}
            {title}
          </h4>
          <p className="text-sm">{message}</p>
        </div>
        {
          onCloseRef.current && (
            <button onClick={onCloseRef.current}>
              <i className="fa-solid fa-xmark text-text-color cursor-pointer" />
            </button>
          )
        }
      </div >
    </div >
  );
};