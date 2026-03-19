import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { MegaMenu } from "primereact/megamenu";
import { Ripple } from "primereact/ripple";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import CurrentRequestsTemplate from "./components/CurrentRequestsTemplate";
import { Config } from "./models/models";
import { GetConfig } from "./services/config_service";

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
      className="flex align-items-center p-3 cursor-pointer mb-2 gap-2 "
      to="/"
    >
      <div className="flex">
        {config && (
          <div className="mr-2">
            <FontAwesomeIcon icon={config.icon_default ?? "beer-mug-empty"} />
          </div>
        )}
        {config && <div className="mr-2">{config.application_name}</div>}
      </div>
    </Link>
  );

  return (
    <div className="card">
      <MegaMenu
        model={items}
        orientation="horizontal"
        start={start}
        end={<CurrentRequestsTemplate listeners={listeners} />}
        breakpoint="960px"
        className="p-3 surface-0 shadow-2"
        style={{ borderRadius: "3rem" }}
      />
    </div>
  );
}

export default NavigationMenu;
