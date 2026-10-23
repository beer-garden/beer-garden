import { Dialog } from "primereact/dialog";
import { Messages } from "primereact/messages";
import { Password } from "primereact/password";
import { ChangeEvent, useRef, useState } from "react";

import { useToast } from "../providers/ToastProvider";
import {
  AdminUpdatePassword,
  UserUpdatePassword,
} from "../services/user_service";
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
  const showToast = useToast();
  const [currentPassword, setCurrentPassword] = useState<string | undefined>(
    undefined,
  );
  const [newPassword, setNewPassword] = useState<string | undefined>(undefined);
  const [confirmPassword, setConfirmPassword] = useState<string | undefined>(
    undefined,
  );
  const [confirmPasswordInvalid, setConfirmPasswordInvalid] =
    useState<boolean>(true);
  const msgs = useRef<Messages>(null);

  function setPassword() {
    msgs.current?.clear();
    if (isAdmin) {
      setAdminUserPassword();
    } else {
      setUserPassword();
    }
  }

  function setAdminUserPassword() {
    if (username && newPassword && confirmPassword) {
      if (newPassword !== confirmPassword) {
        msgs.current?.show({
          severity: "error",
          detail: "Passwords do not match",
          sticky: true,
        });
        return;
      }
      AdminUpdatePassword(username, newPassword)
        .then(() => {
          if (callback) {
            callback();
          }
          handleUserPasswordDialogClose();
          showToast({
            severity: "success",
            summary: "Success",
            detail: `Password updated for user ${username}`,
            life: 3000,
          });
        })
        .catch((error) => {
          console.error("Error updating password:", error);
          msgs.current?.show({
            severity: "error",
            detail: `Failed to update password for ${username}`,
            sticky: true,
          });
        });
    }
  }

  function setUserPassword() {
    if (currentPassword && newPassword && confirmPassword) {
      if (newPassword !== confirmPassword) {
        msgs.current?.show({
          severity: "error",
          detail: "Passwords do not match",
          sticky: true,
        });
        return;
      }
      UserUpdatePassword(newPassword, currentPassword)
        .then(() => {
          if (callback) {
            callback();
          }
          handleUserPasswordDialogClose();
          showToast({
            severity: "success",
            summary: "Success",
            detail: `Password updated for user ${username}`,
            life: 3000,
          });
        })
        .catch((error) => {
          console.error("Error updating password:", error);
          msgs.current?.show({
            severity: "error",
            detail: `Failed to update password for ${username}`,
            sticky: true,
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
          <AccessButton onClick={handleUserPasswordDialogClose} label="Close" />
          <AccessButton
            data-testid={`submit-btn-dialog`}
            severity="danger"
            onClick={setPassword}
            label="Submit"
          />
        </>
      }
      visible={showPasswordDialog}
      style={{ width: "50vw" }}
      onHide={() => {
        handleUserPasswordDialogClose();
      }}
    >
      <Messages ref={msgs} />
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
              tooltip="Enter Current Password"
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
          tooltip="Enter New Password"
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
          tooltip="Confirm New Password"
        />
      </div>
    </Dialog>
  );
}

export default UserChangePassword;
