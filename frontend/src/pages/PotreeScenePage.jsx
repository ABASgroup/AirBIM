import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls";
import { Potree } from "potree-core";

function PotreeScenePage() {
  const { projectId } = useParams();
  const containerRef = useRef(null);
  const rendererRef = useRef(null);
  const sceneRef = useRef(null);
  const cameraRef = useRef(null);
  const controlsRef = useRef(null);
  const potreeRef = useRef(null);
  const pointCloudsRef = useRef([]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(window.devicePixelRatio || 1);
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setClearColor(0x0b1120, 1);
    renderer.domElement.style.display = "block";
    container.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0b1120);
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(
      60,
      container.clientWidth / container.clientHeight,
      0.1,
      10000
    );
    camera.position.set(0, 0, 20);
    cameraRef.current = camera;

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.minDistance = 0.5;
    controls.maxDistance = 2000;
    controlsRef.current = controls;

    const ambient = new THREE.AmbientLight(0xffffff, 0.7);
    const directional = new THREE.DirectionalLight(0xffffff, 0.8);
    directional.position.set(10, 10, 10);
    scene.add(ambient, directional);

    const potree = new Potree();
    potree.pointBudget = 2_000_000;
    potreeRef.current = potree;

    const frameId = requestAnimationFrame(function animate() {
      controls.update();
      if (pointCloudsRef.current.length > 0) {
        potree.updatePointClouds(pointCloudsRef.current, camera, renderer);
      }
      renderer.render(scene, camera);
      requestAnimationFrame(animate);
    });

    const handleResize = () => {
      if (!container || !camera || !renderer) return;
      const width = container.clientWidth;
      const height = container.clientHeight;
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
    };

    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      cancelAnimationFrame(frameId);
      controls.dispose();
      renderer.dispose();
      if (renderer.domElement.parentNode) {
        renderer.domElement.parentNode.removeChild(renderer.domElement);
      }
      pointCloudsRef.current.forEach((pc) => pc.dispose && pc.dispose());
      scene.clear();
    };
  }, []);

  useEffect(() => {
    if (!potreeRef.current || !sceneRef.current) return;

    const potree = potreeRef.current;
    const scene = sceneRef.current;
    const url = "/BasicHouse.laz";

    potree.loadPointCloud(url, (name, path) => path)
      .then((e) => {
        const pointcloud = e.pointcloud;

        let material = pointcloud.material;
        material.size = 1;
        material.pointSizeType = 0;
        material.shape = 0;

        scene.add(pointcloud);
        pointCloudsRef.current = [pointcloud];

      })
      .catch((err) => {
        console.error("Ошибка загрузки potree:", err);
      });
  }, [projectId]);

  return (
    <div className="flex h-full flex-col">
      <div
        ref={containerRef}
        className="relative h-[600px] overflow-hidden"
      />
    </div>
  );
}

export default PotreeScenePage;
