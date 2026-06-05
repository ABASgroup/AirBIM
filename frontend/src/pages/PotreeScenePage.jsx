import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { getProjectStages, getConvertedPointCloudLinks } from "@/api/stage";
import { getProjectBim } from "@/api/file";

function PotreeScenePage({ projectId }) {
  const params = useParams();
  const actualProjectId = projectId ?? params.projectId;
  const renderAreaRef = useRef(null);
  const viewerRef = useRef(null);
  const [items, setItems] = useState([]);
  const [selectedKey, setSelectedKey] = useState(null);
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState("");

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
    const fetchList = async () => {
      if (!actualProjectId) return;
      setLoading(true);
      try {
        const stagesRes = await getProjectStages(actualProjectId);
        const bimRes = await getProjectBim(actualProjectId).catch(() => null);

        const stageItems = [];
        if (stagesRes?.data) {
          for (const st of stagesRes.data) {
            stageItems.push({
              key: `stage-${st.id}`,
              type: "stage",
              label: `Stage ${new Date(st.created_at).toLocaleString()}`,
              stageId: st.id,
              metadataUrl: null,
            });
          }
        }

        const bimItems = [];
        if (bimRes?.data) {
          const bim = bimRes.data;
          bimItems.push({
            key: `bim-${bim.id}`,
            type: "bim",
            label: "BIM",
            bimId: bim.id,
            pointCloudId: bim.point_cloud_id ?? null,
            metadataUrl: null,
          });
        }

        const all = [...bimItems, ...stageItems];
        setItems(all);
        if (all.length) setSelectedKey(all[0].key);
      } finally {
        setLoading(false);
      }
    };

    fetchList();
  }, [actualProjectId]);

  useEffect(() => {
    const loadSelected = async () => {
      const viewer = viewerRef.current;
      if (!viewer || !selectedKey) return;

      const item = items.find((i) => i.key === selectedKey);
      if (!item) return;

      let loadItem = item;

      setStatusMsg("");
      try {
        viewer.scene.pointclouds.slice().forEach((pc) => viewer.scene.removePointCloud(pc));
      } catch (e) { }

      let metadataUrl = item.metadataUrl ?? null;

      if (!metadataUrl) {
        if (item.type === "stage") {
          try {
            setLoading(true);
            const linksRes = await getConvertedPointCloudLinks(item.stageId);
            const links = linksRes?.data || [];
            metadataUrl = links.find((l) => l.endsWith("metadata.json")) || links[0] || null;
          } catch (err) {
            setStatusMsg("Конвертированные файлы для этапа не найдены.");
            return;
          } finally {
            setLoading(false);
          }

          if (!metadataUrl) {
            setStatusMsg("Конвертированные файлы для этапа не найдены.");
            return;
          }

          setItems((prev) => prev.map((i) => (i.key === item.key ? { ...i, metadataUrl } : i)));
          loadItem = { ...item, metadataUrl };
        } else if (item.type === "bim") {
          const pcId = item.pointCloudId;
          if (!pcId) {
            setStatusMsg("Для BIM конвертация ещё не завершена.");
            return;
          }

          const firstStage = items.find((i) => i.type === "stage");
          if (!firstStage) {
            setStatusMsg("Нет доступных этапов для загрузки BIM.");
            return;
          }

          try {
            setLoading(true);
            const linksRes = await getConvertedPointCloudLinks(firstStage.stageId);
            const links = linksRes?.data || [];
            metadataUrl = links.find((l) => l.endsWith("metadata.json")) || links[0] || null;
          } catch (err) {
            metadataUrl = null;
          } finally {
            setLoading(false);
          }

          if (!metadataUrl) {
            setStatusMsg("Конвертированные файлы для BIM не найдены.");
            return;
          }

          // persist resolved metadataUrl into items
          setItems((prev) => prev.map((i) => (i.key === item.key ? { ...i, metadataUrl } : i)));
          loadItem = { ...item, metadataUrl };
        }
      }

      if (metadataUrl) {
        setStatusMsg("Загрузка сцены...");
        setLoading(true);
        const toLoad = loadItem?.metadataUrl ?? metadataUrl;
        window.Potree.loadPointCloud(toLoad, loadItem.label, (e) => {
          const pointcloud = e.pointcloud;
          const material = pointcloud.material;
          material.size = 1.0;
          material.pointSizeType = window.Potree.PointSizeType.FIXED;
          viewer.scene.addPointCloud(pointcloud);
          viewer.fitToScreen();
          setLoading(false);
          setStatusMsg("");
        });
      }
    };

    loadSelected();
  }, [selectedKey, items]);

  return (
    <div className="potree_container">
      <div className="flex items-start gap-4 mb-2">
        <div>
          <label className="block text-sm text-gray-600">Сцены</label>
          <div className="border px-2 py-1 max-h-48 overflow-auto" style={{ minWidth: 220 }}>
            {items.length === 0 && <div className="text-sm text-gray-500">Этапов нет</div>}
            {items.map((it) => (
              <div
                key={it.key}
                onClick={() => setSelectedKey(it.key)}
                className={`p-2 cursor-pointer ${selectedKey === it.key ? "bg-blue-100" : "hover:bg-gray-100"}`}
              >
                <div className="text-sm font-medium">{it.label}</div>
                <div className="text-xs text-gray-500">
                  {it.type === "stage" ? "Этап" : "BIM"}
                  {it.metadataUrl ? " · Готово" : " · Конвертация: нет"}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="flex-1">
          {loading && <div className="text-sm text-gray-500 mb-2">Загрузка...</div>}
          {statusMsg && <div className="text-sm text-red-600 mb-2">{statusMsg}</div>}
        </div>
      </div>

      <div id="potree_render_area" ref={renderAreaRef} style={{ width: "100%", height: "80vh" }} />
      <div id="potree_sidebar_container" />
    </div>
  );
}

export default PotreeScenePage;