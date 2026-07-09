import { useState, useEffect } from "react";
import { useLocation, useParams, Link } from "react-router-dom";
import PerformanceCharts from "../components/PerformanceCharts.jsx";
import Background3D from "../components/Background3D.jsx";
import { fetchHistoryRecord } from "../api/client.js";
import { buildTranscriptMarkdown, downloadTextFile } from "../utils/transcript.js";
export default function ReportScreen() {
  const location = useLocation();
  const { sessionId } = useParams();
  const [tab, setTab] = useState("overview");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [report, setReport] = useState(location.state?.report || null);
  const [qaLog, setQaLog] = useState(location.state?.qaLog || []);
  const [meta, setMeta] = useState({
    resumeSummary: location.state?.resumeSummary || "",
    jdSummary: location.state?.jdSummary || "",
    completedAt: location.state?.completedAt || null,
  });
  useEffect(() => {
    if (report || !sessionId) return;
    setLoading(true);
    fetchHistoryRecord(sessionId)
      .then((record) => {
        setReport(record.final_report);
        setQaLog(record.qa_log || []);
        setMeta({
          resumeSummary: record.resume_summary,
          jdSummary: record.jd_summary,
          completedAt: record.completed_at,
        });
      })
      .catch((err) => setError(err))
      .finally(() => setLoading(false));
  }, [sessionId, report]);

  function handleDownload() {
    const markdown = buildTranscriptMarkdown({ qaLog, report, ...meta });
    downloadTextFile(`interview-transcript-${sessionId || "session"}.md`, markdown);
  }
  if (loading) {
    return <div className="min-h-screen flex items-center justify-center text-muted">Loading interview...</div>;
  }
  if (error || !report) {
    return (
      <div className="min-h-screen flex items-center justify-center text-muted">
        {error ? error.message : "No report available."} <Link to="/" className="text-signal ml-2">Start a new interview</Link>
      </div>
    );
  }
  return (
    <div className="min-h-screen px-6 py-16 flex justify-center screen-enter">
      <Background3D />
      <div className="w-full max-w-2xl">
        <div className="flex items-center justify-between mb-3">
          <p className="font-mono text-xs uppercase tracking-[0.2em] text-signal">
            Interview Complete
          </p>
          <Link to="/history" className="text-xs font-mono text-muted hover:text-signal transition">
            View history →
          </Link>
        </div>
        <div className="flex items-baseline gap-4 mb-8">
          <h1 className="font-display text-5xl">{report.overall_score}/10</h1>
          <span className="text-muted">overall impression</span>
        </div>

        <div className="flex items-center justify-between mb-10 border-b border-line">
          <div className="flex gap-1">
            <TabButton active={tab === "overview"} onClick={() => setTab("overview")}>
              Overview
            </TabButton>
            <TabButton active={tab === "analytics"} onClick={() => setTab("analytics")}>
              Analytics Dashboard
            </TabButton>
          </div>
          <button
            onClick={handleDownload}
            className="text-xs font-mono px-3 py-2 mb-1 rounded-md border border-line text-muted hover:border-signal hover:text-signal transition"
          >
            ↓ Download transcript
          </button>
        </div>
        {tab === "overview" ? (
          <>
            <Section title="Strengths">
              <ul className="space-y-2">
                {report.strengths?.map((s, i) => (
                  <li key={i} className="text-sm text-ink leading-relaxed pl-4 border-l-2 border-pass">{s}</li>
                ))}
              </ul>
            </Section>
            <Section title="Areas to improve">
              <ul className="space-y-2">
                {report.areas_to_improve?.map((s, i) => (
                  <li key={i} className="text-sm text-ink leading-relaxed pl-4 border-l-2 border-flag">{s}</li>
                ))}
              </ul>
            </Section>
            <Section title="Round breakdown">
              <div className="space-y-3">
                {Object.entries(report.round_breakdown || {}).map(([round, text]) => (
                  <div key={round}>
                    <p className="text-xs font-mono uppercase tracking-wider text-signal mb-1">{round}</p>
                    <p className="text-sm text-muted leading-relaxed">{text}</p>
                  </div>
                ))}
              </div>
            </Section>
            <Section title="Communication & confidence">
              <p className="text-sm text-muted leading-relaxed">{report.confidence_assessment}</p>
            </Section>
            <Section title="Verdict">
              <p className="text-sm text-ink leading-relaxed">{report.final_verdict}</p>
            </Section>
          </>
        ) : (
          <Section title="Performance graphs">
            <PerformanceCharts qaLog={qaLog} />
          </Section>
        )}
        <Link
          to="/"
          className="inline-block mt-6 bg-panel border border-line px-6 py-2.5 rounded-md text-sm font-medium hover:border-signal transition"
        >
          Practice again
        </Link>
      </div>
    </div>
  );
}
function TabButton({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-2.5 text-sm font-medium transition border-b-2 -mb-px ${
        active ? "border-signal text-signal" : "border-transparent text-muted hover:text-ink"
      }`}
    >
      {children}
    </button>
  );
}
function Section({ title, children }) {
  return (
    <div className="mb-8 pb-8 border-b border-line last:border-0">
      <h2 className="font-display text-lg mb-4">{title}</h2>
      {children}
    </div>
  );
}
