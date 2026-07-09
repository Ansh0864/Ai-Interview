/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        base: "#12141A",
        panel: "#1B1E27",
        line: "#2B2F3B",
        ink: "#EDEDEF",
        muted: "#9A9EAE",
        signal: "#E8A33D",
        pass: "#3FA796",
        flag: "#D9776B",
      },
      fontFamily: {
        display: ["Fraunces", "serif"],
        body: ["Inter", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      keyframes: {
        eqBounce: {
          "0%, 100%": { transform: "scaleY(0.3)" },
          "50%": { transform: "scaleY(1)" },
        },
      },
      animation: {
        "eq-1": "eqBounce 0.9s ease-in-out infinite",
        "eq-2": "eqBounce 0.7s ease-in-out infinite 0.15s",
        "eq-3": "eqBounce 1.1s ease-in-out infinite 0.3s",
        "eq-4": "eqBounce 0.8s ease-in-out infinite 0.1s",
        "eq-5": "eqBounce 1.0s ease-in-out infinite 0.25s",
      },
    },
  },
  plugins: [],
};
