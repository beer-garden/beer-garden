import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Button } from "primereact/button";
import { MegaMenu } from "primereact/megamenu";
import { Ripple } from "primereact/ripple";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import CurrentRequestsTemplate from "./components/CurrentRequestsTemplate";
import UserLogin from "./components/UserLogin";
import { Config } from "./models/models";
import { ClearRefresh, ClearToken } from "./services/token_service";
import { GetCurrentUser } from "./services/user_service";

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

  const itemRenderer = (item: any) => {
    return (
      <Link
        className="flex align-items-center cursor-pointer px-3 py-2 overflow-hidden relative font-semibold text-lg uppercase p-ripple hover:surface-ground"
        style={{ borderRadius: "2rem" }}
        to={item.route}
      >
        {item.icon && <FontAwesomeIcon icon={item.icon} />}
        <span className="inline-flex flex-column gap-1">
          <span className="ml-2">{item.label}</span>
          {item.subtext && <span>{item.subtext}</span>}
        </span>
        <Ripple />
      </Link>
    );
  };

  const items = [
    {
      label: "Requests",
      root: true,
      template: itemRenderer,
      route: "/requests",
    },
    {
      label: "Scheduler",
      root: true,
      template: itemRenderer,
      route: "/jobs",
    },
    {
      label: "Create Request",
      root: true,
      template: itemRenderer,
      route: "/create/request",
    },
    {
      label: "Topics",
      root: true,
      template: itemRenderer,
    },
    {
      label: "Users",
      root: true,
      template: itemRenderer,
    },
    {
      label: "Roles",
      root: true,
      template: itemRenderer,
      route: "/roles",
    },
    {
      label: "About",
      root: true,
      template: itemRenderer,
      route: "/about",
    },
  ];

  const start = (
    <Link
      className="flex align-items-center cursor-pointer px-3 py-2 overflow-hidden relative font-semibold text-lg uppercase p-ripple hover:surface-ground"
      to="/"
    >
      <div className="flex">
        <div className="mr-2">
          <FontAwesomeIcon icon={iconDefault} />
        </div>

        {applicationName && <div className="mr-2">{applicationName}</div>}
      </div>
    </Link>
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

      <CurrentRequestsTemplate listeners={listeners} />
    </div>
  );

  return (
    <div className="card">
      <MegaMenu
        model={items}
        orientation="horizontal"
        start={start}
        end={end}
        breakpoint="960px"
        className="p-3 surface-0 shadow-2"
        style={{ borderRadius: "3rem" }}
      />
    </div>
  );
}

export default NavigationMenu;
