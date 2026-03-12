import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Button } from "primereact/button";
import { MegaMenu } from "primereact/megamenu";
import { Ripple } from "primereact/ripple";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import CurrentRequestsTemplate from "./components/CurrentRequestsTemplate";
import UserLogin from "./components/UserLogin";
import { Config } from "./models/models";
import { GetConfig } from "./services/config_service";
import { ClearRefresh, ClearToken, GetToken } from "./services/token_service";
import { GetCurrentUser } from "./services/user_service";

function NavigationMenu({ listeners }: { listeners: Record<string, any> }) {
  const [config, setConfig] = useState<Config | null>(null);

  useEffect(() => {
    GetConfig()
      .then((config) => {
        setConfig(config);
      })
      .catch((error) => {
        console.error("Error fetching the config:", error);
      });
  }, []);

  const itemRenderer = (item: any) => {
    if (item.root) {
      return (
        <Link
          className="flex align-items-center cursor-pointer px-3 py-2 overflow-hidden relative font-semibold text-lg uppercase p-ripple hover:surface-ground"
          style={{ borderRadius: "2rem" }}
          to={item.route}
        >
          {/* <FontAwesomeIcon icon={item.icon} /> */}
          <span className="ml-2">{item.label}</span>
          <Ripple />
        </Link>
      );
    } else if (!item.image) {
      return (
        <Link
          className="flex align-items-center p-3 cursor-pointer mb-2 gap-2 "
          to={item.route}
        >
          <span className="inline-flex align-items-center justify-content-center border-circle bg-primary w-3rem h-3rem">
            <FontAwesomeIcon icon={item.icon} />
          </span>
          <span className="inline-flex flex-column gap-1">
            <span className="font-medium text-lg text-900">{item.label}</span>
            <span className="white-space-nowrap">{item.subtext}</span>
          </span>
        </Link>
      );
    } else {
      return (
        <Link
          className="flex flex-column align-items-start gap-3"
          to={item.route}
        >
          <img alt="megamenu-demo" src={item.image} className="w-full" />
          <span>{item.subtext}</span>
          <Button
            className="p-button p-component p-button-outlined"
            label={item.label}
          />
        </Link>
      );
    }
  };

  const items = [
    {
      label: "Systems",
      root: true,
      template: itemRenderer,
      route: "/systems",
    },
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
      label: "Admin",
      root: true,
      template: itemRenderer,
      items: [
        [
          {
            items: [
              {
                label: "About",
                icon: "info",
                template: itemRenderer,
                route: "/about",
              },
              {
                label: "Garden",
                icon: "globe",
                template: itemRenderer,
                route: "/garden",
              },
              {
                label: "Topics",
                icon: "envelope",
                template: itemRenderer,
              },
              {
                label: "Users",
                icon: "user",
                template: itemRenderer,
              },
              {
                label: "Roles",
                icon: "users",
                template: itemRenderer,
              },
            ],
          },
        ],
      ],
    },
  ];

  const start = (
    <div className="flex">
      {config && (
        <div className="mr-2">
          <FontAwesomeIcon icon={config.icon_default ?? "beer-mug-empty"} />
        </div>
      )}
      {config && <div className="mr-2">{config.application_name}</div>}
    </div>
  );

  const getUserName = () => {
    if (config && config?.auth_enabled === true) {
      const token = GetToken();
      if (token !== null) {
        return GetCurrentUser(token);
      }
    }
    return undefined;
  };

  const [loginVisible, setLoginVisible] = useState(false);

  const [username, setUserName] = useState<string | undefined>(getUserName());

  useEffect(() => {
    if (!loginVisible) {
      setUserName(getUserName());
    }
  }, [loginVisible, config]);

  const end = (
    <div className="flex">
      {config && config?.auth_enabled === true && (
        <div>
          {username === undefined && (
            <div>
              <Button
                rounded
                className="mr-2"
                onClick={() => setLoginVisible(true)}
              >
                Login
              </Button>
              <UserLogin visible={loginVisible} setVisible={setLoginVisible} />
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
                      setUserName(undefined);
                    })
                    .catch((error) => {
                      console.error("Error clearing Refresh Token:", error);
                    });
                }}
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
