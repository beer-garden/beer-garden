import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Avatar } from "primereact/avatar";
import { Divider } from "primereact/divider";
import { Dropdown } from "primereact/dropdown";
import { InputSwitch } from "primereact/inputswitch";
import React, { useEffect, useRef, useState } from "react";

import {
  ChangePowerUser,
  ChangeTheme,
  FAIcon,
  ThemeOptions,
} from "../services/util_service";
import AccessButton from "./AccessButton";
import UserChangePassword from "./UserChangePassword";
import { Autocomplete, Box, MenuItem, Select, Switch, TextField } from "@mui/material";
import { AutoComplete } from "primereact/autocomplete";

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

  const focusRef = useRef<InputSwitch>(null);

  useEffect(() => {
    // Focus the element when the component mounts
    focusRef.current?.focus();
  }, []);

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
  }

  return (
    <>
      {username && showPasswordDialog && (
        <UserChangePassword
          username={username}
          isAdmin={false}
          showPasswordDialog={showPasswordDialog}
          setShowPasswordDialog={setShowPasswordDialog}
          callback={() => setShowPasswordDialog(false)}
        />
      )}
      <div>
        {username && (
          <div>
            <div className="flex align-items-center gap-2">
              <Avatar
                label={username.charAt(0).toUpperCase()}
                className="mr-2"
              />
              <span>{username}</span>
            </div>
            <Divider />
          </div>
        )}
        <div className="flex align-items-center gap-2">
          <Switch
            checked={dark}
            onChange={(e) => setDark(e.target.checked)}
          />
          <span className="ml-2" id="switchMode">
            {dark ? (
              <>
                <FAIcon icon="moon" sx={{mr: 2, color: "black"}} />
                <Box component="span" sx={{color: "black"}}>Dark Mode</Box>
              </>
            ) : (
              <>
                <FAIcon icon="sun" sx={{mr: 2, color: "black"}} />
                <Box component="span" sx={{color: "black"}}>Light Mode</Box>
              </>
            )}
          </span>
          <datalist id="selectThemeColorDropdown" aria-hidden="true">
            {ThemeOptions().map((color: string) => (
              <option key={color} value={color} />
            ))}
          </datalist>
          <Autocomplete
            disablePortal
            value={color}
            onChange={handleColor}
            renderInput={(params) => <TextField {...params} label="Select a Color" />}
            sx={{ width: 150 }}
            options={ThemeOptions()}
          />
        </div>
        <div className="flex align-items-center gap-2">
          <Switch
            checked={showAdvancedOption}
            onChange={(e) => {
              setShowAdvancedOption(e.target.checked);
            }}
          />
          <Box component="span" id="switchPowerUser" sx={{ml:2, color: "black"}}>
            Power User
          </Box>
        </div>
      </div>
      {username && (
        <>
          <div>
            <div className="mt-2">
              <AccessButton
                style={{ marginLeft: "auto" }}
                size="small"
                onClick={() => setShowPasswordDialog(true)}
                data-testid="user-password-overlay"
              >
                <FontAwesomeIcon className="mr-2" icon="key" />
                <span>Change Password</span>
              </AccessButton>
            </div>
          </div>

          <div>
            <Divider />
            <AccessButton
              size="small"
              className="mr-2"
              onClick={onLogout}
              data-testid="user-logout-overlay"
            >
              <FontAwesomeIcon className="mr-2" icon="sign-out" />
              <span>Logout</span>
            </AccessButton>
          </div>
        </>
      )}

      {username === undefined && (
        <div>
          <Divider />
          <AccessButton
            size="small"
            severity="warning"
            className="mr-2"
            onClick={onClearSession}
            data-testid="clear-session-overlay"
          >
            <FontAwesomeIcon className="mr-2" icon="eraser" />
            <span>Clear Session Data</span>
          </AccessButton>
        </div>
      )}
    </>
  );
}

export default UserOverlay;
