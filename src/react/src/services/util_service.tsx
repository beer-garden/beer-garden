import { Dropdown } from "primereact/dropdown";
import { ChevronDownIcon } from "primereact/icons/chevrondown";
import { ChevronRightIcon } from "primereact/icons/chevronright";
import { RefObject } from "react";

import { Garden, Instance, Runner, System } from "../models/brewtils-types";
import { Version } from "../models/models";
import {
  UpdatePowerUserMode,
  UpdateUserDarkMode,
  UpdateUserTheme,
} from "./user_service";

export const CompareObjects = (obj1: any, obj2: any) => {
  if (obj1 === obj2) return true; // Check if they are the same reference

  if (typeof obj1 !== typeof obj2) return false; // Check if they are of the same type

  if (
    typeof obj1 !== "object" ||
    obj1 === null ||
    typeof obj2 !== "object" ||
    obj2 === null
  ) {
    return false; // Check if both are objects and not null
  }

  const keys1 = Object.keys(obj1);
  const keys2 = Object.keys(obj2);

  if (keys1.length !== keys2.length) return false; // Must have the same number of keys

  for (const key of keys1) {
    if (!keys2.includes(key) || !CompareObjects(obj1[key], obj2[key])) {
      return false; // Recursively check nested values
    }
  }

  return true;
};

export const GetVersion = async (): Promise<Version> => {
  try {
    const response = await fetch(`${GetBaseURL()}/version`);
    if (!response.ok) {
      // Handle non-OK responses (e.g., 404, 500)
      throw new Error(`HTTP error: Status ${response.status}`);
    }
    const data = (await response.json()) as Version;
    return data;
  } catch (error) {
    // Handle network errors or the error thrown above
    console.error("Error fetching Version:", error);
    throw error; // Re-throw to be handled by the component/hook
  }
};

export const GetBaseURL = (): string => {
  return import.meta.env.VITE_BASE_URL === "/"
    ? ""
    : import.meta.env.VITE_BASE_URL || "";
};

export const GetSeverity = (
  status?: string,
):
  | "warning"
  | "success"
  | "info"
  | "error"
  | "primary"
  | "secondary"
  | "inherit" => {
  switch (status?.toUpperCase()) {
    case "RUNNING": // Instance
    case "HEALTHY": // Connection (Summary)
    case "PUBLISHING": // Connection
    case "RECEIVING": // Connection
    case "SUCCESS": // Request
      return "success";
    case "PAUSED": // Instance
    case "STOPPED": // Instance
      return "info";
    case "INITIALIZING": // Instance
    case "STARTING": // Instance
    case "STOPPING": // Instance
    case "AWAITING_SYSTEM": // Instance
    case "DISABLED": // Connection
      return "warning";
    case "DEAD": // Instance
    case "MISSING_RUNNER": // Conditional Instance Runner Status
    case "UNASSOCIATED_RUNNER": // Runner Status
    case "UNRESPONSIVE": // Connection, Instance
    case "UNKNOWN": // Connection, Instance
    case "ERROR": // Connection, Instance, Request
    case "CANCELED": // Request
    case "INVALID": // Request
    case "NOT_CONFIGURED": // Connection
    case "MISSING_CONFIGURATION": // Connection
    case "CONFIGURATION_ERROR": // Connection
    case "UNREACHABLE": // Connection
      return "error";
    default:
      return "error";
  }
};

export const ThemeOptions = () => [
  "amber",
  "blue",
  "cyan",
  "green",
  "indigo",
  "pink",
  "purple",
];

export const ClearThemes = () => {
  ChangeTheme("blue", false);
};

export const ChangeTheme = (color?: string, dark?: boolean) => {
  if (color === undefined) {
    color = localStorage.getItem("theme_color") || "blue";
  } else {
    localStorage.setItem("theme_color", color);
  }

  if (!ThemeOptions().includes(color)) {
    color = "blue";
    localStorage.setItem("theme_color", color);
  }

  if (dark === undefined) {
    dark = localStorage.getItem("theme_dark") === "true";
  } else {
    localStorage.setItem("theme_dark", dark.toString());
  }

  const themeLink = document.getElementById("theme-link") as HTMLAnchorElement;
  if (themeLink) {
    themeLink.href = `${GetBaseURL()}/themes/lara-${dark ? "dark" : "light"}-${color}/theme.css`;
  }

  const appCSSLink = document.getElementById(
    "app-css-link",
  ) as HTMLAnchorElement;
  if (appCSSLink) {
    appCSSLink.href = `${GetBaseURL()}/src/${dark ? "dark" : "light"}.css`;
  }

  UpdateUserTheme(color).catch((error) => {
    console.error("Error updating user theme:", error);
  });
  UpdateUserDarkMode(dark).catch((error) => {
    console.error("Error updating user dark mode:", error);
  });
};

