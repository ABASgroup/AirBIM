// Сцена потри для визуализации облаков точек
import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { createPortal } from "react-dom";
import { getProjectStages } from "@/api/stage";
import { getProjectBim } from "@/api/file";
import { LoadingSpinner } from "@ui";

function createLayerItem({ key, type, label, pointCloudId, stageId, bimId }) {
  return {
    key,
    type,
    label,
    stageId,
    bimId,
    pointCloudId,
    visible: false,
    loading: false,
    loaded: false,
    error: null,
  };
}

function loadPointCloudAsync(metadataUrl, label) {
  return new Promise((resolve, reject) => {
    window.Potree.loadPointCloud(metadataUrl, label, (e) => {
      if (!e?.pointcloud) {
        reject(new Error("Не удалось загрузить облако точек"));
        return;
      }
      resolve(e.pointcloud);
    });
  });
}

function PotreeScenePage({ projectId }) {
  const params = useParams();
  const actualProjectId = projectId ?? params.projectId;
  const renderAreaRef = useRef(null);
  const viewerRef = useRef(null);
  const loadedCloudsRef = useRef(new Map());
  const [items, setItems] = useState([]);
  const [isListLoading, setIsListLoading] = useState(false);
  const [sidebarContainer, setSidebarContainer] = useState(null);

  const updateItem = useCallback((key, patch) => {
    setItems((prev) => prev.map((i) => (i.key === key ? { ...i, ...patch } : i)));
  }, []);

  useEffect(() => {
    const initViewer = () => {
      const renderArea = renderAreaRef.current;
      if (!renderArea || !window.Potree || !window.THREE) return;

      const viewer = new window.Potree.Viewer(renderArea);
      viewer.setEDLEnabled(false);
      viewer.setFOV(60);
      viewer.setPointBudget(2_000_000);

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
      setIsListLoading(true);
      loadedCloudsRef.current.clear();
      try {
        const stagesRes = await getProjectStages(actualProjectId);
        const bimRes = await getProjectBim(actualProjectId).catch(() => null);

        const stageItems = [];
        if (stagesRes?.data) {
          for (const st of stagesRes.data) {
            stageItems.push(
              createLayerItem({
                key: `stage-${st.id}`,
                type: "stage",
                label: `Stage ${new Date(st.created_at).toLocaleString()}`,
                stageId: st.id,
                pointCloudId: st.point_cloud_id ?? null,
              })
            );
          }
        }

        const bimItems = [];
        if (bimRes?.data) {
          const bim = bimRes.data;
          bimItems.push(
            createLayerItem({
              key: `bim-${bim.id}`,
              type: "bim",
              label: "BIM",
              bimId: bim.id,
              pointCloudId: bim.point_cloud_id ?? null,
            })
          );
        }

        setItems([...bimItems, ...stageItems]);
      } finally {
        setIsListLoading(false);
      }
    };

    fetchList();
  }, [actualProjectId]);

  const focusCloud = useCallback((key) => {
    const viewer = viewerRef.current;
    const pointcloud = loadedCloudsRef.current.get(key);
    if (!viewer || !pointcloud) return;

    const node = new window.THREE.Object3D();
    node.boundingBox = viewer.getBoundingBox([pointcloud]);
    viewer.zoomTo(node, 1, 300);
    viewer.controls.stop();
  }, []);

  const toggleVisibility = useCallback(async (key) => {
    const viewer = viewerRef.current;
    if (!viewer) return;

    let targetItem = null;
    setItems((prev) => {
      targetItem = prev.find((i) => i.key === key) ?? null;
      return prev;
    });
    if (!targetItem) return;

    if (!targetItem.pointCloudId) return;
    if (targetItem.loading) return;

    if (targetItem.visible) {
      const pointcloud = loadedCloudsRef.current.get(key);
      if (pointcloud) pointcloud.visible = false;
      updateItem(key, { visible: false });
      return;
    }

    const existing = loadedCloudsRef.current.get(key);
    if (existing) {
      existing.visible = true;
      updateItem(key, { visible: true });
      return;
    }

    updateItem(key, { loading: true, error: null });

    try {
      const metadataUrl = `/api/files/point_clouds/${targetItem.pointCloudId}/metadata.json`;
      const pointcloud = await loadPointCloudAsync(metadataUrl, targetItem.label);

      const material = pointcloud.material;
      material.size = 1.0;
      material.pointSizeType = window.Potree.PointSizeType.FIXED;
      pointcloud.visible = true;

      viewer.scene.addPointCloud(pointcloud);
      loadedCloudsRef.current.set(key, pointcloud);

      updateItem(key, { loading: false, loaded: true, visible: true });
    } catch {
      updateItem(key, {
        loading: false,
        visible: false,
        error: "Ошибка загрузки",
      });
    }
  }, [updateItem]);

  const getItemStatus = (item) => {
    if (!item.pointCloudId) return "Конвертация не завершена";
    if (item.loading) return <LoadingSpinner variant="overlay" message="Загрузка данных..." />;
    if (item.error) return item.error;
    if (item.loaded && item.visible) return "На сцене";
    if (item.loaded) return "Скрыто";
    return "Выключено";
  };

  return (
    <div className="potree_container relative w-full h-screen">
      {isListLoading && (
        <LoadingSpinner variant="overlay" message="Загрузка данных..." />
      )}

      <div id="potree_render_area" ref={renderAreaRef} style={{ width: "100%", height: "100vh" }} />
      <div id="potree_sidebar_container" />

      {sidebarContainer && createPortal(
        <div className="flex flex-col gap-1 p-1 max-h-[350px] overflow-y-auto custom-scrollbar">
          {items.length === 0 && <div className="text-text-color/50">Этапов нет</div>}
          {items.map((it) => {
            const canToggle = Boolean(it.pointCloudId) && !it.loading;
            const canFocus = it.loaded && !it.loading;

            return (
              <div
                key={it.key}
                className={`p-2 rounded transition-colors ${
                  it.visible ? "bg-primary-color/20" : "text-text-color"
                }`}
              >
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={it.visible}
                    disabled={!canToggle}
                    onChange={() => toggleVisibility(it.key)}
                    className="shrink-0 cursor-pointer disabled:cursor-not-allowed"
                    title={it.pointCloudId ? "Показать / скрыть" : "Облако ещё не готово"}
                  />
                  <div className="flex-1 min-w-0">
                    <div className="font-semibold truncate">{it.label}</div>
                    <div className="text-text-color/50 text-sm">
                      {it.type === "stage" ? "Этап" : "BIM"} · {getItemStatus(it)}
                    </div>
                  </div>
                  <button
                    type="button"
                    disabled={!canFocus}
                    onClick={() => focusCloud(it.key)}
                    title="Приблизить камеру"
                    className="shrink-0 w-7 h-7 rounded flex items-center justify-center text-sm
                      disabled:opacity-30 disabled:cursor-not-allowed
                      hover:bg-primary-color/30 cursor-pointer transition-colors"
                  >
                    ⊙
                  </button>
                </div>
              </div>
            );
          })}
        </div>,
        sidebarContainer
      )}
    </div>
  );
}

export default PotreeScenePage;
