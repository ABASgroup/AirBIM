// Компонент заполненной цветом кнопки
export const FilledButton = ({ children, color = "purple", className = "", ...props }) => {
  const colorMap = {
    purple: "bg-primary-color text-text-color",
    white: "bg-text-color text-primary-color",
    warning: "bg-warning text-text-color",
  };

  return (
    <button
      className={`
        border-none
        min-w-[100px] px-3 py-2
        rounded-[10px]
        transition-all active:scale-95
        cursor-pointer
        flex items-center justify-center
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