import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Button } from "primereact/button";
import { ConfirmDialog, confirmDialog } from "primereact/confirmdialog";
import { Dialog } from "primereact/dialog";
import { useEffect, useRef, useState } from "react";

import { Instance, Queue, System } from "../models/brewtils-types";
import { ClearQueue, GetInstanceQueues } from "../services/queue_service";

interface InstanceManageQueueDialogProps {
  instance: Instance;
  system: System;
  isVisible: boolean;
  onClose: any;
}

function InstanceManageQueueDialog({
  instance,
  system,
  isVisible,
  onClose,
}: InstanceManageQueueDialogProps) {
  const loaded = useRef<boolean>(false);
  const [queues, setQueues] = useState<Array<Queue>>([]);

  useEffect(() => {
    if (!loaded.current) {
      GetInstanceQueues(instance.id)
        .then((data: Array<Queue>) => {
          setQueues(data);
          // setQueueVisible(true);
        })
        .catch((error) => {
          console.error("Error fetching queues:", error);
        });
    }
    loaded.current = true;
  }, []);

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
        })
        .catch((error) => {
          console.error("Error clearing queue:", error);
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
      footer={<Button onClick={onClose}>Close</Button>}
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
                <ConfirmDialog message="Are you sure you want to clear the Queue?" />
                <Button onClick={() => clearQueue(queue.name)}>
                  Clear Queue
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Dialog>
  );
}

export default InstanceManageQueueDialog;
