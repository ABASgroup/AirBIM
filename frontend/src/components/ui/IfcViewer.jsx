import { useEffect, useRef, useState } from "react";
import { IfcViewerAPI } from "web-ifc-viewer";

export function IfcViewer({ url }) {
  const containerRef = useRef(null);
  const viewerRef = useRef(null);
  const [wasmReady, setWasmReady] = useState(false);

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

  useEffect(() => {
    const loadIfc = async () => {
      if (!viewerRef.current || !url || !wasmReady) return;
      await viewerRef.current.IFC.loadIfcUrl(url, true);
    };

    loadIfc();
  }, [url, wasmReady]);

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
    </div>
  );
}