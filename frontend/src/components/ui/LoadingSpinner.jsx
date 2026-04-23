// Спиннер для отображения загрузки
export const LoadingSpinner = ({ message = "Загрузка...", variant = "overlay" }) => {
  if (variant === "inline") {
    return (
      <div className="flex items-center justify-center gap-3 py-8">
        <i className="animate-spin fa-solid fa-spinner text-2xl text-primary"></i>
        <p className="text-base text-mute-text-color">{message}</p>
      </div>
    );
  }

  return (
    <div className="absolute inset-0 flex items-center justify-center bg-black/50 z-10">
      <i className="animate-spin fa-solid fa-spinner text-4xl text-primary"></i>
      <p className="text-lg">{message}</p>
    </div>
  );
};