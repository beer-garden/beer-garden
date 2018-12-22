import { createMuiTheme } from "@material-ui/core";

const defaultTypography = { useNextVariants: true };
export const THEMES = {
  light: createMuiTheme({ typography: defaultTypography }),
  dark: createMuiTheme({
    typography: defaultTypography,
    palette: { type: "dark" },
  }),
};
