import { Box, DialogActions, DialogContent, Grid } from "@mui/material";
import Dialog from "@mui/material/Dialog";
import DialogTitle from "@mui/material/DialogTitle";

import AccessButton from "../components/AccessButton";
import { FAIcon } from "../services/util_service";

function ConfirmDialog({
  accept,
  reject,
  header,
  message,
  setOpen,
  open,
}: {
  accept: () => void;
  reject: () => void;
  setOpen: (open: boolean) => void;
  header: string;
  message: string;
  open: boolean;
}) {
  return (
    <Dialog onClose={() => setOpen(false)} open={open}>
      <DialogTitle>
        <Grid container>
          <Grid size="grow">
            <Box sx={{ display: "flex" }}>
              <FAIcon icon="triangle-exclamation" sx={{ ml: 1 }} />
              <Box sx={{ mx: 1 }}>{header}</Box>
            </Box>
          </Grid>
          <Grid>
            <AccessButton
              onClick={() => {
                setOpen(false);
              }}
              tooltip="Close"
            >
              <FAIcon icon="xmark" sx={{ mx: 1 }} />
            </AccessButton>
          </Grid>
        </Grid>
      </DialogTitle>
      <DialogContent sx={{ mx: 3, my: 1 }}>{message}</DialogContent>
      <DialogActions sx={{ justifyContent: "space-between" }}>
        <AccessButton
          onClick={() => {
            accept();
            setOpen(false);
          }}
          startIcon={<FAIcon icon="check" />}
          sx={{ m: 1 }}
          tooltip="Accept"
        >
          Accept
        </AccessButton>
        <AccessButton
          onClick={() => {
            reject();
            setOpen(false);
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
