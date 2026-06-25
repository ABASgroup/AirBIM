// Сцена потри для визуализации облаков точек
import { useCallback, useEffect, useRef, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { createPortal } from "react-dom";
import { getProjectStages } from "@/api/stage";
import { getProjectBim } from "@/api/file";
import { getProjectResults } from "@/api/recordingResult";
import { LoadingSpinner } from "@ui";
import { getProject } from "@/api/project";
import { getWorkspace } from "@/api/workspace";
import { useWorkspace } from "@/context/WorkspaceContext";

function createLayerItem({ key, type, label, pointCloudId, stageId, bimId, resultId }) {
  return {
    key,
    type,
    label,
    stageId,
    bimId,
    resultId,
    pointCloudId,
    visible: false,
    loading: false,
    loaded: false,
    error: null,
  };
}

function getLayerTypeLabel(type) {
  switch (type) {
    case "stage":
      return "Этап";
    case "bim":
      return "BIM";
    case "plan_fact":
      return "План/факт";
    case "progress":
      return "Фиксация";
    default:
      return type;
  }
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

function configurePointCloudMaterial(pointcloud) {
  pointcloud.minimumNodePixelSize = 0;

  const material = pointcloud.material;
  material.size = 1;
  material.pointSizeType = window.Potree.PointSizeType.FIXED;
}

function getVisiblePointClouds(viewer) {
  return viewer.scene.pointclouds.filter((pc) => pc.visible);
}

function focusViewerOnVisibleClouds(viewer) {
  const clouds = getVisiblePointClouds(viewer);
  if (clouds.length === 0) return;

  // World-space bbox: each cloud keeps metadata.offset as position so layers stay aligned.
  const box = viewer.getBoundingBox(clouds);
  const size = box.getSize(new window.THREE.Vector3());
  if (size.length() > 0) {
    viewer.setMoveSpeed(size.length() / 5);
  }

  const node = new window.THREE.Object3D();
  node.boundingBox = box;
  viewer.zoomTo(node, 1, 300);
  viewer.controls.stop();
}

function PotreeScenePage({ projectId }) {
  const params = useParams();
  const actualProjectId = projectId ?? params.projectId;
  const renderAreaRef = useRef(null);
  const viewerRef = useRef(null);
  const loadedCloudsRef = useRef(new Map());
  const [items, setItems] = useState([]);
  const itemsRef = useRef(items);
  const [isListLoading, setIsListLoading] = useState(false);
  const [sidebarContainer, setSidebarContainer] = useState(null);
  const [quickButtonsContainer, setQuickButtonsContainer] = useState(null);
  const [project, setProject] = useState(null);
  const [workspace, setWorkspace] = useState(null);
  const { switchWorkspace } = useWorkspace();

  useEffect(() => {
    itemsRef.current = items;
  }, [items]);

  const updateItem = useCallback((key, patch) => {
    setItems((prev) => prev.map((i) => (i.key === key ? { ...i, ...patch } : i)));
  }, []);

  useEffect(() => {
    getProject(actualProjectId)
      .then(res => {
        setProject(res.data);
        return getWorkspace(res.data.workspace_id);
      })
      .then(wsRes => setWorkspace(wsRes.data))
      .catch(() => setWorkspace(null));
  }, [actualProjectId]);

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

        const quickButtons = document.getElementById("potree_quick_buttons");
        if (quickButtons) {
          quickButtons.style.display = "flex";
          quickButtons.style.alignItems = "center";
          quickButtons.style.width = "auto";
          quickButtons.style.height = "auto";
          quickButtons.style.gap = "8px";
          quickButtons.style.zIndex = "10000";

          let breadcrumbsHost = document.getElementById("potree-react-breadcrumbs");
          if (!breadcrumbsHost) {
            breadcrumbsHost = document.createElement("div");
            breadcrumbsHost.id = "potree-react-breadcrumbs";
            breadcrumbsHost.className = "flex-1 min-w-0 overflow-hidden";
            quickButtons.appendChild(breadcrumbsHost);
          }
          setQuickButtonsContainer(breadcrumbsHost);
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
        const [stagesRes, bimRes, resultsRes] = await Promise.all([
          getProjectStages(actualProjectId),
          getProjectBim(actualProjectId).catch(() => null),
          getProjectResults(actualProjectId).catch(() => ({ data: [] })),
        ]);

        const stageItems = [];
        if (stagesRes?.data) {
          for (const st of stagesRes.data) {
            stageItems.push(
              createLayerItem({
                key: `stage-${st.id}`,
                type: "stage",
                label: `${st.name}`,
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

        const resultItems = [];
        for (const result of resultsRes?.data ?? []) {
          if (result.type !== "plan_fact" && result.type !== "progress") continue;
          resultItems.push(
            createLayerItem({
              key: `result-${result.id}`,
              type: result.type,
              label: result.type === "plan_fact" ? `${result.id}` : `${result.id}`,
              resultId: result.id,
              pointCloudId: result.point_cloud_id ?? null,
            })
          );
        }

        setItems([...bimItems, ...stageItems, ...resultItems]);
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

    focusViewerOnVisibleClouds(viewer);
  }, []);

  const toggleVisibility = useCallback(async (key) => {
    const viewer = viewerRef.current;
    if (!viewer) return;

    const targetItem = itemsRef.current.find((i) => i.key === key) ?? null;
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
      focusViewerOnVisibleClouds(viewer);
      updateItem(key, { visible: true });
      return;
    }

    updateItem(key, { loading: true, visible: true, error: null });

    try {
      // TODO : Add file_id param to the metadataUrl for Permission.FILES_VIEW support
      // and update the backend endpoint to use require_file_permission(Permission.FILES_VIEW)
      // > backend/api/routers/file.py:get_point_cloud_file
      const metadataUrl = `/api/files/point_clouds/${targetItem.pointCloudId}/metadata.json`;
      const pointcloud = await loadPointCloudAsync(metadataUrl, targetItem.label);
      configurePointCloudMaterial(pointcloud);
      pointcloud.visible = true;

      viewer.scene.addPointCloud(pointcloud);
      loadedCloudsRef.current.set(key, pointcloud);
      focusViewerOnVisibleClouds(viewer);

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
    if (item.loading) return "Загружается...";
    if (item.error) return item.error;
    if (item.loaded && item.visible) return "На сцене";
    if (item.loaded) return "Скрыто";
    return "Не загружено";
  };

  const breadcrumbs = (
    <nav className="flex flex-wrap items-center gap-1 text-sm potree_info_text whitespace-nowrap">
      {workspace && (
        <>
          <Link
            to="/app/dashboard"
            className="text-text-color hover:underline"
            onClick={() => switchWorkspace(workspace.id)}
          >
            {workspace.name}
          </Link>
          <span>/</span>
        </>
      )}
      <Link
        to={`/app/projects/${actualProjectId}`}
        className="text-text-color hover:underline"
        onClick={() => workspace && switchWorkspace(workspace.id)}
      >
        {project?.name ?? "Проект"}
      </Link>
      <span>/</span>
      <span className="text-primary-color">Сцена</span>
    </nav>
  );

  return (
    <div className="potree_container relative w-full h-screen">
      {isListLoading && (
        <LoadingSpinner variant="overlay" message="Загрузка данных..." />
      )}

      <div id="potree_render_area" ref={renderAreaRef} style={{ width: "100%", height: "100vh" }} />
      <div id="potree_sidebar_container" />

      {quickButtonsContainer && createPortal(breadcrumbs, quickButtonsContainer)}

      {sidebarContainer && createPortal(
        <div className="flex flex-col gap-1 p-1 max-h-[350px] overflow-y-auto custom-scrollbar">
          {items.length === 0 && <div className="text-text-color/50">Облаков нет</div>}
          {items.map((it) => {
            const canToggle = Boolean(it.pointCloudId) && !it.loading;
            const canFocus = it.loaded && !it.loading;

            return (
              <div
                key={it.key}
                role="button"
                tabIndex={canToggle ? 0 : -1}
                title={it.pointCloudId ? "Показать / скрыть" : "Облако ещё не готово"}
                className={`p-2 rounded transition-colors select-none
                  ${it.visible || it.loading ? "bg-primary-color/20" : "text-text-color"}
                  ${canToggle ? "cursor-pointer hover:bg-background-color/50" : "cursor-default"}`}
                onPointerDown={(e) => e.stopPropagation()}
                onClick={(e) => {
                  e.stopPropagation();
                  if (canToggle) toggleVisibility(it.key);
                }}
                onKeyDown={(e) => {
                  if ((e.key === "Enter" || e.key === " ") && canToggle) {
                    e.preventDefault();
                    toggleVisibility(it.key);
                  }
                }}
              >
                <div className="flex items-center gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="font-semibold truncate">{it.label}</div>
                    <div className="text-text-color/50 text-sm">
                      {getLayerTypeLabel(it.type)} · {getItemStatus(it)}
                    </div>
                  </div>
                  <button
                    type="button"
                    disabled={!canFocus}
                    onPointerDown={(e) => e.stopPropagation()}
                    onClick={(e) => {
                      e.stopPropagation();
                      focusCloud(it.key);
                    }}
                    title="Приблизить камеру"
                    className="shrink-0 w-7 h-7 rounded flex items-center justify-center text-sm
                      disabled:opacity-30 disabled:cursor-not-allowed"
                  >
                    <i className="fa fa-video-camera text-text-color cursor-pointer hover:brightness-70 active:scale-95" aria-hidden="true"></i>
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
