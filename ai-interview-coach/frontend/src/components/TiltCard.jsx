import { useRef, useState } from "react";

export default function TiltCard({ children, className = "", maxTilt = 6 }) {
  const ref = useRef(null);
  const [transform, setTransform] = useState("rotateX(0deg) rotateY(0deg)");

  function handleMouseMove(e) {
    const el = ref.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5;
    const y = (e.clientY - rect.top) / rect.height - 0.5;
    setTransform(`rotateX(${(-y * maxTilt).toFixed(2)}deg) rotateY(${(x * maxTilt).toFixed(2)}deg)`);
  }

  function handleMouseLeave() {
    setTransform("rotateX(0deg) rotateY(0deg)");
  }
  return (
    <div style={{ perspective: "1200px" }}>
      <div
        ref={ref}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        style={{ transform, transition: "transform 0.15s ease-out", transformStyle: "preserve-3d" }}
        className={className}
      >
        {children}
      </div>
    </div>
  );
}
