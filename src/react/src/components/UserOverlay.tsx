import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Avatar } from "primereact/avatar";
import { Button } from "primereact/button";
import { Divider } from "primereact/divider";
import { Dropdown } from "primereact/dropdown";
import { InputSwitch } from "primereact/inputswitch";
import { Toast } from "primereact/toast";
import { useEffect, useRef, useState } from "react";

import { ChangeTheme, ThemeOptions } from "../services/util_service";
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
    ChangeTheme(color, dark);
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
              <Button
                style={{ marginLeft: "auto" }}
                size="small"
                onClick={() => setShowPasswordDialog(true)}
                data-testid="user-password-overlay"
              >
                <FontAwesomeIcon className="mr-2" icon="key" />
                <span>Change Password</span>
              </Button>
            </div>
            <Divider />
          </div>
        )}
        <div className="flex align-items-center gap-2">
          <InputSwitch
            checked={dark}
            onChange={(e) => setDark(e.value)}
            className="align-self-center"
          />
          <span className="ml-2">
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
          <Dropdown
            value={color}
            onChange={(e) => setColor(e.value)}
            options={ThemeOptions()}
            optionLabel="Color"
            placeholder="Select a Color"
            className="mr-2"
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
          />
          <span className="ml-2">Power User</span>
        </div>
      </div>
      {username && (
        <div>
          <Divider />
          <Button
            size="small"
            className="mr-2"
            onClick={onLogout}
            data-testid="user-logout-overlay"
          >
            <FontAwesomeIcon className="mr-2" icon="sign-out" />
            <span>Logout</span>
          </Button>
        </div>
      )}
    </>
  );
}

export default UserOverlay;
