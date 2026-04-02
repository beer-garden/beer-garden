import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { beforeEach, describe, expect, test, vi } from "vitest";

import * as tokenService from "../services/token_service";
import * as userService from "../services/user_service";
import NavigationMenu from "./NavigationMenu";

vi.mock("../services/user_service");
vi.mock("../services/token_service");

describe("Navigation", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    cleanup();
  });

  test("show username", async () => {
    vi.mocked(tokenService.GetToken).mockReturnValue("token");
    vi.mocked(userService.GetCurrentUser).mockReturnValue("username123");

    render(
      <BrowserRouter basename="/">
        <NavigationMenu
          listeners={{}}
          config={{
            auth_enabled: true,
          }}
          runReloadUI={() => {}}
        />
      </BrowserRouter>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("user-logout")).toBeInTheDocument();
      expect(screen.getByText("Welcome username123!")).toBeVisible();
    });
  });

  test("show login", async () => {
    vi.mocked(tokenService.GetToken).mockReturnValue(null);
    vi.mocked(userService.GetCurrentUser).mockReturnValue(undefined);

    render(
      <BrowserRouter basename="/">
        <NavigationMenu
          listeners={{}}
          config={{ auth_enabled: true }}
          runReloadUI={() => {}}
        />
      </BrowserRouter>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("user-login")).toBeInTheDocument();
    });
  });

  test("disable login", async () => {
    vi.mocked(tokenService.GetToken).mockReturnValue(null);

    render(
      <BrowserRouter basename="/">
        <NavigationMenu
          listeners={{}}
          config={{
            auth_enabled: false,
          }}
          runReloadUI={() => {}}
        />
      </BrowserRouter>,
    );

    const loginButton = screen.queryByText("Login");

    await waitFor(() => {
      expect(loginButton).toBeNull();
      expect(loginButton).not.toBeInTheDocument();
    });
  });
});
