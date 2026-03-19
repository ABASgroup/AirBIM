// Компонент кнопки с контуром

export const UnfilledButton = ({ children, color = "purple", className = "", ...props }) => {
  const colorMap = {
    purple: "border-primary-color text-primary-color bg-transparent",
    white: "border-text-color text-text-color",
    warning: "border-warning text-warning",
  };

  return (
    <button
      className={`
        min-w-[100px] px-6 py-3
        border-2 rounded-[10px] font-bold
        transition-all active:scale-95
        cursor-pointer
        items-center justify-center
        gap-2
        ${colorMap[color] || colorMap.purple}
        ${className}
      `}
      {...props}
    >
      {children}
    </button>
  );
};