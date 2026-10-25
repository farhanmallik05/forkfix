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
          950: "#07090C",
          900: "#0B0D11",
          850: "#101318",
          800: "#161B22",
          700: "#21262D",
          600: "#30363D",
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
