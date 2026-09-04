import { Box, DialogActions, DialogContent, Grid } from "@mui/material";
import Dialog from "@mui/material/Dialog";
import DialogTitle from "@mui/material/DialogTitle";
import { ReactElement } from "react";

import AccessButton from "../components/AccessButton";
import { FAIcon } from "../services/util_service";

function ConfirmDialog({
  accept,
  reject,
  header,
  message,
  setOpen,
  open,
  closeDialog,
}: {
  accept: () => void;
  reject?: () => void;
  setOpen?: (open: boolean) => void;
  closeDialog?: () => void;
  header: string | ReactElement;
  message: string | ReactElement;
  open: boolean;
}) {
  return (
    <Dialog
      onClose={() => {
        if (setOpen) {
          setOpen(false);
          if (closeDialog) {
            closeDialog();
          }
        }
      }}
      open={open}
      aria-labelledby="confirm-dialog-title"
    >
      <DialogTitle id="confirm-dialog-title">
        <Grid container>
          <Grid size="grow">
            <Box sx={{ display: "flex" }}>
              <Box sx={{ mx: 1 }}>{header}</Box>
            </Box>
          </Grid>
          <Grid>
            <AccessButton
              onClick={() => {
                if (setOpen) {
                  setOpen(false);
                }
                if (closeDialog) {
                  closeDialog();
                }
              }}
              tooltip="Close"
            >
              <FAIcon icon="xmark" sx={{ mx: 1 }} />
            </AccessButton>
          </Grid>
        </Grid>
      </DialogTitle>
      <DialogContent sx={{ mx: 3, my: 1 }}>
        <FAIcon icon="triangle-exclamation" sx={{ mr: 1 }} /> {message}
      </DialogContent>
      <DialogActions sx={{ justifyContent: "space-between" }}>
        <AccessButton
          onClick={() => {
            accept();
            if (setOpen) {
              setOpen(false);
            }
            if (closeDialog) {
              closeDialog();
            }
          }}
          startIcon={<FAIcon icon="check" />}
          sx={{ m: 1 }}
          tooltip="Accept"
        >
          Accept
        </AccessButton>
        <AccessButton
          onClick={() => {
            if (reject) {
              reject();
            }

            if (setOpen) {
              setOpen(false);
            }
            if (closeDialog) {
              closeDialog();
            }
          }}
          startIcon={<FAIcon icon="xmark" />}
          sx={{ m: 1 }}
          tooltip="Reject"
        >
          Reject
        </AccessButton>
      </DialogActions>
    </Dialog>
  );
}

export default ConfirmDialog;
