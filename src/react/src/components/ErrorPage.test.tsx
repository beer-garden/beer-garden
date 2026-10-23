import { cleanup, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, test } from "vitest";

import ErrorPage from "./ErrorPage";

describe("ErrorPage", () => {
  beforeEach(() => {
    cleanup();
  });

  test("renders default error when no errorCode provided", () => {
    render(<ErrorPage errorMsg="Something went wrong" />);

    expect(screen.getByText("Error")).toBeInTheDocument();
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
  });

  test("renders default message when no errorMsg provided", () => {
    render(<ErrorPage errorCode={500} />);

    expect(screen.getByText("500 Error")).toBeInTheDocument();
    expect(
      screen.getByText("This page isn't available. Please try something else"),
    ).toBeInTheDocument();
  });

  test("renders 404 error type", () => {
    render(<ErrorPage errorCode={404} errorMsg="Page not found" />);

    expect(screen.getByText("404 Not Found")).toBeInTheDocument();
    expect(screen.getByText("Page not found")).toBeInTheDocument();
  });

  test("renders 401 error type", () => {
    render(<ErrorPage errorCode={401} />);

    expect(screen.getByText("401 Unauthorized")).toBeInTheDocument();
  });

  test("renders 400 error type", () => {
    render(<ErrorPage errorCode={400} errorMsg="Bad request" />);

    expect(screen.getByText("400 Bad Request")).toBeInTheDocument();
    expect(screen.getByText("Bad request")).toBeInTheDocument();
  });

  test("renders generic error for unknown codes", () => {
    render(<ErrorPage errorCode={418} />);

    expect(screen.getByText("418 Error")).toBeInTheDocument();
  });

  test("renders as card when isCard is true", () => {
    render(<ErrorPage errorCode={404} isCard={true} />);

    // In card mode, the title in the header box should show the error type
    expect(screen.getByText("404 Not Found")).toBeInTheDocument();
  });

  test("renders full card with header and details when isCard and both props provided", () => {
    render(
      <ErrorPage
        errorCode={500}
        errorMsg="Internal server error"
        isCard={true}
      />,
    );

    expect(screen.getByText("500 Error")).toBeInTheDocument();
    expect(screen.getByText("Internal server error")).toBeInTheDocument();
  });
});
