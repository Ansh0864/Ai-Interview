import CodeMirror from "@uiw/react-codemirror";
import { javascript } from "@codemirror/lang-javascript";
import { python } from "@codemirror/lang-python";
import { cpp } from "@codemirror/lang-cpp";
import { java } from "@codemirror/lang-java";
import { tokyoNight } from "@uiw/codemirror-theme-tokyo-night";

export const CODE_LANGUAGES = {
  python: { label: "Python", extension: python() },
  javascript: { label: "JavaScript", extension: javascript() },
  cpp: { label: "C++", extension: cpp() },
  java: { label: "Java", extension: java() },
};

/**
 * Fully controlled: `language` and `onLanguageChange` come from the parent
 * so the selected language can actually be sent to the backend and
 * enforced during scoring - previously this was local-only state used
 * purely for syntax highlighting, so picking "Python" never stopped you
 * from submitting Java and having it graded as if it were fine.
 */
export default function CodeEditor({ value, onChange, language, onLanguageChange, disabled }) {
  return (
    <div className="rounded-md overflow-hidden border border-line">
      <div className="flex items-center justify-between bg-panel px-3 py-2 border-b border-line">
        <span className="text-xs font-mono uppercase tracking-wider text-muted">
          Code answer (explain your approach in comments if useful)
        </span>
        <div className="flex gap-1">
          {Object.entries(CODE_LANGUAGES).map(([key, lang]) => (
            <button
              key={key}
              type="button"
              onClick={() => onLanguageChange(key)}
              className={`text-xs font-mono px-2.5 py-1 rounded transition ${
                language === key ? "bg-signal text-[#12141A]" : "text-muted hover:text-ink"
              }`}
            >
              {lang.label}
            </button>
          ))}
        </div>
      </div>
      <CodeMirror
        value={value}
        height="260px"
        theme={tokyoNight}
        extensions={[CODE_LANGUAGES[language].extension]}
        onChange={onChange}
        editable={!disabled}
        basicSetup={{ lineNumbers: true, foldGutter: true, tabSize: 2 }}
        placeholder="// Write your solution here..."
      />
      <p className="text-xs text-muted px-3 py-2 bg-panel/50 border-t border-line">
        Selected language is sent with your answer and checked against what you actually wrote —
        submitting a different language than selected will be marked down heavily.
      </p>
    </div>
  );
}