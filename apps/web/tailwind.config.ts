import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          950: "#080f33",
          900: "#0d1642",
          850: "#101a4d",
          800: "#152058",
          700: "#1c2a68",
          600: "#293878",
          500: "#3a4a8a",
        },
        gold: {
          400: "#fbd452",
          500: "#f5c518",
          600: "#dba800",
        },
      },
      fontFamily: {
        sans: [
          "var(--font-inter)",
          "ui-sans-serif",
          "system-ui",
          "sans-serif",
        ],
      },
      backgroundImage: {
        "hero-gradient":
          "radial-gradient(120% 140% at 15% 0%, #35406d 0%, #1a2560 32%, #0d1642 62%, #080f33 100%)",
        "cta-gradient": "linear-gradient(90deg, #fbd452 0%, #f5c518 100%)",
      },
      boxShadow: {
        card: "0 8px 30px -8px rgba(13, 22, 66, 0.15)",
        "card-lg": "0 20px 60px -15px rgba(13, 22, 66, 0.35)",
      },
      borderRadius: {
        xl2: "1.25rem",
      },
    },
  },
  plugins: [],
};

export default config;
