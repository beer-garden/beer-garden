import {
  Alert,
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
import {
  AdminUpdatePassword,
  UserUpdatePassword,
} from "../services/user_service";
import { FAIcon } from "../services/util_service";
import AccessButton from "./AccessButton";

function UserChangePassword({
  username,
  isAdmin,
  showPasswordDialog,
  setShowPasswordDialog,
  callback,
}: {
  username: string;
  isAdmin: boolean;
  showPasswordDialog: boolean;
  setShowPasswordDialog: (show: boolean) => void;
  callback?: () => void;
}) {
  const showSnackbar = useSnackbar();
  const [currentPassword, setCurrentPassword] = useState<string | undefined>(
    undefined,
  );
  const [newPassword, setNewPassword] = useState<string | undefined>(undefined);
  const [confirmPassword, setConfirmPassword] = useState<string | undefined>(
    undefined,
  );
  const [confirmPasswordInvalid, setConfirmPasswordInvalid] =
    useState<boolean>(true);
  const [alertItem, setAlertItem] = useState<string | undefined>(undefined);

  function setPassword() {
    setAlertItem(undefined);
    if (isAdmin) {
      setAdminUserPassword();
    } else {
      setUserPassword();
    }
  }

  function setAdminUserPassword() {
    if (username && newPassword && confirmPassword) {
      if (newPassword !== confirmPassword) {
        setAlertItem("Passwords do not match");
        return;
      }
      AdminUpdatePassword(username, newPassword)
        .then(() => {
          if (callback) {
            callback();
          }
          handleUserPasswordDialogClose();
          showSnackbar({
            severity: "success",
            summary: "Success",
            detail: `Password updated for user ${username}`,
            life: 3000,
          });
        })
        .catch((error) => {
          console.error("Error updating password:", error);
          setAlertItem(`Failed to update password for ${username}`);
        });
    }
  }

  function setUserPassword() {
    if (currentPassword && newPassword && confirmPassword) {
      if (newPassword !== confirmPassword) {
        setAlertItem("Passwords do not match");
        return;
      }
      UserUpdatePassword(newPassword, currentPassword)
        .then(() => {
          if (callback) {
            callback();
          }
          handleUserPasswordDialogClose();
          showSnackbar({
            severity: "success",
            summary: "Success",
            detail: `Password updated for user ${username}`,
            life: 3000,
          });
        })
        .catch((error) => {
          console.error("Error updating password:", error);
          setAlertItem(`Failed to update password for ${username}`);
        });
    }
  }

  function handleUserPasswordDialogClose() {
    setCurrentPassword(undefined);
    setNewPassword(undefined);
    setConfirmPassword(undefined);
    setConfirmPasswordInvalid(true);
    setShowPasswordDialog(false);
  }

  return (
    <Dialog
      data-testid="change-password-dialog"
      open={showPasswordDialog}
      onClose={() => {
        handleUserPasswordDialogClose();
      }}
      aria-labelledby="change-password-dialog-title"
    >
      <DialogTitle id="change-password-dialog-title">
        <Grid container>
          <Grid size="grow">{`Change Password for ${username}`}</Grid>
          <Grid>
            <AccessButton
              sx={{ ml: 2 }}
              aria-label="Close change password dialog"
              onClick={handleUserPasswordDialogClose}
            >
              <FAIcon icon="xmark" />
            </AccessButton>
          </Grid>
        </Grid>
      </DialogTitle>
      {alertItem && <Alert severity="error">{alertItem}</Alert>}
      <DialogContent dividers>
        <Stack spacing={2}>
          {!isAdmin && (
            <TextField
              id="currentPassword"
              slotProps={{
                input: {
                  "aria-label": "Current Password",
                },
              }}
              label="Current Password"
              type="password"
              value={currentPassword}
              autoComplete="current-password"
              onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
                setCurrentPassword(event.target.value);
              }}
            />
          )}
          <TextField
            id="newPassword"
            slotProps={{
              input: {
                "aria-label": "New Password",
              },
            }}
            label="New Password"
            type="password"
            value={newPassword}
            autoComplete="current-password"
            onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
              setNewPassword(event.target.value);
            }}
          />
          <TextField
            id="confirmPassword"
            slotProps={{
              input: {
                "aria-label": "Confirm Password",
              },
            }}
            label="Confirm Password"
            type="password"
            value={confirmPassword}
            autoComplete="current-password"
            error={confirmPasswordInvalid}
            onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
              setConfirmPassword(event.target.value);
              setConfirmPasswordInvalid(event.target.value !== newPassword);
            }}
          />
        </Stack>
      </DialogContent>
      <DialogActions>
        <AccessButton onClick={handleUserPasswordDialogClose} label="Close">
          Close
        </AccessButton>
        <AccessButton
          data-testid={`submit-btn-dialog`}
          color="error"
          onClick={setPassword}
          label="Submit"
        >
          Submit
        </AccessButton>
      </DialogActions>
    </Dialog>
  );
}

export default UserChangePassword;
