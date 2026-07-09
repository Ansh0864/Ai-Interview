import { useState, useRef } from "react";

export default function VoiceRecorder({ onRecordingComplete, disabled }) {
  const [recording, setRecording] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);
  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];

      recorder.ondataavailable = (e) => chunksRef.current.push(e.data);
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        stream.getTracks().forEach((t) => t.stop());
        onRecordingComplete(blob);
      };

      recorder.start();
      mediaRecorderRef.current = recorder;
      setRecording(true);
      setSeconds(0);
      timerRef.current = setInterval(() => setSeconds((s) => s + 1), 1000);
    } catch (err) {
      alert("Microphone access is needed to answer by voice.");
    }
  }

  function stopRecording() {
    mediaRecorderRef.current?.stop();
    clearInterval(timerRef.current);
    setRecording(false);
  }
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={recording ? stopRecording : startRecording}
      className={`flex items-center gap-2 px-4 py-2.5 rounded-md text-sm font-medium border transition disabled:opacity-50 ${
        recording ? "bg-flag/10 border-flag text-flag" : "bg-panel border-line hover:border-signal"
      }`}
    >
      <span
        className="inline-block w-2.5 h-2.5 rounded-sm"
        style={{ backgroundColor: recording ? "#D9776B" : "#9A9EAE" }}
      />
      {recording ? `Recording... ${seconds}s (tap to stop)` : "Answer by voice"}
    </button>
  );
}
