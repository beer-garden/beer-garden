import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { ButtonGroup } from "primereact/buttongroup";
import { Divider } from "primereact/divider";
import { Panel } from "primereact/panel";
import { Tag } from "primereact/tag";

import { Runner } from "../models/brewtils-types";
import { Config, RunnerGroup } from "../models/models";
import { useSnackbar } from "../providers/SnackbarProvider";
import {
  ReloadRunner,
  RemoveRunner,
  StartRunner,
  StopRunner,
} from "../services/runner_service";
import AccessButton from "./AccessButton";

function UnassociatedRunnerCard({
  runnerGroup,
  config,
}: {
  runnerGroup: RunnerGroup;
  config: Config;
}) {
  const showSnackbar = useSnackbar();

  const headerTemplate = (options: any) => {
    const className = `${options.className} justify-content-space-between`;

    return (
      <div
        className={`${className} flex align-items-center gap-2 unassociated-runner-header`}
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
        showSnackbar({
          severity: "info",
          summary: "Confirmation",
          detail: `Start runner ${runner.id}`,
          life: 3000,
        });
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
        showSnackbar({
          severity: "info",
          summary: "Confirmation",
          detail: `Stopped runner ${runner.id}`,
          life: 3000,
        });
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
        showSnackbar({
          severity: "info",
          summary: "Confirmation",
          detail: `Deleted runner ${runner.id}`,
          life: 3000,
        });
      })
      .catch((error) => {
        console.log("Error deleting runner", error);
      });
  }

  function reloadPath() {
    ReloadRunner(runnerGroup.path)
      .then(() => {
        showSnackbar({
          severity: "info",
          summary: "Confirmation",
          detail: `Reloaded runner ${runnerGroup.path}`,
          life: 3000,
        });
      })
      .catch((error) => {
        console.log("Error Reloading runner", error);
      });
  }

  const runnerActions = (runner: Runner) => {
    return (
      <div className="flex">
        <ButtonGroup>
          <AccessButton
            severity="success"
            size="small"
            title={`Start Runner ${runner.id}`}
            onClick={() => {
              startRunner(runner);
            }}
            data-testid={`START_${runner.id}`}
            config={config}
            permission="PLUGIN_ADMIN"
          >
            <FontAwesomeIcon icon="play" />
          </AccessButton>
          <AccessButton
            severity="warning"
            size="small"
            title={`Stop Runner ${runner.id}`}
            onClick={() => {
              stopRunner(runner);
            }}
            data-testid={`STOP_${runner.id}`}
            config={config}
            permission="PLUGIN_ADMIN"
          >
            <FontAwesomeIcon icon="stop" />
          </AccessButton>
          <AccessButton
            severity="danger"
            size="small"
            title={`Delete Runner ${runner.id}`}
            onClick={() => deleteRunner(runner)}
            data-testid={`DELETE_${runner.id}`}
            config={config}
            permission="PLUGIN_ADMIN"
          >
            <FontAwesomeIcon icon="trash" />
          </AccessButton>
        </ButtonGroup>
      </div>
    );
  };

  return (
    <>
      <Panel headerTemplate={headerTemplate}>
        <div className="mb-3">
          <div style={{ float: "right", marginLeft: "2px" }}>
            <ButtonGroup>
              <AccessButton
                severity="success"
                size="small"
                title={`Start runners in ../${runnerGroup.path}`}
                onClick={() => startRunnerGroup()}
                data-testid="START_GROUP"
                config={config}
                permission="PLUGIN_ADMIN"
              >
                <FontAwesomeIcon icon="play" />
              </AccessButton>
              <AccessButton
                severity="warning"
                size="small"
                title={`Stop runners in ../${runnerGroup.path}`}
                onClick={() => stopRunnerGroup()}
                data-testid="STOP_GROUP"
                config={config}
                permission="PLUGIN_ADMIN"
              >
                <FontAwesomeIcon icon="stop" />
              </AccessButton>
              <AccessButton
                severity="info"
                size="small"
                title={`Reload runners in ../${runnerGroup.path}`}
                onClick={() => reloadPath()}
                className="mr-2"
                data-testid="RELOAD_GROUP"
                config={config}
                permission="PLUGIN_ADMIN"
              >
                <FontAwesomeIcon icon="refresh" />
              </AccessButton>
            </ButtonGroup>
            <AccessButton
              severity="danger"
              size="small"
              title={`Delete runners in ../${runnerGroup.path}`}
              onClick={() => deleteRunnerGroup()}
              data-testid="DELETE_GROUP"
              config={config}
              permission="PLUGIN_ADMIN"
            >
              <FontAwesomeIcon icon="trash" />
            </AccessButton>
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
