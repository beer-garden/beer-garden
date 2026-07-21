import CssBaseline from "@mui/material/CssBaseline";
import { createTheme, PaletteMode, ThemeProvider } from "@mui/material/styles";
import { createContext, ReactNode, useContext, useMemo, useState } from "react";

import { getTheme } from "../theme";

// Create the context
interface ColorModeContextType {
  toggleColorMode: (isDark: boolean) => void;
}

const ColorModeContext = createContext<ColorModeContextType | undefined>(
  undefined,
);

// Create the Provider
export const ColorModeProvider = ({ children }: { children: ReactNode }) => {
  const [mode, setMode] = useState<PaletteMode>("light");

  const colorMode = useMemo(
    () => ({
      toggleColorMode: (isDark: boolean) => {
        setMode(isDark ? "dark" : "light");
      },
    }),
    [],
  );

  const theme = useMemo(() => {
    const colors = getTheme(mode);
    return createTheme({
      palette: {
        mode: mode,
        primary: {
          main: colors.primary.main,
        },
        background: {
          default: colors.background.default,
        },
        text: {
          primary: colors.text.primary,
          secondary: colors.text.secondary,
        },
      },
    });
  }, [mode]);

  return (
    <ColorModeContext.Provider value={colorMode}>
      <ThemeProvider theme={theme}>
        <CssBaseline /> {/* Normalizes background and text colors */}
        {children}
      </ThemeProvider>
    </ColorModeContext.Provider>
  );
};

// Create a custom hook for consuming the context
export const useColorMode = () => {
  const context = useContext(ColorModeContext);
  if (!context) {
    throw new Error(
      "useColorMode must be used within a ColorModeContext.Provider",
    );
  }
  return context.toggleColorMode;
};
