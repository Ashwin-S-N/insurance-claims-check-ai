import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#17201c",
        plum: "#7c3f58",
        plumDark: "#653047",
        plumSoft: "#f4e8ee",
        mint: "#dff3ea",
        clay: "#c46f4f",
        page: "#f6f7f4",
        code: "#141816"
      }
    }
  },
  plugins: []
};

export default config;
