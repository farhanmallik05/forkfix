/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        obsidian: {
          950: "rgb(var(--obsidian-950) / <alpha-value>)",
          900: "rgb(var(--obsidian-900) / <alpha-value>)",
          850: "rgb(var(--obsidian-850) / <alpha-value>)",
          800: "rgb(var(--obsidian-800) / <alpha-value>)",
          700: "rgb(var(--obsidian-700) / <alpha-value>)",
          600: "rgb(var(--obsidian-600) / <alpha-value>)",
        },
        cyber: {
          emerald: "#10B981",
          crimson: "#EF4444",
          violet: "#8B5CF6",
          amber: "#F59E0B",
          cyan: "#06B6D4",
        },
      },
    },
  },
  plugins: [],
}
