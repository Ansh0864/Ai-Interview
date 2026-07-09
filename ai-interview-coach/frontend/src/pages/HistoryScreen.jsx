import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { fetchHistoryList } from "../api/client.js";
import Background3D from "../components/Background3D.jsx";
export default function HistoryScreen() {
  const [records, setRecords] = useState(null);
  const [error, setError] = useState(null);
  useEffect(() => {
    fetchHistoryList().then(setRecords).catch(setError);
  }, []);
  return (
    <div className="min-h-screen px-6 py-16 flex justify-center screen-enter">
      <Background3D />
      <div className="w-full max-w-2xl">
        <div className="flex items-center justify-between mb-10">
          <div>
            <p className="font-mono text-xs uppercase tracking-[0.2em] text-signal mb-3">
              Interview History
            </p>
            <h1 className="font-display text-4xl">Past interviews</h1>
          </div>
          <Link
            to="/"
            className="text-sm font-mono px-4 py-2 rounded-md border border-line text-muted hover:border-signal hover:text-signal transition"
          >
            + New interview
          </Link>
        </div>
        {error && <p className="text-sm text-flag">{error.message}</p>}
        {records && records.length === 0 && (
          <p className="text-muted">
            No completed interviews yet.{" "}
            <Link to="/" className="text-signal">Start one</Link> and it'll show up here once finished.
          </p>
        )}
        <div className="space-y-3">
          {records?.map((r) => (
            <Link
              key={r.session_id}
              to={`/report/${r.session_id}`}
              className="block bg-panel/70 backdrop-blur-sm border border-line rounded-lg px-5 py-4 hover:border-signal transition"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono text-muted">
                  {new Date(r.completed_at).toLocaleString()}
                </span>
                <span
                  className="text-sm font-semibold"
                  style={{
                    color: r.overall_score >= 7 ? "#3FA796" : r.overall_score >= 4 ? "#E8A33D" : "#D9776B",
                  }}
                >
                  {r.overall_score != null ? `${r.overall_score}/10` : "—"}
                </span>
              </div>
              <p className="text-sm text-ink line-clamp-2">{r.jd_summary || "Interview session"}</p>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
