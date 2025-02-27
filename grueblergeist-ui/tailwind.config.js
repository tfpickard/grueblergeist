/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        neonPink: "#ff007f",
        neonBlue: "#00eaff",
        deepPurple: "#240046",
        blackBg: "#121212",
      },
    },
  },
  plugins: [],
};
