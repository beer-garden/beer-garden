import {
  cleanup,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, test, vi } from "vitest";

import { TourStepProps } from "../models/models";
import { SnackbarProvider } from "../providers/SnackbarProvider";
import * as permissionService from "../services/permission_service";
import * as roleService from "../services/role_service";
import RoleIndex from "./RoleIndex";

vi.mock("../services/role_service");
vi.mock("../services/permission_service");

const mockTourSteps = () => {
  const mockRef = {
    current: [] as TourStepProps[], // Mocking the value property
  };
  return mockRef as React.RefObject<TourStepProps[]>;
};

const mockRoles = [
  {
    id: "1",
    name: "plugin_admin",
    permission: "PLUGIN_ADMIN",
    scope_gardens: [],
    scope_namespaces: [],
    scope_systems: [],
    scope_instances: [],
    scope_versions: [],
    scope_commands: [],
    protected: false,
    file_generated: true,
  },
  {
    id: "2",
    name: "test",
    permission: "OPERATOR",
    scope_gardens: [],
    scope_namespaces: [],
    scope_systems: [],
    scope_instances: [],
    scope_versions: [],
    scope_commands: [],
    protected: false,
    file_generated: false,
  },
];

describe("RoleIndex", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    cleanup();
    vi.mocked(permissionService.checkPermission).mockResolvedValue(true);
  });

  // Test role page render
  test("renders role page", async () => {
    const mockRoles = [] as any;

    vi.mocked(roleService.GetRoles).mockResolvedValue(mockRoles);

    render(
      <SnackbarProvider>
        <RoleIndex config={{}} tourStepsRef={mockTourSteps()} />
      </SnackbarProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("Role Management")).toBeInTheDocument();
    });
  });

  //Test Rescan Roles
  test("calls Rescan when Rescan Roles button clicked", async () => {
    const mockRoles = [] as any;

    vi.mocked(roleService.GetRoles).mockResolvedValue(mockRoles);
    vi.mocked(roleService.Rescan).mockResolvedValue();

    render(
      <SnackbarProvider>
        <RoleIndex config={{}} tourStepsRef={mockTourSteps()} />
      </SnackbarProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("role-datatable")).toBeInTheDocument();
    });

    const rescanButton = await screen.findByTestId("rescan-btn");
    await userEvent.click(rescanButton);

    await waitFor(() => {
      expect(roleService.Rescan).toHaveBeenCalled();
    });
  });

  //Test Create Role Button
  test("calls Create when Create Role button clicked", async () => {
    const mockRoles = [] as any;

    vi.mocked(roleService.GetRoles).mockResolvedValue(mockRoles);

    render(
      <SnackbarProvider>
        <RoleIndex config={{}} tourStepsRef={mockTourSteps()} />
      </SnackbarProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("role-datatable")).toBeInTheDocument();
    });

    const createButton = await screen.findByTestId("create-btn");
    await userEvent.click(createButton);

    expect(await screen.findByRole("dialog")).toBeVisible();
  });

  //Test that roles render with correct buttons
  test("renders role page with 2 roles", async () => {
    vi.mocked(roleService.GetRoles).mockResolvedValue(mockRoles);

    render(
      <SnackbarProvider>
        <RoleIndex config={{}} tourStepsRef={mockTourSteps()} />
      </SnackbarProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("role-datatable")).toBeInTheDocument();
    });

    const table = screen.getByRole("table");
    const allRows = within(table).getAllByRole("row");
    expect(allRows.length).toBe(mockRoles.length + 1); // Add header row
  });

  //Test for row buttons
  test("Test for row buttons", async () => {
    vi.mocked(roleService.GetRoles).mockResolvedValue(mockRoles);

    render(
      <SnackbarProvider>
        <RoleIndex config={{}} tourStepsRef={mockTourSteps()} />
      </SnackbarProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("role-datatable")).toBeInTheDocument();
    });

    // Non-protected or non-file_generated should show all buttons
    const deleteButton1 = screen.queryByTestId("delete-btn-test");
    expect(deleteButton1).toBeInTheDocument();
    const editButton1 = screen.queryByTestId("edit-btn-test");
    expect(editButton1).toBeInTheDocument();
    const duplicateButton1 = screen.queryByTestId("duplicate-btn-test");
    expect(duplicateButton1).toBeInTheDocument();

    // Protected or file_generated should only show duplicate
    const deleteButton = screen.queryByTestId("delete-btn-plugin_admin");
    expect(deleteButton).not.toBeInTheDocument();
    const editButton = screen.queryByTestId("edit-btn-plugin_admin");
    expect(editButton).not.toBeInTheDocument();
    const duplicateButton = screen.queryByTestId("duplicate-btn-plugin_admin");
    expect(duplicateButton).toBeInTheDocument();
  });

  //Test duplicate
  test("Test duplicate button", async () => {
    vi.mocked(roleService.GetRoles).mockResolvedValue(mockRoles);

    render(
      <SnackbarProvider>
        <RoleIndex config={{}} tourStepsRef={mockTourSteps()} />
      </SnackbarProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("role-datatable")).toBeInTheDocument();
    });

    // Test duplicate
    await waitFor(() => {
      expect(screen.getByTestId("duplicate-btn-plugin_admin")).toBeVisible();
    });
    const duplicateButton = await screen.findByTestId(
      "duplicate-btn-plugin_admin",
    );
    await userEvent.click(duplicateButton);

    await waitFor(() => {
      expect(screen.getByTestId("role-dialog")).toBeVisible();
    });

    // Click Submit
    await waitFor(() => {
      expect(screen.getByTestId("submit-btn-dialog")).toBeVisible();
    });
    const submitButton = await screen.findByTestId("submit-btn-dialog");
    await userEvent.click(submitButton);

    // await waitFor(() => {
    //   expect(roleService.CreateRole).toHaveBeenCalled();
    // });
  });

  //Test edit
  test("Test edit button", async () => {
    vi.mocked(roleService.GetRoles).mockResolvedValue(mockRoles);
    vi.mocked(roleService.EditRole).mockResolvedValue(mockRoles[1]);

    render(
      <SnackbarProvider>
        <RoleIndex config={{}} tourStepsRef={mockTourSteps()} />
      </SnackbarProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("role-datatable")).toBeInTheDocument();
    });

    // Test edit
    await waitFor(() => {
      expect(screen.getByTestId("edit-btn-test")).toBeVisible();
    });
    const editButton = await screen.findByTestId("edit-btn-test");
    await userEvent.click(editButton);

    await waitFor(() => {
      expect(screen.getByTestId("role-dialog")).toBeVisible();
    });

    // Click Submit
    await waitFor(() => {
      expect(screen.getByTestId("submit-btn-dialog")).toBeVisible();
    });
    const submitButton = await screen.findByTestId("submit-btn-dialog");
    await userEvent.click(submitButton);

    // await waitFor(() => {
    //   expect(roleService.EditRole).toHaveBeenCalled();
    // });
  });

  //Test delete
  test("Test delete button", async () => {
    vi.mocked(roleService.GetRoles).mockResolvedValue(mockRoles);

    render(
      <SnackbarProvider>
        <RoleIndex config={{}} tourStepsRef={mockTourSteps()} />
      </SnackbarProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("role-datatable")).toBeInTheDocument();
    });

    // Test delete
    const deleteButton = await screen.findByTestId("delete-btn-test");
    await userEvent.click(deleteButton);

    await waitFor(() => {
      expect(roleService.DeleteRole).toHaveBeenCalled();
    });
  });
});
