import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Button } from "primereact/button";
import { ButtonGroup } from "primereact/buttongroup";
import { Divider } from "primereact/divider";
import { Panel } from "primereact/panel";
import { Tag } from "primereact/tag";
import { Toast } from "primereact/toast";
import { RefObject, useEffect, useState } from "react";

import { Runner } from "../models/brewtils-types";
import { RunnerGroup } from "../models/models";
import {
  ReloadRunner,
  RemoveRunner,
  StartRunner,
  StopRunner,
} from "../services/runner_service";

function UnassociatedRunnerCard({
  runnerGroup,
  toast,
}: {
  runnerGroup: RunnerGroup;
  toast?: RefObject<Toast | null>;
}) {
  const [darkMode, setDarkMode] = useState(
    localStorage.getItem("theme_dark") === "true",
  );
  const [reloadUI, setReloadUI] = useState(0);

  useEffect(() => {
    const handleStorageChange = () => {
      const newDarkMode = localStorage.getItem("theme_dark") === "true";
      if (newDarkMode !== darkMode) {
        setDarkMode(newDarkMode);
        setReloadUI(reloadUI + 1);
      }
    };
    window.addEventListener("storage", handleStorageChange);
    return () => window.removeEventListener("storage", handleStorageChange);
  }, []);

  const headerTemplate = (options: any) => {
    const className = `${options.className} justify-content-space-between`;

    const backgroundColor = darkMode ? "var(--red-900)" : "var(--red-100)";

    return (
      <div
        className={`${className} flex align-items-center gap-2`}
        style={{ backgroundColor: backgroundColor }}
      >
        <label className="max-w-20rem font-semibold">
          Unassociated Runners: {runnerGroup.path}
        </label>
      </div>
    );
  };

  function statusTemplate(runner: Runner) {
    return (
      <Tag
        value={runner.dead ? "DEAD" : "UNRESPONSIVE"}
        severity={runner.dead ? "danger" : "warning"}
      />
    );
  }

  function startRunnerGroup() {
    for (const runner of runnerGroup.runners) {
      startRunner(runner);
    }
  }

  function startRunner(runner: Runner) {
    StartRunner(runner)
      .then(() => {
        if (toast && toast.current) {
          toast.current?.show({
            severity: "info",
            summary: "Confirmation",
            detail: `Start runner ${runner.id}`,
            life: 3000,
          });
        }
      })
      .catch((error) => {
        console.log("Error starting runner", error);
      });
  }

  function stopRunnerGroup() {
    for (const runner of runnerGroup.runners) {
      stopRunner(runner);
    }
  }

  function stopRunner(runner: Runner) {
    StopRunner(runner)
      .then(() => {
        if (toast && toast.current) {
          toast.current?.show({
            severity: "info",
            summary: "Confirmation",
            detail: `Stopped runner ${runner.id}`,
            life: 3000,
          });
        }
      })
      .catch((error) => {
        console.log("Error stopping runner", error);
      });
  }

  function deleteRunnerGroup() {
    for (const runner of runnerGroup.runners) {
      deleteRunner(runner);
    }
  }

  function deleteRunner(runner: Runner) {
    RemoveRunner(runner)
      .then(() => {
        if (toast && toast.current) {
          toast.current?.show({
            severity: "info",
            summary: "Confirmation",
            detail: `Deleted runner ${runner.id}`,
            life: 3000,
          });
        }
      })
      .catch((error) => {
        console.log("Error deleting runner", error);
      });
  }

  function reloadPath() {
    ReloadRunner(runnerGroup.path)
      .then(() => {
        if (toast && toast.current) {
          toast.current?.show({
            severity: "info",
            summary: "Confirmation",
            detail: `Reloaded runner ${runnerGroup.path}`,
            life: 3000,
          });
        }
      })
      .catch((error) => {
        console.log("Error Reloading runner", error);
      });
  }

  const runnerActions = (runner: Runner) => {
    return (
      <div className="flex">
        <ButtonGroup>
          <Button
            severity="success"
            size="small"
            title={`Start Runner ${runner.id}`}
            onClick={() => {
              startRunner(runner);
            }}
            data-testid={`START_${runner.id}`}
          >
            <FontAwesomeIcon icon="play" />
          </Button>
          <Button
            severity="warning"
            size="small"
            title={`Stop Runner ${runner.id}`}
            onClick={() => {
              stopRunner(runner);
            }}
            data-testid={`STOP_${runner.id}`}
          >
            <FontAwesomeIcon icon="stop" />
          </Button>
          <Button
            severity="danger"
            size="small"
            title={`Delete Runner ${runner.id}`}
            onClick={() => deleteRunner(runner)}
            data-testid={`DELETE_${runner.id}`}
          >
            <FontAwesomeIcon icon="trash" />
          </Button>
        </ButtonGroup>
      </div>
    );
  };

  return (
    <>
      <Panel headerTemplate={headerTemplate} key={reloadUI}>
        <div className="mb-3">
          <div style={{ float: "right", marginLeft: "2px" }}>
            <ButtonGroup>
              <Button
                severity="success"
                size="small"
                title={`Start runners in ../${runnerGroup.path}`}
                onClick={() => startRunnerGroup()}
                data-testid="START_GROUP"
              >
                <FontAwesomeIcon icon="play" />
              </Button>
              <Button
                severity="warning"
                size="small"
                title={`Stop runners in ../${runnerGroup.path}`}
                onClick={() => stopRunnerGroup()}
                data-testid="STOP_GROUP"
              >
                <FontAwesomeIcon icon="stop" />
              </Button>
              <Button
                severity="info"
                size="small"
                title={`Reload runners in ../${runnerGroup.path}`}
                onClick={() => reloadPath()}
                className="mr-2"
                data-testid="RELOAD_GROUP"
              >
                <FontAwesomeIcon icon="refresh" />
              </Button>
            </ButtonGroup>
            <Button
              severity="danger"
              size="small"
              title={`Delete runners in ../${runnerGroup.path}`}
              onClick={() => deleteRunnerGroup()}
              data-testid="DELETE_GROUP"
            >
              <FontAwesomeIcon icon="trash" />
            </Button>
          </div>
          <div style={{ minHeight: "40px" }}>../{runnerGroup.path}</div>
          <Divider className="my-2" style={{ clear: "right" }} />
        </div>
        {runnerGroup.runners?.map((runner: Runner, index: number) => (
          <div key={JSON.stringify(runner)}>
            <div className="flex flex-wrap justify-content-between align-items-center">
              <div>{statusTemplate(runner)}</div>
              <div>{runner.id}</div>
              <div>{runnerActions(runner)}</div>
            </div>
            {index < runnerGroup.runners.length - 1 && (
              <Divider className="my-2" />
            )}
          </div>
        ))}
      </Panel>
    </>
  );
}

export default UnassociatedRunnerCard;
