import { useState, useEffect, useRef } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { submitAnswer, submitAnswerAudio, fetchQuestionAudio } from "../api/client.js";
import RoundProgress from "../components/RoundProgress.jsx";
import VoiceRecorder from "../components/VoiceRecorder.jsx";
import RateLimitNotice from "../components/RateLimitNotice.jsx";
import VoiceOrb from "../components/VoiceOrb.jsx";
import CodeEditor from "../components/CodeEditor.jsx";
import Background3D from "../components/Background3D.jsx";

export default function InterviewScreen() {
  const { sessionId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const [state, setState] = useState(location.state?.initial || null);
  const [answer, setAnswer] = useState("");
  const [code, setCode] = useState("");
  const [codeLanguage, setCodeLanguage] = useState("python");
  const [submitting, setSubmitting] = useState(false);
  const [lastResult, setLastResult] = useState(null);
  const [error, setError] = useState(null);
  const [voiceMode, setVoiceMode] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [needsTapToPlay, setNeedsTapToPlay] = useState(false);
  const [ttsIssue, setTtsIssue] = useState(null); 
  const audioRef = useRef(null);
  const isCodingRound = state?.current_round === "coding";
  function speakWithBrowserVoice(text) {
    if (!("speechSynthesis" in window) || !text) return;
    window.speechSynthesis.cancel(); 
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1;
    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    window.speechSynthesis.speak(utterance);
  }
  useEffect(() => {
    let cancelled = false;
    setNeedsTapToPlay(false);
    setAudioUrl(null);
    if (state?.current_question) {
      fetchQuestionAudio(state.current_question).then(({ url, reason, message }) => {
        if (cancelled) return;
        if (url) {
          setAudioUrl(url);
          setTtsIssue(null);
        } else {
          setTtsIssue({ reason, message });
          speakWithBrowserVoice(state.current_question);
        }
      });
    }
    return () => { cancelled = true; };
  }, [state?.current_question]);

  useEffect(() => {
    if (audioUrl && audioRef.current) {
      audioRef.current.play().catch(() => {
        setNeedsTapToPlay(true);
      });
    }
  }, [audioUrl]);

  function playQuestionAudio() {
    audioRef.current?.play().then(() => setNeedsTapToPlay(false)).catch(() => {});
  }
  useEffect(() => {
    if (isCodingRound) setCode("");
  }, [state?.current_question, isCodingRound]);
  if (!state) {
    return (
      <div className="min-h-screen flex items-center justify-center text-muted">
        No active session found. Go back and start a new interview.
      </div>
    );
  }
  async function processResult(data) {
    setLastResult({
      score: data.last_score,
      feedback: data.last_feedback,
      confidenceFlags: data.last_confidence_flags || [],
    });
    setAnswer("");
    setState(data);
    if (data.finished) {
      navigate(`/report/${sessionId}`, { state: { report: data.final_report, qaLog: data.qa_log || [] } });
    }
  }
  async function handleTextSubmit(e) {
    e.preventDefault();
    const payload = isCodingRound ? code : answer;
    if (!payload.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      const data = await submitAnswer(sessionId, payload, isCodingRound ? codeLanguage : null);
      await processResult(data);
    } catch (err) {
      setError(err);
    } finally {
      setSubmitting(false);
    }
  }
  async function handleVoiceSubmit(blob) {
    setSubmitting(true);
    setError(null);
    try {
      const data = await submitAnswerAudio(sessionId, blob);
      await processResult(data);
    } catch (err) {
      setError(err);
    } finally {
      setSubmitting(false);
    }
  }
  return (
    <div className="min-h-screen flex flex-col items-center px-6 py-12 screen-enter">
      <Background3D />
      <div className="w-full max-w-2xl">
        <RoundProgress
          currentRound={state.current_round}
          questionsAsked={state.questions_asked_in_round}
          maxQuestions={state.max_questions_per_round}
        />
        <div className="mt-12">
          {}
          <div className="flex items-center justify-between mb-4 bg-panel/70 backdrop-blur-sm border border-line rounded-lg px-4 py-3">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs uppercase tracking-wider text-signal">
                AI Interviewer
              </span>
              <span className="inline-block w-[2px] h-4 bg-signal animate-pulse" />
            </div>
            <div className="flex items-center gap-3">
              {needsTapToPlay && (
                <button
                  type="button"
                  onClick={playQuestionAudio}
                  className="text-xs font-mono px-2.5 py-1 rounded-md bg-signal text-[#12141A] hover:opacity-90 transition"
                >
                  🔊 Hear question
                </button>
              )}
              <VoiceOrb mode={isSpeaking ? "speaking" : voiceMode ? "listening" : "idle"} />
            </div>
            {audioUrl && (
              <audio
                ref={audioRef}
                src={audioUrl}
                className="hidden"
                onPlay={() => setIsSpeaking(true)}
                onPause={() => setIsSpeaking(false)}
                onEnded={() => setIsSpeaking(false)}
              />
            )}
          </div>
          <p className="font-display text-2xl md:text-3xl leading-snug mb-2">
            {state.current_question}
          </p>
          <div className="mb-8" />
          {lastResult && lastResult.score != null && (
            <div className="mb-8 p-4 rounded-md bg-panel border border-line">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-mono uppercase tracking-wider text-muted">
                  Previous answer
                </span>
                <span
                  className="text-sm font-semibold"
                  style={{ color: lastResult.score >= 7 ? "#3FA796" : lastResult.score >= 4 ? "#E8A33D" : "#D9776B" }}
                >
                  {lastResult.score}/10
                </span>
              </div>
              <p className="text-sm text-muted leading-relaxed">{lastResult.feedback}</p>
              {lastResult.confidenceFlags?.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-3">
                  {lastResult.confidenceFlags.map((flag, i) => (
                    <span
                      key={i}
                      className="text-xs font-mono px-2 py-1 rounded-md bg-flag/10 text-flag border border-flag/30"
                    >
                      {flag}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}
          {isCodingRound ? (
            <form onSubmit={handleTextSubmit} className="space-y-4">
              <CodeEditor
                value={code}
                onChange={setCode}
                language={codeLanguage}
                onLanguageChange={setCodeLanguage}
                disabled={submitting}
              />
              <RateLimitNotice error={error} />
              <button
                type="submit"
                disabled={submitting || !code.trim()}
                className="bg-signal text-[#12141A] font-semibold px-6 py-2.5 rounded-md hover:opacity-90 transition disabled:opacity-50"
              >
                {submitting ? "Evaluating..." : "Submit code"}
              </button>
            </form>
          ) : (
            <>
              <div className="flex items-center gap-3 mb-4">
                <button
                  type="button"
                  onClick={() => setVoiceMode(false)}
                  className={`text-xs font-mono uppercase tracking-wider px-3 py-1.5 rounded-md transition ${!voiceMode ? "bg-signal text-[#12141A]" : "bg-panel text-muted border border-line"}`}
                >
                  Type
                </button>
                <button
                  type="button"
                  onClick={() => setVoiceMode(true)}
                  className={`text-xs font-mono uppercase tracking-wider px-3 py-1.5 rounded-md transition ${voiceMode ? "bg-signal text-[#12141A]" : "bg-panel text-muted border border-line"}`}
                >
                  Speak
                </button>
              </div>

              {voiceMode ? (
                <div className="space-y-4">
                  <VoiceRecorder onRecordingComplete={handleVoiceSubmit} disabled={submitting} />
                  {submitting && <p className="text-sm text-muted">Transcribing and evaluating your answer...</p>}
                  <RateLimitNotice error={error} />
                </div>
              ) : (
                <form onSubmit={handleTextSubmit} className="space-y-4">
                  <textarea
                    value={answer}
                    onChange={(e) => setAnswer(e.target.value)}
                    placeholder="Type your answer..."
                    rows={6}
                    className="w-full bg-panel border border-line rounded-md px-4 py-3 text-sm placeholder:text-muted focus:border-signal outline-none resize-none"
                    autoFocus
                  />
                  <RateLimitNotice error={error} />
                  <button
                    type="submit"
                    disabled={submitting || !answer.trim()}
                    className="bg-signal text-[#12141A] font-semibold px-6 py-2.5 rounded-md hover:opacity-90 transition disabled:opacity-50"
                  >
                    {submitting ? "Evaluating..." : "Submit answer"}
                  </button>
                </form>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}