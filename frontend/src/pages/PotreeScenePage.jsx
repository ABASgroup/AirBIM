import { useEffect, useRef } from "react";

function PotreeScenePage() {
  const renderAreaRef = useRef(null);

  useEffect(() => {
    const renderArea = renderAreaRef.current;

    if (!renderArea || !window.Potree || !window.THREE) {
      console.error("Potree или THREE не загружены в глобальную область видимости!");
      return;
    }

    const viewer = new window.Potree.Viewer(renderArea);

    viewer.setEDLEnabled(false);
    viewer.setFOV(60);
    viewer.setPointBudget(1_000_000);

    viewer.loadGUI(() => {
      viewer.setLanguage("en");
    });

    window.Potree.workerPool = new window.Potree.WorkerPool("/potree/workers", 4);

    const baseUrl = "/pointclouds/Myran/metadata.json";

    window.Potree.loadPointCloud(baseUrl, "BasicHouse", (e) => {
      const scene = viewer.scene;
      const pointcloud = e.pointcloud;
      const material = pointcloud.material;

      material.size = 1.0;
      material.pointSizeType = window.Potree.PointSizeType.FIXED;

      scene.addPointCloud(pointcloud);
      viewer.fitToScreen();
    });

  }, []);

  return (
    <div className="potree_container">
      <div id="potree_render_area" ref={renderAreaRef}/>
      <div id="potree_sidebar_container"></div>
    </div>
  );
}

export default PotreeScenePage;