import {
  cleanup,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, test, vi } from "vitest";


import * as userService from "./services/user_service";
import * as tokenService from "./services/token_service";
import Navigation from "./Navigation";

vi.mock("./services/user_service");
vi.mock("./services/token_service");

describe("Navigation", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    cleanup();
  });

  test("show username", async () => {
    vi.mocked(tokenService.GetToken).mockResolvedValue("data");
    vi.mocked(userService.GetCurrentUser).mockResolvedValue("username123");

    render(<Navigation listeners={{}}/>);

    await waitFor(() => {
          expect(screen.getByText("username123")).toBeVisible();
        });

  });

});
