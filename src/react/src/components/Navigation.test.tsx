import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { beforeEach, describe, expect, test, vi } from "vitest";

import { TourStepProps } from "../models/models";
import { ToastProvider } from "../providers/ToastProvider";
import * as tokenService from "../services/token_service";
import * as userService from "../services/user_service";
import Navigation from "./Navigation";

vi.mock("../services/user_service");
vi.mock("../services/token_service");

const mockTourSteps = () => {
  const mockRef = {
    current: [] as TourStepProps[], // Mocking the value property
  };
  return mockRef as React.RefObject<TourStepProps[]>;
};

describe("Navigation", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    cleanup();
  });

  test("show login", async () => {
    vi.mocked(tokenService.GetToken).mockReturnValue(null);
    vi.mocked(userService.GetCurrentUser).mockReturnValue(undefined);

    render(
      <BrowserRouter basename="/">
        <ToastProvider>
          <Navigation
            listeners={{}}
            config={{ auth_enabled: true }}
            runReloadUI={() => {}}
            toggleRunTour={() => {}}
            tourStepsRef={mockTourSteps()}
            addRequestItem={() => {}}
          />
        </ToastProvider>
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
        <ToastProvider>
          <Navigation
            listeners={{}}
            config={{
              auth_enabled: false,
            }}
            runReloadUI={() => {}}
            toggleRunTour={() => {}}
            tourStepsRef={mockTourSteps()}
            addRequestItem={() => {}}
          />
        </ToastProvider>
      </BrowserRouter>,
    );

    const loginButton = screen.queryByText("Login");

    await waitFor(() => {
      expect(loginButton).toBeNull();
      expect(loginButton).not.toBeInTheDocument();
    });
  });
});
