import { useEffect, useRef } from "react";
import * as THREE from "three";

export default function Background3D() {
  const containerRef = useRef(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(
      55,
      container.clientWidth / container.clientHeight,
      0.1,
      100
    );
    camera.position.z = 12;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    // Wireframe icosahedra scattered in depth
    const shapes = [];
    const shapeColors = [0xe8a33d, 0x3fa796, 0xd9776b];
    for (let i = 0; i < 7; i++) {
      const geometry = new THREE.IcosahedronGeometry(0.6 + Math.random() * 0.9, 0);
      const material = new THREE.MeshBasicMaterial({
        color: shapeColors[i % shapeColors.length],
        wireframe: true,
        transparent: true,
        opacity: 0.35,
      });
      const mesh = new THREE.Mesh(geometry, material);
      mesh.position.set(
        (Math.random() - 0.5) * 14,
        (Math.random() - 0.5) * 9,
        (Math.random() - 0.5) * 8 - 2
      );
      mesh.userData.spin = {
        x: (Math.random() - 0.5) * 0.004,
        y: (Math.random() - 0.5) * 0.006,
      };
      scene.add(mesh);
      shapes.push(mesh);
    }
    const particleCount = 180;
    const positions = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 20;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 14;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 10 - 3;
    }
    const particleGeometry = new THREE.BufferGeometry();
    particleGeometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    const particleMaterial = new THREE.PointsMaterial({
      color: 0xededef,
      size: 0.035,
      transparent: true,
      opacity: 0.4,
    });
    const particles = new THREE.Points(particleGeometry, particleMaterial);
    scene.add(particles);

    let targetX = 0;
    let targetY = 0;
    function handleMouseMove(e) {
      targetX = (e.clientX / window.innerWidth - 0.5) * 1.2;
      targetY = (e.clientY / window.innerHeight - 0.5) * 0.8;
    }
    window.addEventListener("mousemove", handleMouseMove);

    let frameId;
    function animate() {
      shapes.forEach((mesh) => {
        mesh.rotation.x += mesh.userData.spin.x;
        mesh.rotation.y += mesh.userData.spin.y;
      });
      particles.rotation.y += 0.0004;

      camera.position.x += (targetX - camera.position.x) * 0.02;
      camera.position.y += (-targetY - camera.position.y) * 0.02;
      camera.lookAt(0, 0, 0);

      renderer.render(scene, camera);
      frameId = requestAnimationFrame(animate);
    }
    animate();

    function handleResize() {
      camera.aspect = container.clientWidth / container.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(container.clientWidth, container.clientHeight);
    }
    window.addEventListener("resize", handleResize);

    return () => {
      cancelAnimationFrame(frameId);
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("resize", handleResize);
      shapes.forEach((mesh) => {
        mesh.geometry.dispose();
        mesh.material.dispose();
      });
      particleGeometry.dispose();
      particleMaterial.dispose();
      renderer.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className="fixed inset-0 -z-10 pointer-events-none"
      aria-hidden="true"
    />
  );
}
