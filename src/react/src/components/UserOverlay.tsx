import {
  Autocomplete,
  Avatar,
  Box,
  Divider,
  Stack,
  Switch,
  TextField,
} from "@mui/material";
import React, { useEffect, useState } from "react";

import {
  ChangePowerUser,
  ChangeTheme,
  FAIcon,
  ThemeOptions,
} from "../services/util_service";
import AccessButton from "./AccessButton";
import UserChangePassword from "./UserChangePassword";

function UserOverlay({
  username,
  onLogout,
  onClearSession,
}: {
  username: string | undefined;
  onLogout: any;
  onClearSession: any;
}) {
  const [color, setColor] = useState<string>(
    localStorage.getItem("theme_color") || "blue",
  );
  const [dark, setDark] = useState<boolean>(
    localStorage.getItem("theme_dark") === "true" || false,
  );
  const [showAdvancedOption, setShowAdvancedOption] = useState<boolean>(
    localStorage.getItem("user_advanced") === "true" || false,
  );

  const [showPasswordDialog, setShowPasswordDialog] = useState(false);

  useEffect(() => {
    if (
      (localStorage.getItem("user_advanced") === "true") !==
      showAdvancedOption
    ) {
      ChangePowerUser(showAdvancedOption);
    }
    if (
      (localStorage.getItem("theme_dark") === "true") !== dark ||
      localStorage.getItem("theme_color") !== color
    ) {
      ChangeTheme(color, dark);
      window.dispatchEvent(new Event("storage"));
    }
  }, [color, dark, showAdvancedOption]);

  const handleColor = (_: React.SyntheticEvent, newColor: string | null) => {
    if (newColor) {
      setColor(newColor);
    }
  };

  return (
    <Box>
      {username && showPasswordDialog && (
        <UserChangePassword
          username={username}
          isAdmin={false}
          showPasswordDialog={showPasswordDialog}
          setShowPasswordDialog={setShowPasswordDialog}
          callback={() => setShowPasswordDialog(false)}
        />
      )}
      <Box>
        {username && (
          <Box>
            <Box sx={{ display: "flex", justifyContent: "center", gap: 2 }}>
              <Stack direction="row" sx={{ alignItems: "center" }}>
                <Avatar sx={{ mr: 2 }}>
                  {username.charAt(0).toUpperCase()}
                </Avatar>
                <Box component="span" sx={{ color: "black" }}>
                  {username}
                </Box>
              </Stack>
            </Box>
            <Divider sx={{ my: 2 }} />
          </Box>
        )}
        {/* <Stack direction="row" sx={{alignItems: "center"}}></Stack>
        <Box sx={{display: "flex", justifyContent: "center", gap:2 }}> */}
        <Stack direction="row" sx={{ alignItems: "center" }}>
          <Switch checked={dark} onChange={(e) => setDark(e.target.checked)} />
          <Box component="span" sx={{ ml: 2 }} id="switchMode">
            {dark ? (
              <>
                <FAIcon icon="moon" sx={{ mr: 2, color: "black" }} />
                <Box component="span" sx={{ mr: 2, color: "black" }}>
                  Dark Mode
                </Box>
              </>
            ) : (
              <>
                <FAIcon icon="sun" sx={{ mr: 2, color: "black" }} />
                <Box component="span" sx={{ mr: 2, color: "black" }}>
                  Light Mode
                </Box>
              </>
            )}
          </Box>
          {/* </Stack> */}
          <datalist id="selectThemeColorDropdown" aria-hidden="true">
            {ThemeOptions().map((color: string) => (
              <option key={color} value={color} />
            ))}
          </datalist>
          <Autocomplete
            disablePortal
            value={color}
            onChange={handleColor}
            renderInput={(params) => (
              <TextField {...params} label="Select a Color" />
            )}
            sx={{ width: 150 }}
            options={ThemeOptions()}
          />
        </Stack>
        <Stack direction="row" sx={{ alignItems: "center" }}>
          <Switch
            checked={showAdvancedOption}
            onChange={(e) => {
              setShowAdvancedOption(e.target.checked);
            }}
          />
          <Box
            component="span"
            id="switchPowerUser"
            sx={{ ml: 2, color: "black" }}
          >
            Power User
          </Box>
        </Stack>
      </Box>
      {username && (
        <>
          <Box>
            <Box sx={{ mt: 2 }}>
              <AccessButton
                sx={{ marginLeft: "auto" }}
                size="small"
                onClick={() => setShowPasswordDialog(true)}
                data-testid="user-password-overlay"
              >
                <FAIcon sx={{ mr: 2 }} icon="key" />
                <Box component="span">Change Password</Box>
              </AccessButton>
            </Box>
          </Box>

          <Box>
            <Divider sx={{ my: 2 }} />
            <AccessButton
              size="small"
              sx={{ mr: 2 }}
              onClick={onLogout}
              data-testid="user-logout-overlay"
            >
              <FAIcon sx={{ mr: 2 }} icon="sign-out" />
              <Box component="span">Logout</Box>
            </AccessButton>
          </Box>
        </>
      )}

      {username === undefined && (
        <Box>
          <Divider sx={{ my: 2 }} />
          <AccessButton
            size="small"
            color="warning"
            sx={{ mr: 2 }}
            onClick={onClearSession}
            data-testid="clear-session-overlay"
          >
            <FAIcon sx={{ mr: 2 }} icon="eraser" />
            <Box component="span">Clear Session Data</Box>
          </AccessButton>
        </Box>
      )}
    </Box>
  );
}

export default UserOverlay;
