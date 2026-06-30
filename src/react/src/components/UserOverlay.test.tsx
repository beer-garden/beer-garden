import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, test, vi } from "vitest";

import { ToastProvider } from "../providers/ToastProvider";
import * as tokenService from "../services/token_service";
import * as utilService from "../services/util_service";
import UserOverlay from "./UserOverlay";

vi.mock("../services/util_service");
vi.mock("../services/token_service");

describe("UserOverlay", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    cleanup();
  });

  //Shows expected options when anonymous access
  test("renders Overlay no user", async () => {
    render(
      <ToastProvider>
        <UserOverlay username={undefined} onLogout={() => {}} />
      </ToastProvider>,
    );

    // Check for Expected Options
    await waitFor(() => {
      expect(
        screen.getByRole("switch", { name: "Light Mode" }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("switch", { name: "Power User" }),
      ).toBeInTheDocument();
    });
  });

  //Shows expected options when logged in
  test("renders Overlay with user", async () => {
    const mockUsername = "testUser";

    render(
      <ToastProvider>
        <UserOverlay username={mockUsername} onLogout={() => {}} />
      </ToastProvider>,
    );

    // Check for Expected Options
    await waitFor(() => {
      expect(
        screen.getByText(mockUsername.charAt(0).toUpperCase()),
      ).toBeInTheDocument();
      expect(screen.getByText(mockUsername)).toBeInTheDocument();
      expect(
        screen.getByRole("switch", { name: "Light Mode" }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("switch", { name: "Power User" }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: "Change Password" }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: "Logout" }),
      ).toBeInTheDocument();
    });
  });

  test("test logout user", async () => {
    const mockUsername = "testUser";

    vi.mocked(tokenService.LogoutCurrentUser);

    render(
      <ToastProvider>
        <UserOverlay
          username={mockUsername}
          onLogout={await tokenService.LogoutCurrentUser()}
        />
      </ToastProvider>,
    );

    const logoutButton = await screen.findByTestId("user-logout-overlay");
    await userEvent.click(logoutButton);

    await waitFor(() => {
      expect(tokenService.LogoutCurrentUser).toBeCalled();
    });
  });

  // //Verify power user toggle
  test("test power user toggle", async () => {
    const mockUsername = "testUser";

    render(
      <ToastProvider>
        <UserOverlay username={mockUsername} onLogout={() => {}} />
      </ToastProvider>,
    );

    const switchPowerUser = await screen.findByRole("switch", {
      name: "Power User",
    });

    expect(switchPowerUser).not.toBeChecked();

    await userEvent.click(switchPowerUser);

    expect(switchPowerUser).toBeChecked();

    await waitFor(() => {
      expect(localStorage.getItem("user_advanced")).toBe("true");
    });
  });

  //Verify dark mode toggle
  test("test dark mode toggle", async () => {
    const mockUsername = "testUser";

    render(
      <ToastProvider>
        <UserOverlay username={mockUsername} onLogout={() => {}} />
      </ToastProvider>,
    );

    const switchMode = await screen.findByRole("switch", {
      name: "Light Mode",
    });

    expect(switchMode).not.toBeChecked();

    await userEvent.click(switchMode);

    await waitFor(() => {
      expect(switchMode).toBeChecked();
      expect(localStorage.getItem("theme_dark")).toBe("true");
      expect(screen.getByRole("switch", { name: "Dark Mode" }));
    });

    await userEvent.click(switchMode);

    await waitFor(() => {
      expect(switchMode).not.toBeChecked();
      expect(localStorage.getItem("theme_dark")).toBe("false");
      expect(screen.getByRole("switch", { name: "Light Mode" }));
    });
  });

  // Verify change theme
  test("test theme dropdown", async () => {
    const mockUsername = "testUser";

    vi.mocked(utilService.ThemeOptions).mockReturnValue([
      "amber",
      "blue",
      "cyan",
      "green",
      "indigo",
      "pink",
      "purple",
    ]);

    render(
      <ToastProvider>
        <UserOverlay username={mockUsername} onLogout={() => {}} />
      </ToastProvider>,
    );

    const colorDropdown = await screen.findByRole("combobox");
    const defaultOption = await screen.findByRole("option", {
      name: "blue",
    });
    expect(defaultOption.selected).toBe(true);
    expect(colorDropdown).toHaveValue("blue");
    expect(localStorage.getItem("theme_color")).toBe("blue");

    // TODO: Test changing dropdown
  });
});
