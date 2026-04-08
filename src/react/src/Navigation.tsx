import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Button } from "primereact/button";
import { Menubar } from "primereact/menubar";
import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";

import CurrentRequestsTemplate from "./components/CurrentRequestsTemplate";
import UserLogin from "./components/UserLogin";
import { Config } from "./models/models";
import { ClearRefresh, ClearToken } from "./services/token_service";
import { GetCurrentUser } from "./services/user_service";

function NavigationMenu({
  listeners,
  config,
  runReloadUI,
  toggleRunTour,
}: {
  listeners: Record<string, any>;
  config: Config;
  runReloadUI: () => void;
  toggleRunTour: () => void;
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

  const items = [
    {
      label: "Requests",
      template: (item: any) => {
        return (
          <NavLink to="/requests" className="p-menuitem-link">
            <span>{item.label}</span>
          </NavLink>
        );
      },
    },
    {
      label: "Scheduler",
      template: (item: any) => {
        return (
          <NavLink to="/jobs" className="p-menuitem-link">
            <span>{item.label}</span>
          </NavLink>
        );
      },
    },
    {
      label: "Workspace",
      template: (item: any) => {
        return (
          <NavLink to="/workspace" className="p-menuitem-link">
            <span>{item.label}</span>
          </NavLink>
        );
      },
    },
    {
      label: "Topics",
      template: (item: any) => {
        return (
          <NavLink to="/topics" className="p-menuitem-link">
            <span>{item.label}</span>
          </NavLink>
        );
      },
    },
    {
      label: "Users",
      template: (item: any) => {
        return (
          <NavLink to="/" className="p-menuitem-link">
            <span>{item.label}</span>
          </NavLink>
        );
      },
    },
    {
      label: "Roles",
      template: (item: any) => {
        return (
          <NavLink to="/roles" className="p-menuitem-link">
            <span>{item.label}</span>
          </NavLink>
        );
      },
    },
    {
      label: "About",
      template: (item: any) => {
        return (
          <NavLink to="/about" className="p-menuitem-link">
            <span>{item.label}</span>
          </NavLink>
        );
      },
    },
  ];

  const start = (
    <NavLink
      className="p-menuitem-link text-primary cursor-pointer px-3 py-2 overflow-hidden relative font-semibold text-lg uppercase p-ripple hover:surface-ground"
      to="/"
    >
      <div className="flex">
        <div className="mr-2">
          <FontAwesomeIcon icon={iconDefault} />
        </div>

        {applicationName && <div className="mr-2">{applicationName}</div>}
      </div>
    </NavLink>
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

  const end = (
    <div className="flex">
      {authEnabled === true && (
        <div>
          {username === undefined && (
            <div>
              <Button
                rounded
                className="mr-2"
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
            <div>
              <span className="font-bold mr-2">Welcome {username}!</span>

              <Button
                rounded
                className="mr-2"
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
      <Button
        rounded
        text
        className="mr-2"
        onClick={toggleRunTour}
        aria-label="Start Tour"
        title="Start Tour"
        data-testid="start-tour"
      >
        <FontAwesomeIcon className="fa-2x" icon="compass" />
      </Button>

      <CurrentRequestsTemplate listeners={listeners} />
    </div>
  );

  return (
    <>
      <div className="card">
        <Menubar model={items} start={start} end={end} />
      </div>
    </>
  );
}

export default NavigationMenu;
