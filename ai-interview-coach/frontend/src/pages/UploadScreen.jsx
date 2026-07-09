import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { startSession } from "../api/client.js";
import Background3D from "../components/Background3D.jsx";
import TiltCard from "../components/TiltCard.jsx";
import VoiceOrb from "../components/VoiceOrb.jsx";
import RateLimitNotice from "../components/RateLimitNotice.jsx";
import { getClientId } from "../utils/clientId.js";

export default function UploadScreen() {
  const [resumeFile, setResumeFile] = useState(null);
  const [jdFile, setJdFile] = useState(null);
  const [jdText, setJdText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();
  async function handleSubmit(e) {
    e.preventDefault();
    if (!resumeFile) {
      setError("Add your resume to begin.");
      return;
    }
    if (!jdFile && !jdText.trim()) {
      setError("Add a job description, either as a file or pasted text.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const data = await startSession({ resumeFile, jdFile, jdText, clientId: getClientId() });
      navigate(`/interview/${data.session_id}`, { state: { initial: data } });
    } catch (err) {
      setError(err);
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-6 py-16 screen-enter">
      <Background3D />

      <Link
        to="/history"
        className="fixed top-6 right-6 text-xs font-mono px-3 py-2 rounded-md border border-line bg-panel/70 backdrop-blur-sm text-muted hover:border-signal hover:text-signal transition z-10"
      >
        History
      </Link>

      <div className="w-full max-w-6xl grid md:grid-cols-[1.1fr_1fr] gap-16 items-center">
        <div>
          <div className="flex items-center gap-3 mb-6">
            <p className="font-mono text-sm uppercase tracking-[0.2em] text-signal">
              AI Interview Simulation
            </p>
            <VoiceOrb mode="idle" />
          </div>
          <h1 className="font-display text-5xl md:text-7xl leading-[1.05] mb-6">
            Practice the interview<br />before it counts.
          </h1>
          <p className="text-muted text-lg mb-10 leading-relaxed max-w-lg">
            Upload your resume and the job description. An AI interviewer reads
            both, then runs you through behavioral, HR, and technical rounds —
            asking questions out loud, scoring every answer, and giving real
            feedback as you go.
          </p>

          <div className="flex flex-wrap gap-3">
            <FeaturePill label="Voice interview" />
            <FeaturePill label="Live code editor" />
            <FeaturePill label="Confidence detection" />
            <FeaturePill label="Analytics dashboard" />
          </div>
        </div>

        <TiltCard className="bg-panel/80 backdrop-blur-sm border border-line rounded-xl p-10 shadow-2xl">
          <form onSubmit={handleSubmit} className="space-y-7">
            <div>
              <label className="block text-ink text-base font-medium mb-2">Resume</label>
              <input
                type="file"
                accept=".pdf,.txt"
                onChange={(e) => setResumeFile(e.target.files[0])}
                className="block w-full text-sm text-muted file:mr-4 file:py-3 file:px-5 file:rounded-md file:border-0 file:bg-base file:text-ink file:font-medium hover:file:bg-line cursor-pointer bg-base border border-line rounded-md"
              />
            </div>

            <div>
              <label className="block text-ink text-base font-medium mb-2">Job description</label>
              <input
                type="file"
                accept=".pdf,.txt"
                onChange={(e) => setJdFile(e.target.files[0])}
                className="block w-full text-sm text-muted file:mr-4 file:py-3 file:px-5 file:rounded-md file:border-0 file:bg-base file:text-ink file:font-medium hover:file:bg-line cursor-pointer bg-base border border-line rounded-md mb-3"
              />
              <p className="text-sm text-muted mb-2">or paste it directly</p>
              <textarea
                value={jdText}
                onChange={(e) => setJdText(e.target.value)}
                placeholder="Paste the job description here..."
                rows={5}
                className="w-full bg-base border border-line rounded-md px-4 py-3 text-ink placeholder:text-muted focus:border-signal outline-none resize-none"
              />
            </div>

            <RateLimitNotice error={error} />

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-signal text-[#12141A] font-semibold text-lg py-3.5 rounded-md hover:opacity-90 transition disabled:opacity-50"
            >
              {loading ? "Reading your documents..." : "Start interview"}
            </button>
          </form>
        </TiltCard>
      </div>
    </div>
  );
}

function FeaturePill({ label }) {
  return (
    <span className="text-sm font-mono px-4 py-2 rounded-full border border-line bg-panel/70 backdrop-blur-sm text-muted">
      {label}
    </span>
  );
}