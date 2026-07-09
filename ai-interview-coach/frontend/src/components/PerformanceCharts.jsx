import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell,
} from "recharts";

const ROUND_COLORS = { behavioral: "#E8A33D", hr: "#3FA796", coding: "#D9776B" };

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="bg-panel border border-line rounded-md px-3 py-2 max-w-xs">
      <p className="text-xs font-mono uppercase tracking-wider mb-1" style={{ color: ROUND_COLORS[d.round] }}>
        {d.round} · Q{d.index}
      </p>
      <p className="text-xs text-muted line-clamp-2">{d.question}</p>
      <p className="text-sm font-semibold mt-1">{d.score}/10</p>
    </div>
  );
}

export default function PerformanceCharts({ qaLog }) {
  if (!qaLog?.length) return null;

  const progression = qaLog.map((e, i) => ({
    index: i + 1,
    score: e.score,
    round: e.round,
    question: e.question,
  }));

  const roundKeys = ["behavioral", "hr", "coding"];
  const roundAverages = roundKeys
    .map((round) => {
      const entries = qaLog.filter((e) => e.round === round);
      if (!entries.length) return null;
      const avg = entries.reduce((sum, e) => sum + e.score, 0) / entries.length;
      return { round, average: Math.round(avg * 10) / 10 };
    })
    .filter(Boolean);

  const flagCounts = {};
  qaLog.forEach((e) => {
    (e.confidence_flags || []).forEach((flag) => {
      flagCounts[flag] = (flagCounts[flag] || 0) + 1;
    });
  });
  const flagData = Object.entries(flagCounts)
    .map(([flag, count]) => ({ flag, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 6);

  return (
    <div className="space-y-10">
      <div>
        <p className="text-xs font-mono uppercase tracking-wider text-muted mb-4">Score progression</p>
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={progression} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2B2F3B" vertical={false} />
            <XAxis dataKey="index" stroke="#9A9EAE" fontSize={12} tickLine={false} />
            <YAxis domain={[0, 10]} stroke="#9A9EAE" fontSize={12} tickLine={false} />
            <Tooltip content={<CustomTooltip />} />
            <Line
              type="monotone"
              dataKey="score"
              stroke="#E8A33D"
              strokeWidth={2}
              dot={{ r: 4, fill: "#E8A33D" }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div>
        <p className="text-xs font-mono uppercase tracking-wider text-muted mb-4">Average score by round</p>
        <ResponsiveContainer width="100%" height={180}>
          <BarChart data={roundAverages} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2B2F3B" vertical={false} />
            <XAxis dataKey="round" stroke="#9A9EAE" fontSize={12} tickLine={false} />
            <YAxis domain={[0, 10]} stroke="#9A9EAE" fontSize={12} tickLine={false} />
            <Tooltip
              contentStyle={{ background: "#1B1E27", border: "1px solid #2B2F3B", borderRadius: 6 }}
              labelStyle={{ color: "#EDEDEF" }}
            />
            <Bar dataKey="average" radius={[4, 4, 0, 0]}>
              {roundAverages.map((entry, i) => (
                <Cell key={i} fill={ROUND_COLORS[entry.round]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {flagData.length > 0 && (
        <div>
          <p className="text-xs font-mono uppercase tracking-wider text-muted mb-4">
            Communication patterns observed
          </p>
          <ResponsiveContainer width="100%" height={Math.max(120, flagData.length * 40)}>
            <BarChart
              data={flagData}
              layout="vertical"
              margin={{ top: 5, right: 20, left: 10, bottom: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#2B2F3B" horizontal={false} />
              <XAxis type="number" stroke="#9A9EAE" fontSize={12} tickLine={false} allowDecimals={false} />
              <YAxis
                type="category"
                dataKey="flag"
                stroke="#9A9EAE"
                fontSize={11}
                width={160}
                tickLine={false}
              />
              <Tooltip
                contentStyle={{ background: "#1B1E27", border: "1px solid #2B2F3B", borderRadius: 6 }}
                labelStyle={{ color: "#EDEDEF" }}
              />
              <Bar dataKey="count" fill="#D9776B" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
