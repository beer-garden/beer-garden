import { Button } from "primereact/button";
import { Dialog } from "primereact/dialog";
import { Password } from "primereact/password";
import { Toast } from "primereact/toast";
import { ChangeEvent, RefObject, useState } from "react";

import {
  AdminUpdatePassword,
  UserUpdatePassword,
} from "../services/user_service";

function UserChangePassword({
  username,
  isAdmin,
  showPasswordDialog,
  setShowPasswordDialog,
  toast,
}: {
  username: string;
  isAdmin: boolean;
  showPasswordDialog: boolean;
  setShowPasswordDialog: (show: boolean) => void;
  toast: RefObject<Toast | null>;
}) {
  const [currentPassword, setCurrentPassword] = useState<string | undefined>(
    undefined,
  );
  const [newPassword, setNewPassword] = useState<string | undefined>(undefined);
  const [confirmPassword, setConfirmPassword] = useState<string | undefined>(
    undefined,
  );
  const [confirmPasswordInvalid, setConfirmPasswordInvalid] =
    useState<boolean>(true);

  function setPassword() {
    if (isAdmin) {
      setAdminUserPassword();
    } else {
      setUserPassword();
    }
  }

  function setAdminUserPassword() {
    if (username && newPassword && confirmPassword) {
      if (newPassword !== confirmPassword) {
        toast.current?.show({
          severity: "error",
          summary: "Error",
          detail: "Passwords do not match",
          life: 3000,
        });
        return;
      }
      AdminUpdatePassword(username, newPassword)
        .then(() => {
          toast.current?.show({
            severity: "success",
            summary: "Success",
            detail: `Password updated for user ${username}`,
            life: 3000,
          });
          handleUserPasswordDialogClose();
        })
        .catch((error) => {
          console.error("Error updating password:", error);
          toast.current?.show({
            severity: "error",
            summary: "Error",
            detail: `Failed to update password for user ${username}`,
            life: 3000,
          });
        });
    }
  }

  function setUserPassword() {
    if (currentPassword && newPassword && confirmPassword) {
      if (newPassword !== confirmPassword) {
        toast.current?.show({
          severity: "error",
          summary: "Error",
          detail: "Passwords do not match",
          life: 3000,
        });
        return;
      }
      UserUpdatePassword(newPassword, currentPassword)
        .then(() => {
          toast.current?.show({
            severity: "success",
            summary: "Success",
            detail: `Password updated for user ${username}`,
            life: 3000,
          });
          handleUserPasswordDialogClose();
        })
        .catch((error) => {
          console.error("Error updating password:", error);
          toast.current?.show({
            severity: "error",
            summary: "Error",
            detail: `Failed to update password for user ${username}`,
            life: 3000,
          });
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
      header={`Change Password for ${username}`}
      footer={
        <>
          <Button onClick={handleUserPasswordDialogClose}>Close</Button>
          <Button
            data-testid={`submit-btn-dialog`}
            severity="danger"
            onClick={setPassword}
          >
            Submit
          </Button>
        </>
      }
      visible={showPasswordDialog}
      style={{ width: "50vw" }}
      onHide={() => {
        handleUserPasswordDialogClose();
      }}
    >
      <div className="flex flex-column gap-2">
        {!isAdmin && (
          <>
            <label htmlFor="currentPassword" className="font-bold">
              Current Password
            </label>
            <Password
              toggleMask
              id="currentPassword"
              data-testid="current-password"
              className="mb-2"
              value={currentPassword}
              onChange={(e: ChangeEvent<HTMLInputElement>) =>
                setCurrentPassword(e.target.value)
              }
            />
          </>
        )}
        <label htmlFor="newPassword" className="font-bold">
          New Password
        </label>
        <Password
          toggleMask
          id="newPassword"
          data-testid="new-password"
          className="mb-2"
          value={newPassword}
          onChange={(e: ChangeEvent<HTMLInputElement>) =>
            setNewPassword(e.target.value)
          }
        />
        <label htmlFor="confirmPassword" className="font-bold">
          Confirm Password
        </label>
        <Password
          toggleMask
          id="confirmPassword"
          data-testid="confirm-password"
          invalid={confirmPasswordInvalid}
          className="mb-2"
          value={confirmPassword}
          onChange={(e: ChangeEvent<HTMLInputElement>) => {
            setConfirmPassword(e.target.value);
            setConfirmPasswordInvalid(e.target.value !== newPassword);
          }}
        />
      </div>
    </Dialog>
  );
}

export default UserChangePassword;
