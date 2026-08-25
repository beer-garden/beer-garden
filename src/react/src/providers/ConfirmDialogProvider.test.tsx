import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, test, vi } from "vitest";

import { ConfirmDialogProvider, useConfirmDialog } from "./ConfirmDialogProvider";

const TriggerComponent = ({ onConfirm }: { onConfirm?: () => void }) => {
  const showConfirm = useConfirmDialog();

  return (
    <button
      onClick={() =>
        showConfirm({
          accept: onConfirm ?? (() => {}),
          header: "Confirm Action",
          message: "Are you sure?",
        })
      }
    >
      Trigger
    </button>
  );
};

describe("ConfirmDialogProvider", () => {
  beforeEach(() => {
    cleanup();
  });

  test("renders children", () => {
    render(
      <ConfirmDialogProvider>
        <div data-testid="child">Child Content</div>
      </ConfirmDialogProvider>,
    );

    expect(screen.getByTestId("child")).toBeInTheDocument();
  });

  test("does not render dialog initially", () => {
    render(
      <ConfirmDialogProvider>
        <button>Trigger</button>
      </ConfirmDialogProvider>,
    );

    expect(screen.queryByText("Confirm Action")).not.toBeInTheDocument();
  });

  test("shows dialog when showConfirmDialog is called", async () => {
    render(
      <ConfirmDialogProvider>
        <TriggerComponent />
      </ConfirmDialogProvider>,
    );

    await userEvent.click(screen.getByRole("button", { name: "Trigger" }));

    expect(screen.getByText("Confirm Action")).toBeInTheDocument();
    expect(screen.getByText("Are you sure?")).toBeInTheDocument();
    expect(screen.getByText("Accept")).toBeInTheDocument();
    expect(screen.getByText("Reject")).toBeInTheDocument();
  });

  test("calls accept callback when Accept is clicked", async () => {
    const acceptCallback = vi.fn();

    render(
      <ConfirmDialogProvider>
        <TriggerComponent onConfirm={acceptCallback} />
      </ConfirmDialogProvider>,
    );

    await userEvent.click(screen.getByRole("button", { name: "Trigger" }));
    await userEvent.click(screen.getByRole("button", { name: "Accept" }));

    expect(acceptCallback).toHaveBeenCalledTimes(1);
  });

  test("closes dialog when Reject is clicked", async () => {
    render(
      <ConfirmDialogProvider>
        <TriggerComponent />
      </ConfirmDialogProvider>,
    );

    await userEvent.click(screen.getByRole("button", { name: "Trigger" }));

    expect(screen.getByText("Confirm Action")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Reject" }));

    expect(screen.queryByText("Confirm Action")).not.toBeInTheDocument();
  });

  test("closes dialog when Close is clicked", async () => {
    render(
      <ConfirmDialogProvider>
        <TriggerComponent />
      </ConfirmDialogProvider>,
    );

    await userEvent.click(screen.getByRole("button", { name: "Trigger" }));

    expect(screen.getByText("Confirm Action")).toBeInTheDocument();

    const closeButton = screen.getByLabelText("Close");
    await userEvent.click(closeButton);

    expect(screen.queryByText("Confirm Action")).not.toBeInTheDocument();
  });

  test("useConfirmDialog throws when used outside provider", () => {
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    // Suppress React error output
    expect(() => {
      render(<TriggerComponent />);
    }).toThrow("useConfirmDialog must be used within a ConfirmDialogProvider");

    consoleSpy.mockRestore();
  });
});
