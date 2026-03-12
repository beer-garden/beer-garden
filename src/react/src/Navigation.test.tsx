import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { beforeEach, describe, expect, test, vi } from "vitest";

import Navigation from "./Navigation";
import * as tokenService from "./services/token_service";
import * as userService from "./services/user_service";

vi.mock("./services/user_service");
vi.mock("./services/token_service");

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
        <Navigation listeners={{}} />
      </BrowserRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("Logout")).toBeVisible();
      expect(screen.getByText("Welcome username123!")).toBeVisible();
    });
  });

  test("show login", async () => {
    vi.mocked(tokenService.GetToken).mockReturnValue(null);

    render(
      <BrowserRouter basename="/">
        <Navigation listeners={{}} />
      </BrowserRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("Login")).toBeVisible();
    });
  });
});
