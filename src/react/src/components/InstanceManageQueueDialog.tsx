import {
  Box,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";

import { Queue } from "../models/brewtils-types";
import { InstanceDialogProps } from "../models/models";
import { useConfirmDialog } from "../providers/ConfirmDialogProvider";
import { useSnackbar } from "../providers/SnackbarProvider";
import { ClearQueue, GetInstanceQueues } from "../services/queue_service";
import { FAIcon } from "../services/util_service";
import AccessButton from "./AccessButton";
import EnhancedTable from "./EnhancedTable/components/EnhancedTable";

function InstanceManageQueueDialog({
  instance,
  system,
  isVisible,
  onClose,
}: InstanceDialogProps) {
  const [queues, setQueues] = useState<Array<Queue>>([]);
  const showSnackbar = useSnackbar();
  const showConfirmDialog = useConfirmDialog();

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
      showConfirmDialog({
        message: "Are you sure you want to clear the Queue?",
        header: "Confirm",
        accept,
        reject,
      });
    };

    confirm();
  }

  const actionTemplate = (queue: any) => {
    return (
      <AccessButton onClick={() => clearQueue(queue.name)} label="Clear Queue">
        Clear Queue
      </AccessButton>
    );
  };

  return (
    <Dialog
      data-testid="instance-manage-queue-dialog"
      open={isVisible}
      onClose={onClose}
    >
      <DialogTitle>
        <Grid container>
          <Grid size="grow">{`Queue Manager: ${system.name}[${system.version}]-${instance.name}`}</Grid>
          <Grid>
            <AccessButton sx={{ ml: 2 }} onClick={onClose}>
              <FAIcon icon="xmark" />
            </AccessButton>
          </Grid>
        </Grid>
      </DialogTitle>
      <DialogContent>
        <EnhancedTable
          data={queues}
          displayAll={true}
          header={
            <Box sx={{ m: 2 }}>
              <Typography variant="body1" sx={{ fontWeight: "bold" }}>
                Queues
              </Typography>
            </Box>
          }
          columns={[
            {
              id: "name",
              field: "name",
              label: "Name",
            },
            {
              id: "size",
              field: "size",
              label: "Size",
            },
            {
              id: "action",
              label: "Action",
              template: actionTemplate,
            },
          ]}
        />
      </DialogContent>
      <DialogActions>
        <AccessButton onClick={onClose} label="Close">
          Close
        </AccessButton>
      </DialogActions>
    </Dialog>
  );
}

export default InstanceManageQueueDialog;
