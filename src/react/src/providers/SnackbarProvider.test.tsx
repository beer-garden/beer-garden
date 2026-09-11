import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, test, vi } from "vitest";

import { SnackbarProvider, useSnackbar } from "./SnackbarProvider";

const TriggerComponent = ({
  severity = "success",
  summary = "Test Summary",
  detail = "Test Detail",
}: {
  severity?: "success" | "info" | "warning" | "error";
  summary?: string;
  detail?: string;
}) => {
  const showSnackbar = useSnackbar();

  return (
    <button
      onClick={() => showSnackbar({ severity, summary, detail, life: 3000 })}
    >
      Trigger
    </button>
  );
};

describe("SnackbarProvider", () => {
  beforeEach(() => {
    cleanup();
  });

  test("renders children", () => {
    render(
      <SnackbarProvider>
        <div data-testid="child">Child Content</div>
      </SnackbarProvider>,
    );

    expect(screen.getByTestId("child")).toBeInTheDocument();
  });

  test("does not show snackbar initially", () => {
    render(
      <SnackbarProvider>
        <TriggerComponent />
      </SnackbarProvider>,
    );

    expect(screen.queryByText("Test Summary")).not.toBeInTheDocument();
  });

  test("shows snackbar when showSnackbar is called", async () => {
    render(
      <SnackbarProvider>
        <TriggerComponent />
      </SnackbarProvider>,
    );

    await userEvent.click(screen.getByRole("button", { name: "Trigger" }));

    await waitFor(() => {
      expect(screen.getByText("Test Summary")).toBeInTheDocument();
      expect(screen.getByText("Test Detail")).toBeInTheDocument();
    });
  });

  test("snackbar can be closed via onClose", async () => {
    render(
      <SnackbarProvider>
        <TriggerComponent />
      </SnackbarProvider>,
    );

    await userEvent.click(screen.getByRole("button", { name: "Trigger" }));

    await waitFor(() => {
      expect(screen.getByText("Test Summary")).toBeInTheDocument();
    });

    // Find the snackbar's close button and click it
    const closeButton = await screen.findByRole("button", { name: /close/i });
    await userEvent.click(closeButton);

    await waitFor(() => {
      expect(screen.queryByText("Test Summary")).not.toBeInTheDocument();
    });
  });

  test("shows error severity snackbar", async () => {
    render(
      <SnackbarProvider>
        <TriggerComponent
          severity="error"
          summary="Error!"
          detail="Something failed"
        />
      </SnackbarProvider>,
    );

    await userEvent.click(screen.getByRole("button", { name: "Trigger" }));

    await waitFor(() => {
      expect(screen.getByText("Error!")).toBeInTheDocument();
    });
  });

  test("useSnackbar throws when used outside provider", () => {
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    expect(() => {
      render(<TriggerComponent />);
    }).toThrow("useSnackbar must be used within a SnackbarProvider");

    consoleSpy.mockRestore();
  });
});
