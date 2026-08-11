import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Box, ButtonGroup, Chip, Divider } from "@mui/material";
import { grey } from "@mui/material/colors";

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

  function statusTemplate(runner: Runner) {
    return (
      <Chip
        label={runner.dead ? "DEAD" : "UNRESPONSIVE"}
        color={runner.dead ? "error" : "warning"}
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
      <Box sx={{ display: "flex" }}>
        <ButtonGroup>
          <AccessButton
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
      </Box>
    );
  };

  return (
    <>
      <Box
        sx={{
          border: "1px solid",
          borderColor: grey[300],
          m: 0,
          borderRadius: 2,
        }}
      >
        <Box sx={{ bgcolor: "error.main" }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1, p: 2 }}>
            <Box component="span" sx={{ maxWidth: "20rem", fontWeight: 600 }}>
              Unassociated Runners: {runnerGroup.path}
            </Box>
          </Box>
        </Box>
        <Divider />
        <Box sx={{ p: 2 }}>
          <Box sx={{ minHeight: "40px", float: "right", marginLeft: "2px" }}>
            <ButtonGroup>
              <AccessButton
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
                size="small"
                title={`Reload runners in ../${runnerGroup.path}`}
                onClick={() => reloadPath()}
                sx={{ mr: 2 }}
                data-testid="RELOAD_GROUP"
                config={config}
                permission="PLUGIN_ADMIN"
              >
                <FontAwesomeIcon icon="refresh" />
              </AccessButton>
            </ButtonGroup>
            <AccessButton
              size="small"
              title={`Delete runners in ../${runnerGroup.path}`}
              onClick={() => deleteRunnerGroup()}
              data-testid="DELETE_GROUP"
              config={config}
              permission="PLUGIN_ADMIN"
            >
              <FontAwesomeIcon icon="trash" />
            </AccessButton>
          </Box>
          <Box component="span">../{runnerGroup.path}</Box>
          <Divider sx={{ my: 2, clear: "right" }} />
          {runnerGroup.runners?.map((runner: Runner, index: number) => (
            <div key={JSON.stringify(runner)}>
              <Box
                sx={{
                  display: "flex",
                  flexWrap: 1,
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <div>{statusTemplate(runner)}</div>
                <div>{runner.id}</div>
                <div>{runnerActions(runner)}</div>
              </Box>
              {index < runnerGroup.runners.length - 1 && (
                <Divider sx={{ my: 1 }} />
              )}
            </div>
          ))}
        </Box>
      </Box>
    </>
  );
}

export default UnassociatedRunnerCard;
