import { useEffect, useState } from "react";
import { getBimDownloadLink } from "@/api/file";

export const ProjectPreviewThumbnail = ({ hasBim, previewFileId }) => {
  const [imageUrl, setImageUrl] = useState(null);
  const [imageError, setImageError] = useState(false);

  useEffect(() => {
    setImageUrl(null);
    setImageError(false);

    if (!previewFileId) return;

    let cancelled = false;

    getBimDownloadLink(previewFileId)
      .then((res) => {
        if (!cancelled) setImageUrl(res.data.url);
      })
      .catch(() => {
        if (!cancelled) setImageError(true);
      });

    return () => {
      cancelled = true;
    };
  }, [previewFileId]);

  const thumbnailClassName =
    "shrink-0 w-[220px] self-stretch overflow-hidden bg-background-color flex items-center justify-center";

  if (!hasBim) {
    return (
      <div className={thumbnailClassName}>
        <i className="fa-solid fa-building text-2xl text-mute-text-color" />
      </div>
    );
  }

  if (!previewFileId || imageError) {
    return (
      <div className={thumbnailClassName}>
        <i className="animate-spin fa-solid fa-spinner text-2xl text-primary-color" />
      </div>
    );
  }

  if (!imageUrl) {
    return (
      <div className={thumbnailClassName}>
        <i className="animate-spin fa-solid fa-spinner text-2xl text-primary-color" />
      </div>
    );
  }

  return (
    <div className={thumbnailClassName}>
      <img
        src={imageUrl}
        alt="Превью BIM"
        className="h-full w-full object-contain object-center"
        onError={() => setImageError(true)}
      />
    </div>
  );
};
