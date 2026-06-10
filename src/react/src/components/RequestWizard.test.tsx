import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { v4 as uuidv4 } from "uuid";
import { beforeEach, describe, expect, test, vi } from "vitest";

import { System } from "../models/brewtils-types";
import { RequestItem } from "../models/models";
import { ToastProvider } from "../providers/ToastProvider";
import * as systemService from "../services/system_service";
import RequestWizard from "./RequestWizard";

vi.mock("../services/system_service");

describe("RequestWizard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    cleanup();
  });

  test("renders Request Wizard Card", async () => {
    const mockSystems = [] as System[];
    const newItem: RequestItem = {
      itemId: uuidv4(),
      type: "REQUEST",
    };

    vi.mocked(systemService.GetSystemList).mockResolvedValue(mockSystems);

    render(
      <ToastProvider>
        <RequestWizard
          requestItem={newItem}
          updateRequestItem={() => {}}
          removeItem={() => {}}
          config={{}}
          isDialog={false}
        />
      </ToastProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("Pick System")).toBeInTheDocument();
    });
  });
});
