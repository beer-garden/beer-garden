import { createTheme } from "@mui/material";
import {
  blue,
  deepOrange,
  green,
  grey,
  lightGreen,
  red,
} from "@mui/material/colors";

const lightPalette = {
  mode: "light" as const,
  primary: { main: green[400], contrastText: grey[900] },
  secondary: { main: red[400], contrastText: grey[900] },
  error: { main: red[400], contrastText: grey[900] },
  info: { main: blue[400], contrastText: grey[900] },
  success: { main: lightGreen[400], contrastText: grey[900] },
  warning: { main: deepOrange[400], contrastText: grey[900] },
  background: {
    default: grey[100],
    paper: grey[50],
  },
  text: {
    primary: grey[900],
    secondary: grey[800],
  },
  action: {
    active: grey[100],
    hover: grey[600],
    selected: grey[700],
  },
  divider: grey[700],
};

const darkPalette = {
  mode: "dark" as const,
  primary: { main: green[900], contrastText: grey[50] },
  secondary: { main: red[900], contrastText: grey[50] },
  error: { main: red[900], contrastText: grey[50] },
  info: { main: blue[900], contrastText: grey[50] },
  success: { main: lightGreen[900], contrastText: grey[50] },
  warning: { main: deepOrange[900], contrastText: grey[50] },
  background: {
    default: grey[900],
    paper: grey[800],
  },
  text: {
    primary: grey[50],
    secondary: grey[100],
  },
  action: {
    active: grey[100],
    hover: grey[800],
    selected: grey[700],
  },
  divider: grey[700],
};

// See https://mui.com/material-ui/customization/palette/#color-schemes
export const theme = createTheme({
  colorSchemes: {
    light: { palette: lightPalette },
    dark: { palette: darkPalette },
  },
  defaultColorScheme: "light",
});
