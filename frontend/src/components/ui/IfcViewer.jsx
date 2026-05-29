import { useEffect, useRef, useState } from "react";
import { IfcViewerAPI } from "web-ifc-viewer";
import { LoadingSpinner } from "@ui";

export function IfcViewer({ url }) {
  const containerRef = useRef(null);
  const viewerRef = useRef(null);
  const [wasmReady, setWasmReady] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [loadError, setLoadError] = useState(null);

  useEffect(() => {
    const loadIfc = async () => {
      if (!viewerRef.current || !url || !wasmReady) return;

      setIsLoading(true);
      setLoadError(null);

      try {
        await viewerRef.current.IFC.loadIfcUrl(url, true);
      } catch (error) {
        setLoadError("Не удалось загрузить BIM модель");
      } finally {
        setIsLoading(false);
      }
    };

    loadIfc();
  }, [url, wasmReady]);

  useEffect(() => {
    if (!containerRef.current) return;

    let isMounted = true;
    const viewer = new IfcViewerAPI({ container: containerRef.current });
    viewerRef.current = viewer;

    const initViewer = async () => {
      await viewer.IFC.setWasmPath("/wasm/");
      if (!isMounted) return;
      setWasmReady(true);
    };

    initViewer();

    return () => {
      isMounted = false;
      if (viewer) viewer.dispose();
    };
  }, []);

  const handleFileChange = async (event) => {
    const file = event.target.files[0];
    if (!file || !viewerRef.current) return;

    const ifcURL = URL.createObjectURL(file);
    try {
      await viewerRef.current.IFC.loadIfcUrl(ifcURL, true);
    } finally {
      URL.revokeObjectURL(ifcURL);
    }
  };

  return (
    <div className="relative w-full h-full overflow-hidden">
      <div
        ref={containerRef}
        className="w-full h-full outline-none"
      />
      {isLoading && <LoadingSpinner message="Загрузка BIM модели..." />}
      {loadError && <div className="error-message">{loadError}</div>}
    </div>
  );
}