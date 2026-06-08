import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, test, vi } from "vitest";

import { Garden, User } from "../models/brewtils-types";
import { ToastProvider } from "../providers/ToastProvider";
import * as gardenService from "../services/garden_service";
import * as userService from "../services/user_service";
import UserChangeAccountMapping from "./UserChangeAccountMapping";

vi.mock("../services/garden_service");
vi.mock("../services/user_service");

describe("UserChangeAccountMapping", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    cleanup();
  });

  test("renders provided account mapping", async () => {
    const mockGarden = {} as Garden;
    vi.mocked(gardenService.GetRootGarden).mockResolvedValue(mockGarden);

    const mockUser = {
      username: "user",
      user_alias_mapping: [
        { target_garden: "target_garden_name", username: "target_username" },
      ],
    } as User;

    render(
      <ToastProvider>
        <UserChangeAccountMapping
          config={{}}
          user={mockUser}
          showAccountMappingDialog={true}
          setShowAccountMappingDialog={() => {}}
        />
      </ToastProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("target_garden_name")).toBeInTheDocument();
      expect(screen.getByDisplayValue("target_username")).toBeInTheDocument();
    });
  });

  test("renders garden account mapping", async () => {
    const mockGarden = {
      children: [{ name: "target_garden_name" } as Garden],
    } as Garden;
    vi.mocked(gardenService.GetRootGarden).mockResolvedValue(mockGarden);

    const mockUser = {
      username: "user",
      user_alias_mapping: [],
    } as User;

    render(
      <ToastProvider>
        <UserChangeAccountMapping
          config={{}}
          user={mockUser}
          showAccountMappingDialog={true}
          setShowAccountMappingDialog={() => {}}
        />
      </ToastProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("target_garden_name")).toBeInTheDocument();
    });
  });

  test("renders change account name", async () => {
    const mockGarden = {
      children: [{ name: "target_garden_name" } as Garden],
    } as Garden;
    vi.mocked(gardenService.GetRootGarden).mockResolvedValue(mockGarden);
    vi.mocked(userService.UpdateUserAliasMapping).mockResolvedValue({} as User);

    const mockUser = {
      username: "user",
      user_alias_mapping: [],
    } as User;

    render(
      <ToastProvider>
        <UserChangeAccountMapping
          config={{}}
          user={mockUser}
          showAccountMappingDialog={true}
          setShowAccountMappingDialog={() => {}}
        />
      </ToastProvider>,
    );

    await waitFor(() => {
      expect(
        screen.getByTestId(`edit-user-account-${mockGarden.children[0].name}`),
      );
    });

    const aliasUsername = await screen.findByTestId(
      `edit-user-account-${mockGarden.children[0].name}`,
    );

    fireEvent.change(aliasUsername, { target: { value: "new_username" } });

    await waitFor(() => {
      expect(screen.getByDisplayValue("new_username")).toBeInTheDocument();
    });

    const submitButton = await screen.findByTestId(`submit-btn-dialog`);
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(userService.UpdateUserAliasMapping).toHaveBeenCalledWith(
        mockUser.username,
        [{ target_garden: "target_garden_name", username: "new_username" }],
      );
    });
  });
});
