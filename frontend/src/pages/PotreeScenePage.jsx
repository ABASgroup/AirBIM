// Сцена потри для визуализации облаков точек
import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { createPortal } from "react-dom";
import { getProjectStages, getConvertedPointCloudLinks } from "@/api/stage";
import { getProjectBim } from "@/api/file";
import { LoadingSpinner } from "@ui";
import { useToast } from "@/context";

function PotreeScenePage({ projectId }) {
  const params = useParams();
  const actualProjectId = projectId ?? params.projectId;
  const renderAreaRef = useRef(null);
  const viewerRef = useRef(null);
  const [items, setItems] = useState([]);
  const [selectedKey, setSelectedKey] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [sidebarContainer, setSidebarContainer] = useState(null);
  const { showToast } = useToast();

  useEffect(() => {
    const initViewer = () => {
      const renderArea = renderAreaRef.current;
      if (!renderArea || !window.Potree || !window.THREE) return;

      const viewer = new window.Potree.Viewer(renderArea);
      viewer.setEDLEnabled(false);
      viewer.setFOV(60);
      viewer.setPointBudget(1_000_000);

      viewer.loadGUI(() => {
        viewer.setLanguage("en");

        const $ = window.$;
        if (!$) return;

        let header = $('<h3 class="accordion-header ui-widget"><span>Облака точек</span></h3>');
        let content = $('<div class="accordion-content ui-widget"><div id="potree-react-layers"></div></div>');

        header.click(() => content.slideToggle());

        const menuAbout = $("#menu_appearance");
        if (menuAbout.length) {
          header.insertBefore(menuAbout);
          content.insertBefore(menuAbout);
        } else {
          $("#menu_appearance").append(header).append(content);
        }

        setSidebarContainer(document.getElementById("potree-react-layers"));
      });

      window.Potree.workerPool = new window.Potree.WorkerPool("/potree/workers", 4);
      viewerRef.current = viewer;
    };

    initViewer();
  }, []);

  useEffect(() => {
    const fetchList = async () => {
      if (!actualProjectId) return;
      setIsLoading(true);
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
        setIsLoading(false);
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
            setIsLoading(true);
            const linksRes = await getConvertedPointCloudLinks(item.stageId);
            const links = linksRes?.data || [];
            metadataUrl = links.find((l) => l.endsWith("metadata.json")) || links[0] || null;
          } catch (err) {
            showToast({
              type: "warning",
              title: "Ошибка",
              message: "Конвертированные файлы для этапа не найдены",
            });
            return;
          } finally {
            setIsLoading(false);
          }

          if (!metadataUrl) {
            showToast({
              type: "warning",
              title: "Ошибка",
              message: "Конвертированные файлы для этапа не найдены",
            });
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
            setIsLoading(true);
            const linksRes = await getConvertedPointCloudLinks(firstStage.stageId);
            const links = linksRes?.data || [];
            metadataUrl = links.find((l) => l.endsWith("metadata.json")) || links[0] || null;
          } catch (err) {
            metadataUrl = null;
          } finally {
            setIsLoading(false);
          }

          if (!metadataUrl) {
            setStatusMsg("Конвертированные файлы для BIM не найдены.");
            return;
          }

          setItems((prev) => prev.map((i) => (i.key === item.key ? { ...i, metadataUrl } : i)));
          loadItem = { ...item, metadataUrl };
        }
      }

      if (metadataUrl) {
        setStatusMsg("Загрузка сцены...");
        setIsLoading(true);
        const toLoad = loadItem?.metadataUrl ?? metadataUrl;
        window.Potree.loadPointCloud(toLoad, loadItem.label, (e) => {
          const pointcloud = e.pointcloud;
          const material = pointcloud.material;
          material.size = 1.0;
          material.pointSizeType = window.Potree.PointSizeType.FIXED;
          viewer.scene.addPointCloud(pointcloud);
          viewer.fitToScreen();
          setIsLoading(false);
          setStatusMsg("");
        });
      }
    };

    loadSelected();
  }, [selectedKey, items]);

  return (
    <div className="potree_container relative w-full h-screen">
      {isLoading && (
          <LoadingSpinner variant="overlay" message="Загрузка данных..." />
      )}

      <div id="potree_render_area" ref={renderAreaRef} style={{ width: "100%", height: "100vh" }} />
      <div id="potree_sidebar_container" />

      {sidebarContainer && createPortal(
        <div className="flex flex-col gap-1 p-1 max-h-[350px] overflow-y-auto custom-scrollbar">
          {items.length === 0 && <div className="text-text-color/50">Этапов нет</div>}
          {items.map((it) => (
            <div
              key={it.key}
              onClick={() => setSelectedKey(it.key)}
              className={`p-2 rounded cursor-pointer transition-colors ${selectedKey === it.key
                ? "bg-primary-color/50 text-white"
                : "text-text-color hover:text-text-color/50"
                }`}
            >
              <div className="font-semibold truncate hover:text-text-color/50">{it.label}</div>
              <div className={"text-text-color/50"}>
                {it.type === "stage" ? "Этап" : "BIM"}
                {it.metadataUrl ? " · Загружено" : " · Ожидает"}
              </div>
            </div>
          ))}
        </div>,
        sidebarContainer
      )}
    </div>
  );
}

export default PotreeScenePage;