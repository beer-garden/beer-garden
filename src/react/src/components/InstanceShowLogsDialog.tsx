import { Button } from "primereact/button";
import { Dialog } from "primereact/dialog";
import { Messages } from "primereact/messages";
import { useRef, useState } from "react";

import { Instance } from "../models/brewtils-types";
import { InstanceDialogProps } from "../models/models";
import { GetInstanceLogs } from "../services/instance_service";

function InstanceShowLogsDialog({
  instance,
  system,
  isVisible,
  onClose,
}: InstanceDialogProps) {
  const msgs = useRef<Messages>(null);

  const tailStart = useRef<number>(-20);
  const tailLine = useRef<number>(20);
  const waitTimeout = useRef<number>(30);
  const stopTailing = useRef<boolean>(false);
  const [logs, setLogs] = useState<Array<string> | undefined>(undefined);
  const [displayLogs, setDisplayLogs] = useState<string | undefined>(undefined);
  const [loadingLogs, setLoadingLogs] = useState<boolean>(false);
  const downloadHref = useRef<string>(undefined);

  const filename =
    system.name + "[" + system.version + "]-" + instance.name + ".log";

  const updateTailLineStart = (event: any) => {
    if (event.target.value > 0) {
      tailStart.current = event.target.value * -1;
    } else {
      tailStart.current = event.target.value;
    }
  };

  function successTailLogs(response: any) {
    setLoadingLogs(false);
    //let appendLogs = true;

    if (displayLogs === undefined) {
      setDisplayLogs("");
      setLogs([]);
      //appendLogs = false;
    }

    const requestId = response.headers("request_id");
    downloadHref.current = "api/v1/requests/output/" + requestId;

    let response_logs = null;

    if (typeof response.data === "string") {
      // Legacy support for log only responses
      response_logs = response.data;

      if (response_logs !== null && response_logs.length > 0) {
        tailStart.current =
          tailStart.current + response.data.match(/\n/g).length + 1;
      }
    } else {
      // New log response structure
      response_logs = response.data.logs;

      if (response_logs !== null && response_logs.length > 0) {
        tailStart.current = response.data.end_line + 1;
      }
    }

    for (let i = 0; i < response_logs.length; i++) {
      setDisplayLogs(displayLogs!.concat(response_logs[i]));
    }

    // Sleep so you don't spam the server
    if (
      (response_logs !== null && response_logs.length == 0) ||
      response_logs.match(/\n/g).length < tailLine.current
    ) {
      setTimeout(() => {
        getLogsTailLoop();
      }, 10000); // Sleep Ten seconds
    } else {
      setTimeout(() => {
        getLogsTailLoop();
      }, 1000); // Sleep One Second
    }
  }

  function addErrorAlert() {
    setLoadingLogs(false);
    msgs.current?.show({
      severity: "error",
      detail:
        "Something went wrong on the backend: Error attempting to retrieve logs - unable to determine log filename. Please verify that the plugin is writing to a log file.",
      sticky: true,
    });
  }

  function getLogsTail(instance: Instance) {
    setLoadingLogs(true);
    setDisplayLogs(undefined);
    stopTailing.current = false;

    GetInstanceLogs(
      instance,
      waitTimeout.current,
      tailStart.current,
      null,
    ).then(successTailLogs, addErrorAlert);
  }

  function stopLogsTail() {
    stopTailing.current = true;
  }

  function getLogsTailLoop() {
    if (stopTailing.current) {
      return;
    }
    GetInstanceLogs(
      instance,
      waitTimeout.current,
      tailStart.current,
      tailLine.current + tailStart.current,
    ).then((response) => successTailLogs(response), addErrorAlert);
  }

  return (
    <Dialog
      data-testid="instance-show-logs-dialog"
      header={`Log File: ${system.name}[${system.version}]-${instance.name}`}
      footer={<Button onClick={onClose}>Close Logs</Button>}
      visible={isVisible}
      style={{ width: "50vw" }}
      onShow={() => {
        msgs.current?.show({
          severity: "info",
          detail:
            "Plugin must be listening to the Admin Queue and logging to File for logs to be returned. This will only return information from the log file being actively written to.",
          sticky: true,
        });
      }}
      onHide={onClose}
    >
      <Messages ref={msgs} />
      <div>
        <div>
          <Button
            name="start"
            value="Get Tail Logs"
            onClick={() => getLogsTail(instance)}
          >
            Get Tail Logs
          </Button>
          <Button
            name="stop"
            value="Stop Tail Logs"
            onClick={() => stopLogsTail()}
          >
            Stop Tail Logs
          </Button>
          <label htmlFor="tail_line_start">Tail Lines</label>
          <input
            type="number"
            id="tail_line_start"
            min="0"
            defaultValue={20}
            name="tail_line_start"
            onChange={updateTailLineStart}
          />
        </div>
        <div>
          <a
            href={`api/v1/instances/${instance.id}/logs/?logs_only=true`}
            download={filename}
          >
            <Button>Get Full Logs</Button>
          </a>
        </div>
        {loadingLogs && (
          <div id="loading" className="col-md-12 text-center">
            <h1>
              <div>Loading...</div>
              <div>
                <i className="fa fa-spinner fa-pulse fa-2x"></i>
              </div>
            </h1>
          </div>
        )}
        {logs !== undefined && (
          <div className="container-fluid animate-if">
            <br />
            {displayLogs !== undefined && (
              <>
                <a
                  className="fa fa-download pull-right"
                  href={downloadHref.current}
                  download={filename}
                >
                  Download
                </a>
                <pre id="rawOutput" ng-show="displayLogs !== undefined">
                  {displayLogs}
                </pre>
              </>
            )}
          </div>
        )}
      </div>
    </Dialog>
  );
}

export default InstanceShowLogsDialog;
