import { useEffect, useRef, useState } from "react";
import { getProjectStages, getConvertedPointCloudLinks } from "@/api/stage";
import { getProjectBim } from "@/api/file";

function PotreeScenePage({ projectId }) {
  const renderAreaRef = useRef(null);
  const viewerRef = useRef(null);
  const [scenes, setScenes] = useState([]); // { key, label, metadataUrl }
  const [selectedKey, setSelectedKey] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const initViewer = () => {
      const renderArea = renderAreaRef.current;
      if (!renderArea || !window.Potree || !window.THREE) return;

      const viewer = new window.Potree.Viewer(renderArea);
      viewer.setEDLEnabled(false);
      viewer.setFOV(60);
      viewer.setPointBudget(1_000_000);
      viewer.loadGUI(() => viewer.setLanguage("en"));
      window.Potree.workerPool = new window.Potree.WorkerPool("/potree/workers", 4);
      viewerRef.current = viewer;
    };

    initViewer();
  }, []);

  useEffect(() => {
    // load list of stages + BIM and resolve converted metadata urls
    const fetchScenes = async () => {
      if (!projectId) return;
      setLoading(true);
      try {
        const [stagesRes, bimRes] = await Promise.allSettled([
          getProjectStages(projectId),
          getProjectBim(projectId),
        ]);

        const stageItems = [];
        if (stagesRes.status === "fulfilled") {
          const stages = stagesRes.value.data || [];
          for (const st of stages) {
            // try to find point cloud id on stage object (lenient)
            const pcId =
              st.point_cloud?.id ||
              st.point_cloud?.file?.id ||
              st.point_cloud_id ||
              st.pointcloud_id ||
              null;

            if (!pcId) continue;

            try {
              const linksRes = await getConvertedPointCloudLinks(st.id, pcId);
              const links = linksRes.data || [];
              // prefer metadata.json
              const metadata = links.find((l) => l.endsWith("metadata.json")) || links[0];
              if (metadata) {
                stageItems.push({
                  key: `stage-${st.id}`,
                  label: `Stage ${new Date(st.created_at).toLocaleString()}`,
                  metadataUrl: metadata,
                });
              }
            } catch (err) {
              // ignore missing converted files for this stage
              continue;
            }
          }
        }

        const bimItems = [];
        if (bimRes.status === "fulfilled" && bimRes.value.data) {
          const bim = bimRes.value.data;
          const bimPointCloudId = bim.point_cloud_id || bim.point_cloud?.id || null;
          // to call the stage-scoped converted endpoint we need a stage id; reuse first stage id if available
          const fallbackStageId = (stagesRes.status === "fulfilled" && stagesRes.value.data[0]?.id) || null;
          if (bimPointCloudId && fallbackStageId) {
            try {
              const linksRes = await getConvertedPointCloudLinks(fallbackStageId, bimPointCloudId);
              const links = linksRes.data || [];
              const metadata = links.find((l) => l.endsWith("metadata.json")) || links[0];
              if (metadata) {
                bimItems.push({
                  key: `bim-${bim.id}`,
                  label: `BIM`,
                  metadataUrl: metadata,
                });
              }
            } catch (err) {
              // ignore
            }
          }
        }

        const all = [...bimItems, ...stageItems];
        setScenes(all);
        if (all.length) setSelectedKey(all[0].key);
      } finally {
        setLoading(false);
      }
    };

    fetchScenes();
  }, [projectId]);

  useEffect(() => {
    // load selected scene into potree
    const loadSelected = async () => {
      const viewer = viewerRef.current;
      if (!viewer || !selectedKey) return;
      const sceneItem = scenes.find((s) => s.key === selectedKey);
      if (!sceneItem || !sceneItem.metadataUrl) return;

      // remove previously added pointclouds
      try {
        viewer.scene.pointclouds.slice().forEach((pc) => {
          viewer.scene.removePointCloud(pc);
        });
      } catch (e) {
        // ignore
      }

      // Potree.loadPointCloud accepts absolute URLs too
      setLoading(true);
      window.Potree.loadPointCloud(sceneItem.metadataUrl, sceneItem.label, (e) => {
        const pointcloud = e.pointcloud;
        const material = pointcloud.material;
        material.size = 1.0;
        material.pointSizeType = window.Potree.PointSizeType.FIXED;
        viewer.scene.addPointCloud(pointcloud);
        viewer.fitToScreen();
        setLoading(false);
      });
    };

    loadSelected();
  }, [selectedKey, scenes]);

  return (
    <div className="potree_container">
      <div className="flex items-start gap-4 mb-2">
        <div>
          <label className="block text-sm text-gray-600">Сцена</label>
          <select
            className="border px-2 py-1"
            value={selectedKey || ""}
            onChange={(e) => setSelectedKey(e.target.value)}
          >
            {scenes.length === 0 && <option value="">Нет доступных сцен</option>}
            {scenes.map((s) => (
              <option key={s.key} value={s.key}>
                {s.label}
              </option>
            ))}
          </select>
        </div>

        {loading && <div className="text-sm text-gray-500 mt-5">Загрузка...</div>}
      </div>

      <div id="potree_render_area" ref={renderAreaRef} style={{ width: "100%", height: "80vh" }} />
      <div id="potree_sidebar_container" />
    </div>
  );
}

export default PotreeScenePage;