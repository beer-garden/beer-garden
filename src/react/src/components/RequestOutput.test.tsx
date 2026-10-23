import { cleanup, render, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, test, vi } from "vitest";

import RequestOutput from "./RequestOutput";

describe("RequestOutput", () => {
  beforeEach(() => {
    cleanup();
  });

  test("renders skeleton when status is CREATED", async () => {
    const page = render(
      <RequestOutput
        request={{
          id: "123",
          status: "CREATED",
          output: "",
          output_type: "STRING",
        }}
      />,
    );

    await waitFor(() => {
      expect(
        page.container.querySelector("#request-output-skeleton"),
      ).toBeVisible();
    });
  });

  test("renders skeleton when status is IN_PROGRESS", async () => {
    const page = render(
      <RequestOutput
        request={{
          id: "123",
          status: "IN_PROGRESS",
          output: "",
          output_type: "STRING",
        }}
      />,
    );

    await waitFor(() => {
      expect(
        page.container.querySelector("#request-output-skeleton"),
      ).toBeVisible();
    });
  });

  test("renders undefined output when status is SUCCESS", async () => {
    const page = render(
      <RequestOutput
        request={{ id: "123", status: "SUCCESS", output: "Test output" }}
      />,
    );
    await waitFor(() => {
      expect(page.container.querySelector("#request-output")).toBeVisible();
      expect(page.getByText("Test output")).toBeVisible();
    });
  });

  test("renders STRING output when status is SUCCESS", async () => {
    const page = render(
      <RequestOutput
        request={{
          id: "123",
          status: "SUCCESS",
          output: "Test output",
          output_type: "STRING",
        }}
      />,
    );
    await waitFor(() => {
      expect(page.container.querySelector("#request-output")).toBeVisible();
      expect(page.getByText("Test output")).toBeVisible();
    });
  });

  test("renders parsed JSON output", async () => {
    const page = render(
      <RequestOutput
        request={{
          id: "123",
          status: "SUCCESS",
          output: '{"key":"value"}',
          output_type: "JSON",
        }}
      />,
    );
    await waitFor(() => {
      expect(page.container.querySelector("#request-output")).toBeVisible();
      expect(page.getByText(/key/)).toBeVisible();
    });
  });

  test("renders error message for invalid JSON", async () => {
    const page = render(
      <RequestOutput
        request={{
          id: "123",
          status: "SUCCESS",
          output: "invalid json",
          output_type: "JSON",
        }}
      />,
    );
    await waitFor(() => {
      expect(page.container.querySelector("#request-output")).toBeVisible();
      expect(page.getByText(/Failed to parse JSON/)).toBeVisible();
    });
  });

  test("renders HTML output with dangerouslySetInnerHTML", async () => {
    const page = render(
      <RequestOutput
        request={{
          id: "123",
          status: "SUCCESS",
          output: "<p>HTML content</p>",
          output_type: "HTML",
        }}
      />,
    );
    await waitFor(() => {
      expect(page.container.querySelector("#request-output")).toBeVisible();
      expect(page.getByText("HTML content")).toBeVisible();
    });
  });

  test("renders Large JSON Output with warning", async () => {
    const jsonOutput = {} as any;

    class MockBlobClass {
      data: Array<any>;
      size: number;

      constructor(data: []) {
        this.data = data;
        this.size = 50000001;
      }
    }

    vi.stubGlobal("Blob", MockBlobClass);

    const page = render(
      <RequestOutput
        request={{
          id: "123",
          status: "SUCCESS",
          output: JSON.stringify(jsonOutput),
          output_type: "JSON",
        }}
      />,
    );
    await waitFor(() => {
      expect(page.container.querySelector("#request-output")).toBeVisible();
      expect(page.getByText("Output is too large")).toBeVisible();
    });
  });

  test("renders Large String Output show Output", async () => {
    const jsonOutput = { key: "example" } as any;
    class MockBlobClass {
      data: Array<any>;
      size: number;

      constructor(data: []) {
        this.data = data;
        this.size = 50000001;
      }
    }

    vi.stubGlobal("Blob", MockBlobClass);
    const page = render(
      <RequestOutput
        request={{
          id: "123",
          status: "SUCCESS",
          output: JSON.stringify(jsonOutput),
          output_type: "JSON",
        }}
      />,
    );

    const showOutput = await page.findByTestId("request-show-output");
    await userEvent.click(showOutput);

    await waitFor(() => {
      expect(page.container.querySelector("#request-output")).toBeVisible();
      expect(page.getByText(/key/)).toBeVisible();
    });
  });
});
