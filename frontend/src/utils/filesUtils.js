export const normalizeExtension = (extension) => {
  if (!extension) {
    return "";
  }

  return extension.startsWith(".") ? extension : `.${extension}`;
};

export const getSelectedFiles = (value) => {
  if (!value) {
    return [];
  }

  if (Array.isArray(value)) {
    return value.filter(Boolean);
  }

  if (value instanceof FileList) {
    return Array.from(value);
  }

  return [value];
};

export const formatFileSize = (sizeInBytes) => {
  if (!Number.isFinite(sizeInBytes) || sizeInBytes <= 0) {
    return "0 B";
  }

  const sizeUnits = ["B", "KB", "MB", "GB"];
  const sizeIndex = Math.min(Math.floor(Math.log(sizeInBytes) / Math.log(1024)), sizeUnits.length - 1);
  const formattedSize = sizeInBytes / (1024 ** sizeIndex);

  return `${formattedSize.toFixed(formattedSize >= 10 || sizeIndex === 0 ? 0 : 1)} ${sizeUnits[sizeIndex]}`;
};

export async function isIFC(file) {
  const buffer = await file.slice(0, 15).arrayBuffer();
  const header = new TextDecoder().decode(buffer);
  return header.startsWith("ISO-10303-21;");
}
