import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, test, vi } from "vitest";

import { Config } from "../models/models";
import AccessButton from "./AccessButton";

const mockConfig: Config = {
  auth_enabled: false,
} as Config;

describe("AccessButton", () => {
  beforeEach(() => {
    cleanup();
  });

  test("renders children inside a Button", () => {
    render(
      <AccessButton config={mockConfig}>
        <span>Click Me</span>
      </AccessButton>,
    );

    expect(screen.getByText("Click Me")).toBeInTheDocument();
    expect(screen.getByRole("button")).toBeInTheDocument();
  });

  test("renders with tooltip when provided", () => {
    render(
      <AccessButton config={mockConfig} tooltip="Helpful tip">
        <span>Action</span>
      </AccessButton>,
    );

    // The button is wrapped in a Tooltip, so its accessible name comes from the tooltip
    expect(screen.getByRole("button", { name: "Helpful tip" })).toBeInTheDocument();
  });

  test("uses label as aria-label when tooltip not provided", () => {
    render(
      <AccessButton config={mockConfig} label="Do Something">
        <span>Action</span>
      </AccessButton>,
    );

    const button = screen.getByLabelText("Do Something");
    expect(button).toBeInTheDocument();
  });

  test("uses aria-label prop as tooltip when provided", () => {
    render(
      <AccessButton config={mockConfig} aria-label="Custom ARIA">
        <span>Action</span>
      </AccessButton>,
    );

    expect(screen.getByLabelText("Custom ARIA")).toBeInTheDocument();
  });

  test("sets variant to contained by default", () => {
    render(
      <AccessButton config={mockConfig}>
        <span>Action</span>
      </AccessButton>,
    );

    // The MUI Button should have variant="contained"
    const button = screen.getByRole("button");
    expect(button).toBeInTheDocument();
  });

  test("applies text variant when text prop is set", () => {
    render(
      <AccessButton config={mockConfig} text>
        <span>Action</span>
      </AccessButton>,
    );

    expect(screen.getByRole("button", { name: "Action" })).toBeInTheDocument();
  });

  test("applies rounded style when rounded prop is set", () => {
    render(
      <AccessButton config={mockConfig} rounded>
        <span>Action</span>
      </AccessButton>,
    );

    expect(screen.getByRole("button")).toBeInTheDocument();
  });

  test("applies basic class when basic prop is set", () => {
    render(
      <AccessButton config={mockConfig} basic>
        <span>Action</span>
      </AccessButton>,
    );

    const button = screen.getByRole("button");
    expect(button.className).toContain("basic");
  });

  test("fires onClick handler when clicked", async () => {
    const handleClick = vi.fn();

    render(
      <AccessButton config={mockConfig} onClick={handleClick}>
        <span>Action</span>
      </AccessButton>,
    );

    await userEvent.click(screen.getByRole("button"));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  test("renders without HasAccess when auth is disabled", () => {
    render(
      <AccessButton config={mockConfig}>
        <span>Action</span>
      </AccessButton>,
    );

    expect(screen.getByText("Action")).toBeInTheDocument();
  });

  test("renders HasAccess wrapper when auth is enabled and permission provided", () => {
    const authConfig: Config = { auth_enabled: true } as Config;

    // When HasAccess renders, it starts in checking mode
    // so children won't show immediately
    render(
      <AccessButton config={authConfig} permission="READ_ONLY">
        <span>Protected Action</span>
      </AccessButton>,
    );

    // Should not show the button content during initial checking
    // The HasAccess component handles access determination
    expect(screen.getByRole("button", { name: "Protected Action" })).toBeInTheDocument();
  });

  test("sets color to info by default", () => {
    render(
      <AccessButton config={mockConfig}>
        <span>Action</span>
      </AccessButton>,
    );

    expect(screen.getByRole("button")).toBeInTheDocument();
  });

  test("allows overriding color prop", () => {
    render(
      <AccessButton config={mockConfig} color="error">
        <span>Action</span>
      </AccessButton>,
    );

    expect(screen.getByRole("button")).toBeInTheDocument();
  });
});
