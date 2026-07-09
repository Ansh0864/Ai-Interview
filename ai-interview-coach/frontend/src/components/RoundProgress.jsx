const ROUNDS = [
  { key: "behavioral", label: "Behavioral" },
  { key: "hr", label: "HR" },
  { key: "coding", label: "Coding" },
];

export default function RoundProgress({ currentRound, questionsAsked, maxQuestions }) {
  const currentIndex = ROUNDS.findIndex((r) => r.key === currentRound);

  return (
    <div className="w-full">
      <div className="flex gap-2">
        {ROUNDS.map((round, i) => {
          const isDone = i < currentIndex;
          const isActive = i === currentIndex;
          return (
            <div key={round.key} className="flex-1">
              <div className="h-1 rounded-full overflow-hidden bg-line">
                <div
                  className="h-full transition-all duration-500"
                  style={{
                    width: isDone ? "100%" : isActive ? `${(questionsAsked / maxQuestions) * 100}%` : "0%",
                    backgroundColor: isDone ? "#3FA796" : "#E8A33D",
                  }}
                />
              </div>
              <p className={`mt-2 text-xs font-mono uppercase tracking-wider ${isActive ? "text-signal" : isDone ? "text-pass" : "text-muted"}`}>
                {round.label}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
