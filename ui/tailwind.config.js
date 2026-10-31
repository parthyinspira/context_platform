import tokens from "./src/tokens.json" with { type: "json" };

const colorKeys = Object.keys(tokens.light);

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: Object.fromEntries(
        colorKeys.map((key) => [
          key.replace(/\./g, "-"),
          `var(--${key.replace(/\./g, "-")})`,
        ]),
      ),
      fontFamily: {
        ui: tokens.type.fontUi.split(",").map((f) => f.trim()),
        mono: tokens.type.fontMono.split(",").map((f) => f.trim()),
      },
      borderRadius: {
        control: `${tokens.radius.control}px`,
        card: `${tokens.radius.card}px`,
      },
    },
  },
  plugins: [],
};
