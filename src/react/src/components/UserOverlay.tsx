import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Avatar } from "primereact/avatar";
import { Divider } from "primereact/divider";
import { Dropdown } from "primereact/dropdown";
import { InputSwitch } from "primereact/inputswitch";
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

  const focusRef = useRef<InputSwitch>(null);

  useEffect(() => {
    // Focus the element when the component mounts
    focusRef.current?.focus();
  }, []);

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
            ref={focusRef}
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
            {ThemeOptions().map((color: string) => (
              <option key={color} value={color} />
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
              select: {
                "aria-controls": "selectThemeColorDropdown",
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
    </>
  );
}

export default UserOverlay;