export const ChangePowerUser = (powerUser?: boolean) => {
  if (powerUser === undefined) {
    powerUser = localStorage.getItem("user_advanced") === "true";
  } else {
    localStorage.setItem("user_advanced", powerUser.toString());
  }

  UpdatePowerUserMode(powerUser).catch((error) => {
    console.error("Error updating power user mode:", error);
  });
};

const getInstanceStatus = (
  instance: Instance,
  associatedRunners: RefObject<Runner[] | undefined>,
): string => {
  if (instance.metadata?.runner_id && associatedRunners.current) {
    for (const runner of associatedRunners.current) {
      if (runner.id === instance.metadata?.runner_id) {
        if (runner.dead) {
          return "DEAD";
        }
        return instance.status ?? "UNKNOWN";
      }
    }
  }
  return "MISSING_RUNNER";
};

export const GenerateStatusCounts = (
  gardenRef: RefObject<Garden | undefined>,
  associatedRunners: RefObject<Runner[] | undefined>,
  garden: Garden,
  systems: System[] | undefined,
) => {
  // Pre Sort statuses to ensure consistent ordering in the UI
  const statusCounts = new Map([
    // Severity success
    ["RUNNING", 0],
    // Severity info
    ["PAUSED", 0],
    ["STOPPED", 0],
    // Severity warning
    ["INITIALIZING", 0],
    ["STARTING", 0],
    ["STOPPING", 0],
    ["AWAITING_SYSTEM", 0],
    // Severity danger
    ["DEAD", 0],
    ["UNRESPONSIVE", 0],
    ["UNKNOWN", 0],
    ["ERROR", 0],
    ["UNASSOCIATED_RUNNER", 0],
  ]);

  if (systems && systems.length > 0) {
    for (const system of systems.filter(
      (sys) => sys.garden_name === garden.name,
    )) {
      system?.instances?.forEach((instance: Instance) => {
        if (instance.status) {
          if (!system.local || associatedRunners?.current === undefined) {
            statusCounts.set(
              instance.status,
              (statusCounts.get(instance.status) || 0) + 1,
            );
          } else {
            const status = getInstanceStatus(instance, associatedRunners);
            statusCounts.set(status, (statusCounts.get(status) || 0) + 1);
          }
        }
      });
    }
  }

  if (
    gardenRef?.current &&
    garden.name === gardenRef.current.name &&
    associatedRunners?.current &&
    associatedRunners.current.length > 0
  ) {
    for (const runner of associatedRunners.current) {
      let isUnassociated = true;
      if (systems) {
        if (
          systems.some((system) => {
            if (system.instances) {
              return system.instances.some(
                (instance) => instance?.metadata?.runner_id === runner.id,
              );
            }
            return false;
          })
        ) {
          isUnassociated = false;
        }
      }
      if (isUnassociated) {
        statusCounts.set(
          "UNASSOCIATED_RUNNER",
          (statusCounts.get("UNASSOCIATED_RUNNER") || 0) + 1,
        );
      }
    }
  }

  return statusCounts;
};

export const getErrorCode = (errorMsg: string) => {
  if (errorMsg) {
    const regex = /HTTP error: Status (\d+)/;
    if (regex.test(errorMsg)) {
      const match = errorMsg.match(regex);
      if (match) {
        return parseInt(match[1]);
      }
    }
  }
};

export const PaginatorTemplate = {
  layout:
    "FirstPageLink PrevPageLink NextPageLink PageLinks LastPageLink RowsPerPageDropdown CurrentPageReport",
  RowsPerPageDropdown: (options: any) => {
    return (
      <>
        <datalist id="rowsPerPageDropdownOptions" aria-hidden="true">
          {options?.options?.map((status: any) => (
            <option key={status.label} value={status.value} />
          ))}
        </datalist>
        <Dropdown
          dropdownIcon={(opts) => {
            const iconProps = opts?.iconProps as any;
            return iconProps["data-pr-overlay-visible"] ? (
              <ChevronRightIcon
                {...iconProps}
                role="img"
                aria-label="Collapse page length selection"
              />
            ) : (
              <ChevronDownIcon
                {...iconProps}
                role="img"
                aria-label="Expand page length selection"
              />
            );
          }}
          value={options.value}
          options={options.options}
          onChange={options.onChange}
          pt={{
            input: {
              autoComplete: "off",
              "aria-label": "Dropdown page length",
            },
            select: {
              autoComplete: "off",
              "aria-controls": "rowsPerPageDropdownOptions",
              "aria-label": "Select page length",
            },
            trigger: { "aria-label": "Open Dropdown for page length" },
          }}
        />
      </>
    );
  },
};
