import tokens from "./tokens.json";

export const themes = tokens;

export function applyTheme(themeName) {
  const theme = themes[themeName] ?? themes.light;
  const root = document.documentElement;
  root.setAttribute("data-theme", themeName);
  for (const [key, value] of Object.entries(theme)) {
    root.style.setProperty(`--${key.replace(/\./g, "-")}`, value);
  }
}
