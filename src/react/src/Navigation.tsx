import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Button } from "primereact/button";
import { MegaMenu } from "primereact/megamenu";
import { Ripple } from "primereact/ripple";
import { Link } from "react-router-dom";

import CurrentRequestsTemplate from "./components/CurrentRequestsTemplate";

function NavigationMenu({ listeners }: { listeners: Record<string, any> }) {
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
                subtext: "Subtext of item",
                template: itemRenderer,
                route: "/about",
              },
              {
                label: "Garden",
                icon: "globe",
                subtext: "Subtext of item",
                template: itemRenderer,
                command: () => {
                  window.open("/garden", "_self");
                },
              },
              {
                label: "Topics",
                icon: "envelope",
                subtext: "Subtext of item",
                template: itemRenderer,
              },
              {
                label: "Users",
                icon: "user",
                subtext: "Subtext of item",
                template: itemRenderer,
              },
              {
                label: "Roles",
                icon: "users",
                subtext: "Subtext of item",
                template: itemRenderer,
              },
            ],
          },
        ],
      ],
    },
  ];

  const start = <FontAwesomeIcon icon="beer-mug-empty" />;

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
