import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, test, vi } from "vitest";

import { Role, User } from "../models/brewtils-types";
import { SnackbarProvider } from "../providers/SnackbarProvider";
import * as roleService from "../services/role_service";
import * as userService from "../services/user_service";
import UserChangeRoles from "./UserChangeRoles";

vi.mock("../services/user_service");
vi.mock("../services/role_service");

describe("UserChangeRoles", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    cleanup();
  });

  test("renders Roles", async () => {
    const mockRoles = [
      {
        name: "protected_role",
        permission: "GARDEN_ADMIN",
        protected: true,
        file_generated: false,
        description: "Protected Garden Admin Role",
        id: "123",
      },
      {
        name: "file_role",
        permission: "PLUGIN_ADMIN",
        protected: false,
        file_generated: true,
        description: "File Generated Plugin Admin Role",
        id: "456",
      },
      {
        name: "operator_role",
        permission: "OPERATOR",
        protected: false,
        file_generated: false,
        description: "Operator Role",
        id: "789",
      },
    ] as Role[];
    vi.mocked(roleService.GetRoles).mockResolvedValue(mockRoles);

    const mockUser = {
      username: "user",
    } as User;

    render(
      <SnackbarProvider>
        <UserChangeRoles
          user={mockUser}
          showRolesDialog={true}
          setShowRolesDialog={() => {}}
        />
      </SnackbarProvider>,
    );
    // Check for Roles
    await waitFor(() => {
      expect(screen.getByText("protected_role")).toBeInTheDocument();
      expect(screen.getByText("file_role")).toBeInTheDocument();
      expect(screen.getByText("operator_role")).toBeInTheDocument();
    });

    // Check for check boxes (div and input)
    // Row Selected === Unchecked
    // Row Unselected === Checked
    await waitFor(() => {
      expect(screen.getAllByLabelText("Row Selected 123").length).toBe(2);
      expect(screen.getAllByLabelText("Row Selected 456").length).toBe(2);
      expect(screen.getAllByLabelText("Row Selected 789").length).toBe(2);
    });
  });

  test("renders Selected Roles", async () => {
    const mockRoles = [
      {
        name: "protected_role",
        permission: "GARDEN_ADMIN",
        protected: true,
        file_generated: false,
        description: "Protected Garden Admin Role",
        id: "123",
      },
      {
        name: "file_role",
        permission: "PLUGIN_ADMIN",
        protected: false,
        file_generated: true,
        description: "File Generated Plugin Admin Role",
        id: "456",
      },
      {
        name: "operator_role",
        permission: "OPERATOR",
        protected: false,
        file_generated: false,
        description: "Operator Role",
        id: "789",
      },
    ] as Role[];
    vi.mocked(roleService.GetRoles).mockResolvedValue(mockRoles);

    const mockUser = {
      username: "user",
      local_roles: [
        {
          name: "operator_role",
          permission: "OPERATOR",
          protected: false,
          file_generated: false,
          description: "Operator Role",
          id: "789",
        },
      ],
    } as User;

    render(
      <SnackbarProvider>
        <UserChangeRoles
          user={mockUser}
          showRolesDialog={true}
          setShowRolesDialog={() => {}}
        />
      </SnackbarProvider>,
    );
    // Check for Roles
    await waitFor(() => {
      expect(screen.getByText("protected_role")).toBeInTheDocument();
      expect(screen.getByText("file_role")).toBeInTheDocument();
      expect(screen.getByText("operator_role")).toBeInTheDocument();
    });

    // Check for check boxes (div and input)
    // Row Selected === Unchecked
    // Row Unselected === Checked
    await waitFor(() => {
      expect(screen.getAllByLabelText("Row Selected 123").length).toBe(2);
      expect(screen.getAllByLabelText("Row Selected 456").length).toBe(2);
      expect(screen.getAllByLabelText("Row Unselected 789").length).toBe(2);
    });
  });

  test("renders Update Roles", async () => {
    const mockRoles = [
      {
        name: "protected_role",
        permission: "GARDEN_ADMIN",
        protected: true,
        file_generated: false,
        description: "Protected Garden Admin Role",
        id: "123",
      },
      {
        name: "file_role",
        permission: "PLUGIN_ADMIN",
        protected: false,
        file_generated: true,
        description: "File Generated Plugin Admin Role",
        id: "456",
      },
      {
        name: "operator_role",
        permission: "OPERATOR",
        protected: false,
        file_generated: false,
        description: "Operator Role",
        id: "789",
      },
    ] as Role[];
    vi.mocked(roleService.GetRoles).mockResolvedValue(mockRoles);
    vi.mocked(userService.UpdateUserRoles).mockResolvedValue({});

    const mockUser = {
      username: "user",
      local_roles: [
        {
          name: "operator_role",
          permission: "OPERATOR",
          protected: false,
          file_generated: false,
          description: "Operator Role",
          id: "789",
        },
      ],
    } as User;

    render(
      <SnackbarProvider>
        <UserChangeRoles
          user={mockUser}
          showRolesDialog={true}
          setShowRolesDialog={() => {}}
        />
      </SnackbarProvider>,
    );
    // Check for Roles
    await waitFor(() => {
      expect(screen.getByText("protected_role")).toBeInTheDocument();
      expect(screen.getByText("file_role")).toBeInTheDocument();
      expect(screen.getByText("operator_role")).toBeInTheDocument();
    });

    // Check for check boxes (div and input)
    // Row Selected === Unchecked
    // Row Unselected === Checked
    await waitFor(() => {
      expect(screen.getAllByLabelText("Row Selected 123").length).toBe(2);
      expect(screen.getAllByLabelText("Row Selected 456").length).toBe(2);
      expect(screen.getAllByLabelText("Row Unselected 789").length).toBe(2);
    });

    const fileRoleCheckbox =
      await screen.findAllByLabelText("Row Selected 456");

    await userEvent.click(fileRoleCheckbox[1]);

    await waitFor(() => {
      expect(screen.getAllByLabelText("Row Selected 123").length).toBe(2);
      expect(screen.getAllByLabelText("Row Unselected 456").length).toBe(2);
      expect(screen.getAllByLabelText("Row Unselected 789").length).toBe(2);
    });

    const submitButton = await screen.findByTestId(`submit-btn-dialog`);
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(userService.UpdateUserRoles).toBeCalledWith(mockUser.username, [
        "operator_role",
        "file_role",
      ]);
    });
  });
});
