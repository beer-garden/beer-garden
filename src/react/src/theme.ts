export const getTheme = (mode: string) => ({
  ...(mode === "dark" ? darkColorScheme : lightColorScheme),
});

const darkColorScheme = {
  primary: {
    main: "#374151", // Your primary brand color
    contrastText: "#fff",
  },
  background: { default: "#370712" },
  text: { primary: "#ffffff", secondary: "#ffffff" },
  // more colors
};
const lightColorScheme = {
  primary: {
    main: "#1976d2", // Your primary brand color
  },
  background: { default: "#ffffff" },
  text: { primary: "#000000", secondary: "#ffffff" },
  // more colors
};
