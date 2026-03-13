// Компонент заполненной цветом кнопки

export const FilledButton = ({ children, color = "purple", className = "", ...props }) => {
  const colorMap = {
    purple: "bg-main-purple text-main-white",
    white: "bg-main-white text-main-purple",
    warning: "bg-warning text-main-white",
  };

  return (
    <button
      className={`
        border-none
        min-w-[100px] px-6 py-3
        rounded-[10px] font-bold 
        transition-all active:scale-95
        cursor-pointer
        ${colorMap[color] || colorMap.purple}
        ${className}
      `}
      {...props}
    >
      {children}
    </button>
  );
};