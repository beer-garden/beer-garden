import { Dialog } from "primereact/dialog";
import { Messages } from "primereact/messages";
import { useRef, useState } from "react";

import { Instance } from "../models/brewtils-types";
import { InstanceDialogProps } from "../models/models";
import { GetInstanceLogs } from "../services/instance_service";
import AccessButton from "./AccessButton";

function InstanceShowLogsDialog({
  instance,
  system,
  isVisible,
  onClose,
}: InstanceDialogProps) {
  const msgs = useRef<Messages>(null);

  const tailLineStart = useRef<number>(20);
  const tailStart = useRef<number>(-20);
  const tailLine = useRef<number>(20);
  const waitTimeout = useRef<number>(30);
  const stopTailing = useRef<boolean>(false);
  const [displayLogs, setDisplayLogs] = useState<string | undefined>(undefined);
  const [loadingLogs, setLoadingLogs] = useState<boolean>(false);
  const downloadHref = useRef<string>(undefined);

  const filename =
    system.name + "[" + system.version + "]-" + instance.name + ".log";

  const updateTailLineStart = (event: any) => {
    if (event.target.value > 0) {
      tailLineStart.current = event.target.value * -1;
    } else {
      tailLineStart.current = event.target.value;
    }
  };

  function successTailLogs(response: [any, any]) {
    const data = response[0];
    const headers = response[1];

    setLoadingLogs(false);

    const requestId = headers.get("request_id");
    downloadHref.current = "api/v1/requests/output/" + requestId;

    let response_logs = null;

    if (typeof data === "string") {
      // Legacy support for log only responses
      response_logs = data;

      if (response_logs !== null && response_logs.length > 0) {
        tailStart.current =
          tailStart.current + (data.match(/\n/g) ?? "").length + 1;
      }
    } else {
      // New log response structure
      response_logs = data.logs;

      if (response_logs !== null && response_logs.length > 0) {
        tailStart.current = data.end_line + 1;
      }
    }

    setDisplayLogs((prevDisplayLogs) => {
      if (prevDisplayLogs !== undefined) {
        return prevDisplayLogs.concat(response_logs);
      } else {
        return "".concat(response_logs);
      }
    });

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

    if (tailLineStart.current > 0) {
      tailStart.current = tailLineStart.current * -1;
    } else {
      tailStart.current = tailLineStart.current;
    }

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
      header={`Log File: ${system.name}[${system.version}]-${instance.name}`}
      footer={
        <AccessButton
          onClick={onClose}
          tooltip="Close Instance Show Logs Dialog"
          label="Close Logs"
        />
      }
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
      // Framework adds hidden focusable spans. Unable to edit these
      pt={{}}
      onHide={onClose}
    >
      <Messages ref={msgs} />
      <div>
        <div>
          <AccessButton
            name="start"
            value="Get Tail Logs"
            tooltip="Get Tail logs"
            onClick={() => getLogsTail(instance)}
            label="Get Tail Logs"
          />
          <AccessButton
            name="stop"
            value="Stop Tail Logs"
            tooltip="Stop Tail Logs"
            onClick={() => stopLogsTail()}
            label="Stop Tail Logs"
          />
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
            <AccessButton
              tooltip="Download Full Logs File"
              label="Get Full Logs"
            />
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
        {displayLogs !== undefined && (
          <div className="container-fluid animate-if">
            <br />
            <>
              <a
                className="fa fa-download pull-right"
                href={downloadHref.current}
                download={filename}
                aria-label="Download Current Logs Displayed"
              >
                Download
              </a>
              <pre id="rawOutput">{displayLogs}</pre>
            </>
          </div>
        )}
      </div>
    </Dialog>
  );
}

export default InstanceShowLogsDialog;
