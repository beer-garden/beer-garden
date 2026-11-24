import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, test, vi } from "vitest";

import { SnackbarProvider } from "../providers/SnackbarProvider";
import * as userService from "../services/user_service";
import UserChangePassword from "./UserChangePassword";

vi.mock("../services/user_service");

describe("UserChangePassword", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    cleanup();
  });

  test("renders admin fields", async () => {
    render(
      <SnackbarProvider>
        <UserChangePassword
          username={"username"}
          isAdmin={true}
          showPasswordDialog={true}
          setShowPasswordDialog={() => {}}
        />
      </SnackbarProvider>,
    );

    await waitFor(() => {
      expect(
        screen.queryByLabelText("Current Password"),
      ).not.toBeInTheDocument();
      expect(screen.queryByLabelText("New Password")).toBeInTheDocument();
      expect(screen.queryByLabelText("Confirm Password")).toBeInTheDocument();
    });
  });

  test("renders user fields", async () => {
    render(
      <SnackbarProvider>
        <UserChangePassword
          username={"username"}
          isAdmin={false}
          showPasswordDialog={true}
          setShowPasswordDialog={() => {}}
        />
      </SnackbarProvider>,
    );

    await waitFor(() => {
      expect(screen.getAllByLabelText("Current Password").length).toBe(1);
      expect(screen.getAllByLabelText("New Password").length).toBe(1);
      expect(screen.getAllByLabelText("Confirm Password").length).toBe(1);
    });
  });

  test("renders invalid match password", async () => {
    render(
      <SnackbarProvider>
        <UserChangePassword
          username={"username"}
          isAdmin={true}
          showPasswordDialog={true}
          setShowPasswordDialog={() => {}}
        />
      </SnackbarProvider>,
    );

    await waitFor(() => {
      expect(screen.getAllByLabelText("New Password").length).toBe(1);
      expect(screen.getAllByLabelText("Confirm Password").length).toBe(1);
    });

    const newPassword = await screen.findByLabelText(`New Password`);
    const confirmPassword = await screen.findByLabelText(`Confirm Password`);

    fireEvent.change(newPassword, { target: { value: "good_password" } });
    fireEvent.change(confirmPassword, { target: { value: "bad_password" } });

    expect(confirmPassword).toHaveAttribute("aria-invalid", "true");
  });

  test("renders valid match password", async () => {
    render(
      <SnackbarProvider>
        <UserChangePassword
          username={"username"}
          isAdmin={true}
          showPasswordDialog={true}
          setShowPasswordDialog={() => {}}
        />
      </SnackbarProvider>,
    );

    await waitFor(() => {
      expect(screen.getAllByLabelText("New Password").length).toBe(1);
      expect(screen.getAllByLabelText("Confirm Password").length).toBe(1);
    });

    const newPassword = await screen.findByLabelText(`New Password`);
    const confirmPassword = await screen.findByLabelText(`Confirm Password`);

    fireEvent.change(newPassword, { target: { value: "good_password" } });
    fireEvent.change(confirmPassword, { target: { value: "good_password" } });

    expect(confirmPassword).not.toHaveClass("p-invalid");
  });

  test("renders submit admin password", async () => {
    vi.mocked(userService.AdminUpdatePassword).mockResolvedValue();

    render(
      <SnackbarProvider>
        <UserChangePassword
          username={"username"}
          isAdmin={true}
          showPasswordDialog={true}
          setShowPasswordDialog={() => {}}
        />
      </SnackbarProvider>,
    );

    await waitFor(() => {
      expect(screen.getAllByLabelText("New Password").length).toBe(1);
      expect(screen.getAllByLabelText("Confirm Password").length).toBe(1);
    });

    const newPassword = await screen.findByLabelText(`New Password`);
    const confirmPassword = await screen.findByLabelText(`Confirm Password`);

    fireEvent.change(newPassword, { target: { value: "good_password" } });
    fireEvent.change(confirmPassword, { target: { value: "good_password" } });

    const submitButton = await screen.findByTestId(`submit-btn-dialog`);
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(userService.AdminUpdatePassword).toHaveBeenCalledWith(
        "username",
        "good_password",
      );
    });
  });

  test("renders submit user password", async () => {
    vi.mocked(userService.UserUpdatePassword).mockResolvedValue();

    render(
      <SnackbarProvider>
        <UserChangePassword
          username={"username"}
          isAdmin={false}
          showPasswordDialog={true}
          setShowPasswordDialog={() => {}}
        />
      </SnackbarProvider>,
    );

    await waitFor(() => {
      expect(screen.getAllByLabelText("Current Password").length).toBe(1);
      expect(screen.getAllByLabelText("New Password").length).toBe(1);
      expect(screen.getAllByLabelText("Confirm Password").length).toBe(1);
    });

    const currentPassword = await screen.findByLabelText(`Current Password`);
    const newPassword = await screen.findByLabelText(`New Password`);
    const confirmPassword = await screen.findByLabelText(`Confirm Password`);

    fireEvent.change(currentPassword, { target: { value: "old_password" } });
    fireEvent.change(newPassword, { target: { value: "good_password" } });
    fireEvent.change(confirmPassword, { target: { value: "good_password" } });

    const submitButton = await screen.findByTestId(`submit-btn-dialog`);
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(userService.UserUpdatePassword).toHaveBeenCalledWith(
        "good_password",
        "old_password",
      );
    });
  });
});
