const BAR_ANIMATIONS = ["animate-eq-1", "animate-eq-2", "animate-eq-3", "animate-eq-4", "animate-eq-5"];

export default function VoiceOrb({ mode = "idle" }) {
  const active = mode !== "idle";
  const color = mode === "listening" ? "#D9776B" : "#E8A33D";
  const label = mode === "speaking" ? "Speaking" : mode === "listening" ? "Listening" : "Voice ready";
  return (
    <div className="flex items-center gap-3">
      <div
        className="flex items-end gap-[3px] h-5 px-2 py-1 rounded-full border"
        style={{ borderColor: active ? color : "#2B2F3B", backgroundColor: active ? `${color}1A` : "transparent" }}
      >
        {BAR_ANIMATIONS.map((anim, i) => (
          <span
            key={i}
            className={`w-[3px] rounded-full ${active ? anim : ""}`}
            style={{
              height: active ? "100%" : "3px",
              backgroundColor: color,
              opacity: active ? 1 : 0.4,
            }}
          />
        ))}
      </div>
      <span
        className="text-xs font-mono uppercase tracking-wider transition-colors"
        style={{ color: active ? color : "#9A9EAE" }}
      >
        {label}
      </span>
    </div>
  );
}
