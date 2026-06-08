import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, test, vi } from "vitest";

import { ToastProvider } from "../providers/ToastProvider";
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
      <ToastProvider>
        <UserChangePassword
          username={"username"}
          isAdmin={true}
          showPasswordDialog={true}
          setShowPasswordDialog={() => {}}
        />
      </ToastProvider>,
    );

    await waitFor(() => {
      expect(screen.queryByTestId("current-password")).not.toBeInTheDocument();
      expect(screen.getByTestId("new-password")).toBeInTheDocument();
      expect(screen.getByTestId("confirm-password")).toBeInTheDocument();
    });
  });

  test("renders user fields", async () => {
    render(
      <ToastProvider>
        <UserChangePassword
          username={"username"}
          isAdmin={false}
          showPasswordDialog={true}
          setShowPasswordDialog={() => {}}
        />
      </ToastProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("current-password")).toBeInTheDocument();
      expect(screen.getByTestId("new-password")).toBeInTheDocument();
      expect(screen.getByTestId("confirm-password")).toBeInTheDocument();
    });
  });

  test("renders invalid match password", async () => {
    render(
      <ToastProvider>
        <UserChangePassword
          username={"username"}
          isAdmin={true}
          showPasswordDialog={true}
          setShowPasswordDialog={() => {}}
        />
      </ToastProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("new-password")).toBeInTheDocument();
      expect(screen.getByTestId("confirm-password")).toBeInTheDocument();
    });

    const newPassword = await screen.findByTestId(`new-password`);
    const confirmPassword = await screen.findByTestId(`confirm-password`);

    fireEvent.change(newPassword, { target: { value: "good_password" } });
    fireEvent.change(confirmPassword, { target: { value: "bad_password" } });

    expect(confirmPassword).toHaveClass("p-invalid");
  });

  test("renders valid match password", async () => {
    render(
      <ToastProvider>
        <UserChangePassword
          username={"username"}
          isAdmin={true}
          showPasswordDialog={true}
          setShowPasswordDialog={() => {}}
        />
      </ToastProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("new-password")).toBeInTheDocument();
      expect(screen.getByTestId("confirm-password")).toBeInTheDocument();
    });

    const newPassword = await screen.findByTestId(`new-password`);
    const confirmPassword = await screen.findByTestId(`confirm-password`);

    fireEvent.change(newPassword, { target: { value: "good_password" } });
    fireEvent.change(confirmPassword, { target: { value: "good_password" } });

    expect(confirmPassword).not.toHaveClass("p-invalid");
  });

  test("renders submit admin password", async () => {
    vi.mocked(userService.AdminUpdatePassword).mockResolvedValue();

    render(
      <ToastProvider>
        <UserChangePassword
          username={"username"}
          isAdmin={true}
          showPasswordDialog={true}
          setShowPasswordDialog={() => {}}
        />
      </ToastProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("new-password")).toBeInTheDocument();
      expect(screen.getByTestId("confirm-password")).toBeInTheDocument();
    });

    const newPassword = await screen.findByTestId(`new-password`);
    const confirmPassword = await screen.findByTestId(`confirm-password`);

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
      <ToastProvider>
        <UserChangePassword
          username={"username"}
          isAdmin={false}
          showPasswordDialog={true}
          setShowPasswordDialog={() => {}}
        />
      </ToastProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("current-password")).toBeInTheDocument();
      expect(screen.getByTestId("new-password")).toBeInTheDocument();
      expect(screen.getByTestId("confirm-password")).toBeInTheDocument();
    });

    const currentPassword = await screen.findByTestId(`current-password`);
    const newPassword = await screen.findByTestId(`new-password`);
    const confirmPassword = await screen.findByTestId(`confirm-password`);

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
