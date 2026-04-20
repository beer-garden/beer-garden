import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Button } from "primereact/button";
import { Menubar } from "primereact/menubar";
import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";

import { Config } from "../models/models";
import { ClearRefresh, ClearToken } from "../services/token_service";
import { GetCurrentUser } from "../services/user_service";
import CurrentRequestsTemplate from "./CurrentRequestsTemplate";
import UserLogin from "./UserLogin";
import { Dialog } from "primereact/dialog";
import RequestCreateCard from "./RequestCreateCard";

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

  const [showCreateReqest, setShowCreateRequest] = useState<boolean>(false);


  const items = [
    {
      label: "Create Request",
      template: (item: any) => {
        return (
          <NavLink to="/requests" onClick={(e) => {e.preventDefault(); setShowCreateRequest(true);}} className="p-menuitem-link">         
            <FontAwesomeIcon className="mr-2" icon="pencil" />
            <span>{item.label}</span>       
          </NavLink>
        );
      },
    },
    {
      label: "Requests",
      template: (item: any) => {
        return (
          <NavLink to="/requests" className="p-menuitem-link">
            <FontAwesomeIcon className="mr-2" icon="file-lines" />
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
            <FontAwesomeIcon className="mr-2" icon="clock" />
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
            <FontAwesomeIcon className="mr-2" icon="toolbox" />
            <span>{item.label}</span>
          </NavLink>
        );
      },
    },
    {
      label: "Admin",
      icon: <FontAwesomeIcon className="mr-2" icon="bars" />,
      items: [
        {
          label: "Topics",
          template: (item: any) => {
            return (
              <NavLink to="/topics" className="p-menuitem-link">
                <FontAwesomeIcon className="mr-2" icon="envelope" />
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
                <FontAwesomeIcon className="mr-2" icon="users" />
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
                <FontAwesomeIcon className="mr-2" icon="user-gear" />
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
                <FontAwesomeIcon className="mr-2" icon="info" />
                <span>{item.label}</span>
              </NavLink>
            );
          },
        },
      ],
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

      <CurrentRequestsTemplate listeners={listeners} />
    </div>
  );

  return (
    <>
      {showCreateReqest && (
        <Dialog
        visible={showCreateReqest}
        style={{ width: "50vw" }}
        modal
        onHide={() => {
          setShowCreateRequest(false);
        }}
        content={() => (
          <div>

              <RequestCreateCard
                removeItem={() => {
                  setShowCreateRequest(false);
                }}
                updateRequestItem={()=>{}}
                requestItem={{itemId: 'test', type:"REQUEST"}}
              />
            
          </div>
        )}
      />
      )}
      <div className="card">
        <Menubar model={items} start={start} end={end} />
      </div>
    </>
  );
}

export default NavigationMenu;
