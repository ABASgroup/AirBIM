import { useId, useMemo, useRef } from "react";
import { formatFileSize, getSelectedFiles, normalizeExtension } from "@utils";

export const FileSelect = ({
  value,
  onChange,
  extensions = [],
  isMultiple = false,
  placeholder = "Выберите файл",
  className = "",
  buttonClassName = "",
  inputClassName = "",
  bgClassName = "bg-background-color",
  disabled = false,
}) => {
  const inputId = useId();
  const inputRef = useRef(null);

  const accept = useMemo(() => {
    const normalizedExtensions = extensions.map(normalizeExtension).filter(Boolean);
    return normalizedExtensions.join(",");
  }, [extensions]);

  const selectedFiles = useMemo(() => getSelectedFiles(value), [value]);

  const displayValue = useMemo(() => {
    if (selectedFiles.length === 0) {
      return placeholder;
    }

    if (isMultiple) {
      if (selectedFiles.length === 1) {
        return `${selectedFiles[0].name} · ${formatFileSize(selectedFiles[0].size)}`;
      }

      return `${selectedFiles[0].name} · ${formatFileSize(selectedFiles[0].size)} + ${selectedFiles.length - 1}`;
    }

    const selectedFile = selectedFiles[0];
    return selectedFile ? `${selectedFile.name} · ${formatFileSize(selectedFile.size)}` : placeholder;
  }, [isMultiple, placeholder, selectedFiles]);

  const handleChange = (event) => {
    const files = Array.from(event.target.files || []);
    if (onChange) {
      onChange(isMultiple ? files : files[0] || null);
    }

    event.target.value = "";
  };

  const handleClick = () => {
    if (!disabled) {
      inputRef.current?.click();
    }
  };

  return (
    <div className={className}>
      <button
        type="button"
        onClick={handleClick}
        disabled={disabled}
        className={`
          w-full rounded-[5px] px-4 py-3 flex items-center justify-between gap-3 border-none text-left transition-all
          ${bgClassName}
          ${disabled ? "cursor-default text-mute-text-color" : "cursor-pointer hover:opacity-90"}
          ${buttonClassName}
        `}
      >
        <span className={`${selectedFiles.length === 0 ? "text-mute-text-color" : "text-text-color"}`}>
          {displayValue}
        </span>

        {isMultiple ? (
          <i className="fa-solid fa-folder-open text-text-color" />
        ) : (
          <i className="fa-solid fa-file-arrow-up text-text-color" />
        )}
      </button>

      {selectedFiles.length > 1 && (
        <div className="mt-2 space-y-1">
          {selectedFiles.map((file) => (
            <div
              key={`${file.name}-${file.lastModified}`}
              className="text-sm text-mute-text-color flex items-center justify-between gap-3"
            >
              <span className="truncate">{file.name}</span>
              <span className="shrink-0">{formatFileSize(file.size)}</span>
            </div>
          ))}
        </div>
      )}

      <input
        id={inputId}
        ref={inputRef}
        type="file"
        className={inputClassName}
        accept={accept || undefined}
        multiple={isMultiple}
        disabled={disabled}
        onChange={handleChange}
        style={{ display: "none" }}
      />
    </div>
  );
};
