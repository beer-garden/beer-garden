import { createTheme } from "@mui/material";
import {
  blue,
  deepOrange,
  grey,
  lightGreen,
  red,
  teal,
} from "@mui/material/colors";

const lightPalette = {
  mode: "light" as const,
  primary: { main: teal[400], contrastText: grey[900], dark: teal[900] },
  secondary: { main: red[400], contrastText: grey[900], dark: red[900] },
  error: { main: red[400], contrastText: grey[900], dark: red[900] },
  info: { main: blue[400], contrastText: grey[900], dark: blue[800] },
  success: {
    main: lightGreen[400],
    contrastText: grey[900],
    dark: lightGreen[900],
  },
  warning: {
    main: deepOrange[400],
    contrastText: grey[900],
    dark: deepOrange[900],
  },
  background: {
    default: grey[100],
    paper: grey[50],
  },
  text: {
    primary: grey[900],
    secondary: grey[800],
    disabled: grey[700],
  },
  action: {
    active: grey[100],
    hover: grey[600],
    selected: grey[500],
  },
  divider: grey[700],
};

const darkPalette = {
  mode: "dark" as const,
  primary: { main: teal[900], contrastText: grey[50], dark: teal[400] },
  secondary: { main: red[900], contrastText: grey[50], dark: red[400] },
  error: { main: red[900], contrastText: grey[50], dark: red[400] },
  info: { main: blue[900], contrastText: grey[50], dark: blue[400] },
  success: {
    main: lightGreen[900],
    contrastText: grey[50],
    dark: lightGreen[400],
  },
  warning: {
    main: deepOrange[900],
    contrastText: grey[50],
    dark: deepOrange[400],
  },
  background: {
    default: grey[900],
    paper: grey[800],
  },
  text: {
    primary: grey[50],
    secondary: grey[400],
  },
  action: {
    active: grey[100],
    hover: grey[800],
    selected: grey[700],
  },
  divider: grey[700],
};

const buttonStyleGenerator = (ownerState: any, theme: any) => {
  if (ownerState?.variant !== "text") {
    const themeColor = theme.palette[ownerState.color];
    if (themeColor) {
      return {
        borderColor: themeColor?.dark,
        color: themeColor?.contrastText,
        background: themeColor?.main,
        borderWidth: "1px",
      };
    }

    return {
      borderColor: theme.palette.info.dark,
      color: theme.palette.info.contrastText,
      background: theme.palette.info.main,
      borderWidth: "1px",
    };
  }

  return {};
};

const chipStyleGenerator = (ownerState: any, theme: any) => {
  const themeColor = theme.palette[ownerState.color];
  if (themeColor) {
    return {
      border: `1px solid ${themeColor?.dark}`,
    };
  }

  return {
    border: `1px solid ${theme.palette.info.dark}`,
  };
};

// See https://mui.com/material-ui/customization/palette/#color-schemes
export const theme = createTheme({
  colorSchemes: {
    light: { palette: lightPalette },
    dark: { palette: darkPalette },
  },
  defaultColorScheme: "light",
  components: {
    MuiStepIcon: {
      styleOverrides: {
        root: ({ theme }) => ({
          "&.Mui-active": {
            color: theme.palette.info.main,
          },
          "&.Mui-completed": {
            color: theme.palette.info.main,
          },
        }),
      },
    },
    MuiTablePagination: {
      styleOverrides: {
        selectIcon: ({ theme }) => ({
          color: theme.palette.text.primary,
        }),
        root: {
          "& .MuiTablePagination-spacer": { display: "none" },
          "& .MuiTablePagination-toolbar": {
            justifyContent: "flex-start",
            paddingLeft: 2,
          },
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: ({ ownerState, theme }) => ({
          ...buttonStyleGenerator(ownerState, theme),
        }),
      },
    },
    MuiChip: {
      styleOverrides: {
        root: ({ ownerState, theme }) => ({
          ...chipStyleGenerator(ownerState, theme),
        }),
      },
    },
    MuiFormHelperText: {
      styleOverrides: {
        root: ({ theme }) => ({
          color: theme.palette.primary.contrastText,
          "&.Mui-error": {
            color: theme.palette.error.contrastText,
          },
        }),
      },
    },
    MuiInputLabel: {
      styleOverrides: {
        root: ({ theme }) => ({
          // Changes the text color globally
          color: theme.palette.primary.contrastText,
        }),
      },
    },
    MuiToggleButton: {
      styleOverrides: {
        root: ({ theme }) => ({
          color: theme.palette.primary.contrastText, // Sets the non-selected text color
          "&.Mui-selected": {
            color: theme.palette.primary.contrastText, // Sets the selected text color if needed
            backgroundColor: theme.palette.info.main,
          },
        }),
      },
    },
    MuiIconButton: {
      styleOverrides: {
        root: ({ theme }) => ({
          color: theme.palette.text.primary,
        }),
      },
    },
    MuiLink: {
      defaultProps: {
        underline: "hover",
      },
      styleOverrides: {
        root: ({ theme }) => ({
          color: theme.palette.primary.contrastText,
          fontWeight: 600,
          textDecoration: "none",
          "&:hover": {
            color: theme.palette.primary.contrastText,
          },
        }),
      },
    },
    MuiAutocomplete: {
      styleOverrides: {
        popupIndicator: ({ theme }) => ({
          color: theme.palette.text.primary,
        }),
      },
    },
    MuiSelect: {
      styleOverrides: {
        icon: ({ theme }) => ({
          color: theme.palette.text.primary,
        }),
      },
    },
    MuiTab: {
      styleOverrides: {
        root: ({ theme }) => ({
          color: theme.palette.text.secondary,
          "&.Mui-selected": {
            color: theme.palette.text.primary,
          },
        }),
      },
    },
  },
});
