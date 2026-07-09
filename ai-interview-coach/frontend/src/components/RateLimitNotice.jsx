import { useState, useEffect } from "react";

export default function RateLimitNotice({ error }) {
  const normalized = typeof error === "string" ? { message: error, retryAfterSeconds: null } : error;
  const [remaining, setRemaining] = useState(normalized?.retryAfterSeconds ?? null);

  useEffect(() => {
    setRemaining(normalized?.retryAfterSeconds ?? null);
  }, [error]);

  useEffect(() => {
    if (remaining == null || remaining <= 0) return;
    const id = setInterval(() => setRemaining((r) => Math.max(0, r - 1)), 1000);
    return () => clearInterval(id);
  }, [remaining]);

  if (!normalized) return null;

  return (
    <div className="text-sm text-flag space-y-1">
      <p>{normalized.message}</p>
      {remaining != null && remaining > 0 && (
        <p className="font-mono text-xs">
          Try again in <span className="font-semibold">{Math.ceil(remaining)}s</span>
        </p>
      )}
    </div>
  );
}
