// Общий компонент модальных окон 
export const Modal = ({ children, title, showBackdrop, onClose }) => {
  return (
    <div className="fixed inset-0 z-60 flex items-center justify-center p-5 pointer-events-none">
      {showBackdrop && <div className="absolute inset-0 bg-black/30" />}
      <div className="relative min-w-xl bg-surface/70 backdrop-blur-xl rounded-[5px] 
      border-text-color/20 border-2 p-10 shadow-bottom pointer-events-auto
      [&_p]:text-lg [&_p]:m-2 
      [&_label]:text-xs [&_label]:font-bold [&_label]:text-mute-text-color 
      [&_label]:uppercase [&_label]:tracking-widest [&_label]:block [&_label]:mb-2">
        {onClose && (
          <button onClick={onClose} className="absolute top-2 right-2 text-xl">
            <i className="fa-solid fa-xmark text-text-color cursor-pointer hover:brightness-70 active:scale-95"></i>
          </button>
        )}
        {title && <h2 className="text-3xl font-bold text-text-color mb-5 text-center">{title}</h2>}

        <div className="flex flex-col gap-2">{children}</div>
      </div>
    </div>
  );
};