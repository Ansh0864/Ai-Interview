function formatSection(title, lines) {
  return `## ${title}\n\n${lines.join("\n")}\n`;
}
export function buildTranscriptMarkdown({ qaLog, report, resumeSummary, jdSummary, completedAt }) {
  const parts = [`# Interview Transcript\n`];
  if (completedAt) parts.push(`*Completed: ${new Date(completedAt).toLocaleString()}*\n`);
  if (resumeSummary) parts.push(`**Candidate background:** ${resumeSummary}\n`);
  if (jdSummary) parts.push(`**Role:** ${jdSummary}\n`);
  if (report) {
    parts.push(formatSection("Overall", [
      `**Score:** ${report.overall_score}/10`,
      "",
      "**Strengths:**",
      ...(report.strengths || []).map((s) => `- ${s}`),
      "",
      "**Areas to improve:**",
      ...(report.areas_to_improve || []).map((s) => `- ${s}`),
      "",
      "**Verdict:** " + (report.final_verdict || ""),
    ]));
  }
  const rounds = [...new Set((qaLog || []).map((e) => e.round))];
  for (const round of rounds) {
    const entries = qaLog.filter((e) => e.round === round);
    const lines = entries.flatMap((e, i) => [
      `**Q${i + 1}: ${e.question}**`,
      "",
      `> ${e.answer.replace(/\n/g, "\n> ")}`,
      "",
      `Score: ${e.score}/10 — ${e.feedback}`,
      e.confidence_flags?.length ? `Flags: ${e.confidence_flags.join(", ")}` : "",
      "",
    ]);
    parts.push(formatSection(round.charAt(0).toUpperCase() + round.slice(1) + " round", lines));
  }
  return parts.join("\n");
}

export function downloadTextFile(filename, content) {
  const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
