import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { confirmDialog } from "primereact/confirmdialog";
import { Dialog } from "primereact/dialog";
import { useEffect, useState } from "react";

import { Queue } from "../models/brewtils-types";
import { InstanceDialogProps } from "../models/models";
import { useSnackbar } from "../providers/SnackbarProvider";
import { ClearQueue, GetInstanceQueues } from "../services/queue_service";
import AccessButton from "./AccessButton";

function InstanceManageQueueDialog({
  instance,
  system,
  isVisible,
  onClose,
}: InstanceDialogProps) {
  const [queues, setQueues] = useState<Array<Queue>>([]);
  const showSnackbar = useSnackbar();

  useEffect(() => {
    if (isVisible) {
      GetInstanceQueues(instance.id)
        .then((data: Array<Queue>) => {
          setQueues(data);
        })
        .catch((error) => {
          console.error("Error fetching queues:", error);
          showSnackbar({
            severity: "error",
            summary: "Error",
            detail: `Error fetching queues: ${error}`,
            life: 3000,
          });
        });
    }
  }, [isVisible]);

  function clearQueue(queueName: string | undefined) {
    const accept = () => {
      if (!queueName) {
        return;
      }
      ClearQueue(queueName)
        .then(() => {
          //QUEUE_CLEARED events do not have name to indicate the queue
          // Set to 0 on success code
          setQueues((prevQueues) => {
            const newQueues = prevQueues.map((queue) => {
              if (queue.name == queueName) {
                queue.size = 0;
              }
              return { ...queue };
            });
            return newQueues;
          });
          showSnackbar({
            severity: "success",
            summary: "Success",
            detail: `Cleared queue: ${queueName}`,
            life: 3000,
          });
        })
        .catch((error) => {
          console.error("Error clearing queue:", error);
          showSnackbar({
            severity: "error",
            summary: "Error",
            detail: `Error clearing queue: ${error}`,
            life: 3000,
          });
        });
    };

    const reject = () => {};

    const confirm = () => {
      confirmDialog({
        message: "Are you sure you want to clear the Queue?",
        header: "Confirm",
        icon: <FontAwesomeIcon icon="exclamation" />,
        defaultFocus: "accept",
        accept,
        reject,
      });
    };

    confirm();
  }

  return (
    <Dialog
      header={`Queue Manager: ${system.name}[${system.version}]-${instance.name}`}
      footer={
        <AccessButton
          onClick={onClose}
          tooltip="Close Instance Manage Queue Dialog"
          label="Close"
        >
          Close
        </AccessButton>
      }
      visible={isVisible}
      style={{ width: "50vw" }}
      onHide={onClose}
    >
      <table className="table">
        <thead>
          <tr>
            <th scope="col">Name</th>
            <th scope="col">Message Size</th>
            <th scope="col"></th>
          </tr>
        </thead>
        <tbody>
          {queues.map((queue, index) => (
            <tr key={index}>
              <td>{queue.name}</td>
              <td>{queue.size}</td>
              <td>
                <AccessButton
                  onClick={() => clearQueue(queue.name)}
                  label="Clear Queue"
                >
                  Clear Queue
                </AccessButton>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Dialog>
  );
}

export default InstanceManageQueueDialog;
