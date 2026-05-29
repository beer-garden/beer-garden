import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Avatar } from "primereact/avatar";
import { Divider } from "primereact/divider";
import { Dropdown } from "primereact/dropdown";
import { InputSwitch } from "primereact/inputswitch";
import { Toast } from "primereact/toast";
import { useEffect, useRef, useState } from "react";

import { ChangeTheme, ThemeOptions } from "../services/util_service";
import AccessButton from "./AccessButton";
import UserChangePassword from "./UserChangePassword";

function UserOverlay({
  username,
  onLogout,
}: {
  username: string | undefined;
  onLogout: any;
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
  const toast = useRef<Toast>(null);

  useEffect(() => {
    if (
      (localStorage.getItem("theme_dark") === "true") !== dark ||
      localStorage.getItem("theme_color") !== color
    ) {
      ChangeTheme(color, dark);
      window.dispatchEvent(new Event("storage"));
    }
  }, [color, dark]);

  return (
    <>
      <Toast ref={toast} />
      {username && showPasswordDialog && (
        <UserChangePassword
          username={username}
          isAdmin={false}
          showPasswordDialog={showPasswordDialog}
          setShowPasswordDialog={setShowPasswordDialog}
          toast={toast}
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
            <Divider />
          </div>
        )}
        <div className="flex align-items-center gap-2">
          <InputSwitch
            checked={dark}
            onChange={(e) => setDark(e.value)}
            className="align-self-center"
            pt={{
              root: {
                role: undefined,
                "aria-checked": undefined,
              },
              input: {
                "aria-labelledby": "switchMode",
              },
            }}
          />
          <span className="ml-2" id="switchMode">
            {dark ? (
              <>
                <FontAwesomeIcon className="mr-2" icon="moon" />
                <span>Dark Mode</span>
              </>
            ) : (
              <>
                <FontAwesomeIcon className="mr-2" icon="sun" />
                <span>Light Mode</span>
              </>
            )}
          </span>
          <datalist id="selectThemeColorDropdown" aria-hidden="true">
            {ThemeOptions().map((status: any) => (
              <option key={status.label} value={status.value} />
            ))}
          </datalist>
          <Dropdown
            value={color}
            onChange={(e) => setColor(e.value)}
            options={ThemeOptions()}
            optionLabel="Color"
            placeholder="Select a Color"
            className="mr-2"
            pt={{
              dropdownIcon: {
                role: "img",
                "aria-label": "Dropdown icon for selecting theme color",
              },
              input: {
                autoComplete: "off",
                "aria-label": "Dropdown theme color",
              },
              select: {
                autoComplete: "off",
                "aria-controls": "selectThemeColorDropdown",
                "aria-label": "Select theme color",
              },
            }}
          />
        </div>
        <div className="flex align-items-center gap-2">
          <InputSwitch
            checked={showAdvancedOption}
            onChange={(e) => {
              setShowAdvancedOption(e.value);
              localStorage.setItem("user_advanced", JSON.stringify(e.value));
            }}
            className="align-self-center"
            pt={{
              root: {
                role: undefined,
                "aria-checked": undefined,
              },
              input: {
                "aria-labelledby": "switchPowerUser",
              },
            }}
          />
          <span className="ml-2" id="switchPowerUser">
            Power User
          </span>
        </div>
      </div>
      {username && (
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
      )}
    </>
  );
}

export default UserOverlay;
