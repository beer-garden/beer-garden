import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { ConfirmDialog } from "primereact/confirmdialog";
import { beforeEach, describe, expect, test, vi } from "vitest";

import { User } from "../models/brewtils-types";
import { Config, TourStepProps } from "../models/models";
import { SnackbarProvider } from "../providers/SnackbarProvider";
import * as permissionService from "../services/permission_service";
import * as tokenService from "../services/token_service";
import * as userService from "../services/user_service";
import UserIndex from "./UserIndex";

vi.mock("../services/user_service");
vi.mock("../services/token_service");
vi.mock("../services/permission_service");

const mockConfig: Config = { auth_enabled: false } as Config;

const mockUsers: User[] = [
  {
    id: "1",
    username: "admin",
    protected: true,
    file_generated: false,
    local_roles: [{ id: "r1", name: "Admin", permission: "GARDEN_ADMIN" }],
    upstream_roles: [],
    user_alias_mapping: [],
    metadata: { has_token: true, last_authentication: 1000000 },
  } as User,
  {
    id: "2",
    username: "operator",
    protected: false,
    file_generated: false,
    local_roles: [{ id: "r2", name: "Operator", permission: "OPERATOR" }],
    upstream_roles: [],
    user_alias_mapping: [],
    metadata: { has_token: false },
  } as User,
];

const mockTourSteps = () => {
  const mockRef = {
    current: [] as TourStepProps[], // Mocking the value property
  };
  return mockRef as React.RefObject<TourStepProps[]>;
};

describe("UserIndex", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    cleanup();
    vi.mocked(userService.GetUsers).mockResolvedValue(mockUsers);
    vi.mocked(userService.DeleteUser).mockResolvedValue();
    vi.mocked(userService.RescanUsers).mockResolvedValue();
    vi.mocked(tokenService.RevokeToken).mockResolvedValue();
    vi.mocked(permissionService.checkPermission).mockResolvedValue(true);
  });

  test("should render user management page", async () => {
    render(
      <SnackbarProvider>
        <UserIndex config={mockConfig} tourStepsRef={mockTourSteps()} />
      </SnackbarProvider>,
    );
    expect(screen.getByText("User Management")).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByTestId("user-datatable")).toBeInTheDocument();
    });
  });

  test("should load users on mount", async () => {
    render(
      <SnackbarProvider>
        <UserIndex config={mockConfig} tourStepsRef={mockTourSteps()} />
      </SnackbarProvider>,
    );
    await waitFor(() => {
      expect(userService.GetUsers).toHaveBeenCalled();
    });
  });

  test("should display users in datatable", async () => {
    render(
      <SnackbarProvider>
        <UserIndex config={mockConfig} tourStepsRef={mockTourSteps()} />
      </SnackbarProvider>,
    );
    await waitFor(() => {
      expect(screen.getByText("admin")).toBeInTheDocument();
      expect(screen.getByText("operator")).toBeInTheDocument();
    });
  });

  test("should show rescan button", () => {
    render(
      <SnackbarProvider>
        <UserIndex config={mockConfig} tourStepsRef={mockTourSteps()} />
      </SnackbarProvider>,
    );
    expect(screen.getByTestId("rescan-btn")).toBeInTheDocument();
  });

  test("should show create user button", () => {
    render(
      <SnackbarProvider>
        <UserIndex config={mockConfig} tourStepsRef={mockTourSteps()} />
      </SnackbarProvider>,
    );
    expect(screen.getByTestId("create-btn")).toBeInTheDocument();
  });

  test("should handle rescan users", async () => {
    render(
      <SnackbarProvider>
        <UserIndex config={mockConfig} tourStepsRef={mockTourSteps()} />
      </SnackbarProvider>,
    );
    const rescanBtn = screen.getByTestId("rescan-btn");
    fireEvent.click(rescanBtn);
    await waitFor(() => {
      expect(userService.RescanUsers).toHaveBeenCalled();
    });
  });

  test("should revoke user token", async () => {
    render(
      <SnackbarProvider>
        <UserIndex config={mockConfig} tourStepsRef={mockTourSteps()} />
      </SnackbarProvider>,
    );
    await waitFor(() => {
      expect(
        screen.getByTestId(`revoke-user-${mockUsers[0].id}`),
      ).toBeInTheDocument();
    });

    fireEvent.click(
      await screen.findByTestId(`revoke-user-${mockUsers[0].id}`),
    );

    await waitFor(() => {
      expect(tokenService.RevokeToken).toHaveBeenCalledWith(
        mockUsers[0].username,
      );
    });
  });

  test("should not show roles button for protected user", async () => {
    render(
      <SnackbarProvider>
        <UserIndex config={mockConfig} tourStepsRef={mockTourSteps()} />
      </SnackbarProvider>,
    );
    await waitFor(() => {
      expect(screen.queryByTestId("roles-user-1")).not.toBeInTheDocument();
    });
  });

  test("should show roles button for non-protected user", async () => {
    render(
      <SnackbarProvider>
        <UserIndex config={mockConfig} tourStepsRef={mockTourSteps()} />
      </SnackbarProvider>,
    );
    await waitFor(() => {
      expect(screen.getByTestId("roles-user-2")).toBeInTheDocument();
    });
  });

  test("should delete user", async () => {
    // Simulate ConfirmDialog in parent (i.e. App.tsx)
    render(
      <>
        <SnackbarProvider>
          <ConfirmDialog />
          <UserIndex config={mockConfig} tourStepsRef={mockTourSteps()} />
        </SnackbarProvider>
      </>,
    );
    const userTwo = mockUsers[1];

    await waitFor(() => {
      expect(
        screen.getByTestId(`delete-user-${userTwo.id}`),
      ).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId(`delete-user-${userTwo.id}`));
    // Click Yes on modal
    fireEvent.click(screen.getByRole("button", { name: /accept/i }));

    await waitFor(() => {
      expect(userService.DeleteUser).toHaveBeenCalled();
      expect(userService.DeleteUser).toHaveBeenCalledWith(userTwo.username);
    });
  });

  test("should display auth disabled warning when auth is disabled", () => {
    const disabledConfig: Config = { auth_enabled: false } as Config;
    render(
      <SnackbarProvider>
        <UserIndex config={disabledConfig} tourStepsRef={mockTourSteps()} />
      </SnackbarProvider>,
    );
    expect(
      screen.getByText(/authorization is currently disabled/i),
    ).toBeInTheDocument();
  });

  test("should show active tag for users with token", async () => {
    render(
      <SnackbarProvider>
        <UserIndex config={mockConfig} tourStepsRef={mockTourSteps()} />
      </SnackbarProvider>,
    );
    await waitFor(() => {
      const activeTags = screen.getAllByText("Active");
      expect(activeTags.length).toBeGreaterThan(0);
    });
  });

  test("should show inactive tag for users without token", async () => {
    render(
      <SnackbarProvider>
        <UserIndex config={mockConfig} tourStepsRef={mockTourSteps()} />
      </SnackbarProvider>,
    );
    await waitFor(() => {
      const inactiveTags = screen.getAllByText("Inactive");
      expect(inactiveTags.length).toBeGreaterThan(0);
    });
  });
});
