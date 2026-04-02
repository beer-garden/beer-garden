import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Button } from "primereact/button";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { Config } from "../models/models";
import { ClearRefresh, ClearToken } from "../services/token_service";
import { GetCurrentUser } from "../services/user_service";
import CurrentRequestsTemplate from "./CurrentRequestsTemplate";
import UserLogin from "./UserLogin";

function NavigationMenu({
  listeners,
  config,
  runReloadUI,
}: {
  listeners: Record<string, any>;
  config: Config;
  runReloadUI: () => void;
}) {
  const [iconDefault, setIconDefault] = useState<string>(
    config?.icon_default ?? "beer-mug-empty",
  );
  const [applicationName, setApplicationName] = useState<string | undefined>(
    config?.application_name,
  );
  const [authEnabled, setAuthEnabled] = useState<boolean | undefined>(
    config?.auth_enabled,
  );

  const getUserName = () => {
    if (authEnabled === true) {
      return GetCurrentUser();
    }
    return undefined;
  };

  const [username, setUserName] = useState<string | undefined>(getUserName());
  const [loginVisible, setLoginVisible] = useState(false);

  const updateUserName = (username: string | undefined) => {
    setUserName(username);
    runReloadUI();
  };

  useEffect(() => {
    if (config?.icon_default && config.icon_default !== iconDefault) {
      setIconDefault(config.icon_default);
    }

    if (
      config?.application_name &&
      config.application_name !== applicationName
    ) {
      setApplicationName(config.application_name);
    }

    if (
      config?.auth_enabled !== undefined &&
      config.auth_enabled !== authEnabled
    ) {
      setAuthEnabled(config.auth_enabled);
      if (config.auth_enabled && username === undefined) {
        setLoginVisible(true);
      } else if (!config.auth_enabled) {
        ClearToken();
        ClearRefresh().catch((error) => {
          console.error("Error Clearing Refresh Token:", error);
        });
      }
    }
  }, [config, authEnabled, username, iconDefault, applicationName]);

  const buttonProps = {
    className: "p-button-plain p-button-text mr-2",
  };

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        borderBottom: "1px solid",
      }}
    >
      <Link to={`/`}>
        <Button
          icon={<FontAwesomeIcon className="mr-2" icon={iconDefault} />}
          {...buttonProps}
        >
          {applicationName}
        </Button>
      </Link>
      <Link to={`/requests`}>
        <Button {...buttonProps}>Requests</Button>
      </Link>
      <Link to={`/jobs`}>
        <Button {...buttonProps}>Scheduler</Button>
      </Link>
      <Link to={`/topics`}>
        <Button {...buttonProps}>Topics</Button>
      </Link>
      <Link to={`/users`}>
        <Button {...buttonProps}>Users</Button>
      </Link>
      <Link to={`/roles`}>
        <Button {...buttonProps}>Roles</Button>
      </Link>
      <Link to={`/about`}>
        <Button {...buttonProps}>About</Button>
      </Link>

      <div style={{ marginLeft: "auto" }}>
        <div className="flex">
          {authEnabled === true && (
            <div>
              {username === undefined && (
                <div>
                  <Button
                    {...buttonProps}
                    text
                    onClick={() => setLoginVisible(true)}
                    data-testid="user-login"
                  >
                    Login
                  </Button>
                  <UserLogin
                    visible={loginVisible}
                    setVisible={setLoginVisible}
                    setUsernameDisplay={updateUserName}
                  />
                </div>
              )}
              {username !== undefined && (
                <div className="flex align-items-center">
                  <div className="align-items-center mr-2">
                    Welcome {username}!
                  </div>
                  <Button
                    {...buttonProps}
                    onClick={() => {
                      ClearToken();
                      ClearRefresh()
                        .finally(() => {
                          updateUserName(undefined);
                        })
                        .catch((error) => {
                          console.error("Error clearing Refresh Token:", error);
                        });
                    }}
                    data-testid="user-logout"
                  >
                    Logout
                  </Button>
                </div>
              )}
            </div>
          )}

          <CurrentRequestsTemplate listeners={listeners} />
        </div>
      </div>
    </div>
  );
}

export default NavigationMenu;
