import { Dialog } from "primereact/dialog";
import { InputText } from "primereact/inputtext";
import { Password } from "primereact/password";
import { ChangeEvent, useState } from "react";

import { useToast } from "../providers/ToastProvider";
import { CreateUser } from "../services/user_service";
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
  const showToast = useToast();
  const [username, setUsername] = useState<string | undefined>(undefined);
  const [newPassword, setNewPassword] = useState<string | undefined>(undefined);
  const [confirmPassword, setConfirmPassword] = useState<string | undefined>(
    undefined,
  );
  const [confirmPasswordInvalid, setConfirmPasswordInvalid] =
    useState<boolean>(true);

  function createUser() {
    if (!username) {
      showToast({
        severity: "error",
        summary: "Error",
        detail: "Missing Username",
        life: 3000,
      });
    } else if (!newPassword || !confirmPassword) {
      showToast({
        severity: "error",
        summary: "Error",
        detail: "Missing Password",
        life: 3000,
      });
    } else if (newPassword !== confirmPassword) {
      showToast({
        severity: "error",
        summary: "Error",
        detail: "Passwords do not match",
        life: 3000,
      });
    } else {
      CreateUser(username, newPassword)
        .then(() => {
          showToast({
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
          showToast({
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
      header={`Create User`}
      footer={
        <>
          <AccessButton onClick={handleUserCreateDialogClose} label="Close" />
          <AccessButton
            data-testid={`submit-btn-dialog`}
            severity="danger"
            onClick={createUser}
            label="Submit"
          />
        </>
      }
      visible={showCreateUserDialog}
      style={{ width: "50vw" }}
      onHide={() => {
        handleUserCreateDialogClose();
      }}
    >
      <div className="flex flex-column gap-2">
        <label htmlFor="username" className="font-bold">
          Username
        </label>
        <InputText
          id="username"
          className="mb-2"
          value={username}
          onChange={(e: ChangeEvent<HTMLInputElement>) =>
            setUsername(e.target.value)
          }
        />
        <label htmlFor="newPassword" className="font-bold">
          New Password
        </label>
        <Password
          toggleMask
          id="newPassword"
          className="mb-2"
          value={newPassword}
          onChange={(e: ChangeEvent<HTMLInputElement>) =>
            setNewPassword(e.target.value)
          }
          tooltip="Enter New Password"
        />
        <label htmlFor="confirmPassword" className="font-bold">
          Confirm Password
        </label>
        <Password
          toggleMask
          id="confirmPassword"
          invalid={confirmPasswordInvalid}
          className="mb-2"
          value={confirmPassword}
          onChange={(e: ChangeEvent<HTMLInputElement>) => {
            setConfirmPassword(e.target.value);
            setConfirmPasswordInvalid(e.target.value !== newPassword);
          }}
          tooltip="Confirm New Password"
        />
      </div>
    </Dialog>
  );
}

export default UserCreate;
