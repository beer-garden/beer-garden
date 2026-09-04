import {
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  Stack,
} from "@mui/material";
import TextField from "@mui/material/TextField";
import { useState } from "react";

import { useSnackbar } from "../providers/SnackbarProvider";
import { CreateUser } from "../services/user_service";
import { FAIcon } from "../services/util_service";
import AccessButton from "./AccessButton";

function UserCreate({
  showCreateUserDialog,
  setShowCreateUserDialog,
  callback,
}: {
  showCreateUserDialog: boolean;
  setShowCreateUserDialog: (show: boolean) => void;
  callback?: () => void;
}) {
  const showSnackbar = useSnackbar();
  const [username, setUsername] = useState<string | undefined>(undefined);
  const [newPassword, setNewPassword] = useState<string | undefined>(undefined);
  const [confirmPassword, setConfirmPassword] = useState<string | undefined>(
    undefined,
  );
  const [confirmPasswordInvalid, setConfirmPasswordInvalid] =
    useState<boolean>(true);

  function createUser() {
    if (!username) {
      showSnackbar({
        severity: "error",
        summary: "Error",
        detail: "Missing Username",
        life: 3000,
      });
    } else if (!newPassword || !confirmPassword) {
      showSnackbar({
        severity: "error",
        summary: "Error",
        detail: "Missing Password",
        life: 3000,
      });
    } else if (newPassword !== confirmPassword) {
      showSnackbar({
        severity: "error",
        summary: "Error",
        detail: "Passwords do not match",
        life: 3000,
      });
    } else {
      CreateUser(username, newPassword)
        .then(() => {
          showSnackbar({
            severity: "info",
            summary: "Info",
            detail: `Created Account for ${username}`,
            life: 3000,
          });
          if (callback) {
            callback();
          }
          handleUserCreateDialogClose();
        })
        .catch((error) => {
          console.error("Failed creating user", error);
          showSnackbar({
            severity: "error",
            summary: "Error",
            detail: `Error creating user: ${error}`,
            life: 3000,
          });
        });
    }
  }

  function handleUserCreateDialogClose() {
    setUsername(undefined);
    setNewPassword(undefined);
    setConfirmPassword(undefined);
    setConfirmPasswordInvalid(true);
    setShowCreateUserDialog(false);
  }

  return (
    <Dialog
      data-testid="create-user-dialog"
      open={showCreateUserDialog}
      onClose={() => {
        handleUserCreateDialogClose();
      }}
      aria-labelledby="create-user-dialog-title"
    >
      <DialogTitle id="create-user-dialog-title">
        <Grid container>
          <Grid size="grow">Create User</Grid>
          <Grid>
            <AccessButton
              sx={{ mr: 2 }}
              aria-label="Close create user dialog"
              onClick={() => {
                handleUserCreateDialogClose();
              }}
            >
              <FAIcon icon="xmark" />
            </AccessButton>
          </Grid>
        </Grid>
      </DialogTitle>
      <DialogContent dividers>
        <Stack spacing={2}>
          <TextField
            id="username"
            label="Username"
            value={username}
            required
            onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
              setUsername(event.target.value);
            }}
          />
          <TextField
            id="newPassword"
            label="Password"
            type="password"
            value={newPassword}
            autoComplete="current-password"
            onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
              setNewPassword(event.target.value);
            }}
          />
          <TextField
            id="confirmPassword"
            label="Confirm Password"
            type="password"
            value={confirmPassword}
            error={confirmPasswordInvalid}
            autoComplete="current-password"
            onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
              setConfirmPassword(event.target.value);
              setConfirmPasswordInvalid(event.target.value !== newPassword);
            }}
          />
        </Stack>
      </DialogContent>
      <DialogActions sx={{ justifyContent: "center" }}>
        <AccessButton
          onClick={handleUserCreateDialogClose}
          label="Close"
          sx={{ mr: 1 }}
        >
          Close
        </AccessButton>
        <AccessButton
          data-testid={`submit-btn-dialog`}
          color="error"
          onClick={createUser}
          label="Submit"
          sx={{ mr: 1 }}
        >
          Submit
        </AccessButton>
      </DialogActions>
    </Dialog>
  );
}

export default UserCreate;
