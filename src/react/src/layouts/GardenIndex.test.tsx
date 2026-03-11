import {
  cleanup,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, test, vi } from "vitest";

import { Config } from "../models/models";
import * as configService from "../services/config_service";
import * as gardenService from "../services/garden_service";
import * as queueService from "../services/queue_service";
import * as systemService from "../services/system_service";
import GardenTable from "./GardenIndex";

vi.mock("../services/garden_service");
vi.mock("../services/config_service");
vi.mock("../services/system_service");
vi.mock("../services/queue_service");

describe("GardenTable", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    cleanup();
  });

  test("renders garden table", async () => {
    const mockConfig = { garden_name: "Root" } as Config;
    const mockGarden = {
      id: "1",
      name: "Root",
      version: "1.0.0",
      children: [],
      receiving_connections: [],
      publishing_connections: [],
    };

    vi.mocked(configService.GetConfig).mockResolvedValue(mockConfig);
    vi.mocked(gardenService.GetRootGarden).mockResolvedValue(mockGarden);

    render(<GardenTable listeners={{}} />);

    await waitFor(() => {
      expect(screen.getByText("Sync All")).toBeInTheDocument();
    });
  });

  test("fetches root garden on mount", async () => {
    const mockConfig = { garden_name: "Root" } as Config;
    const mockGarden = {
      id: "1",
      name: "Root Garden",
      version: "1.0.0",
      children: [],
      receiving_connections: [],
      publishing_connections: [],
    };

    vi.mocked(configService.GetConfig).mockResolvedValue(mockConfig);
    vi.mocked(gardenService.GetRootGarden).mockResolvedValue(mockGarden);

    render(<GardenTable listeners={{}} />);

    await waitFor(() => {
      expect(configService.GetConfig).toHaveBeenCalled();
      expect(gardenService.GetRootGarden).toHaveBeenCalledWith(mockConfig, {});
    });
  });

  test("calls SyncGarden when Sync All button clicked", async () => {
    const mockConfig = { garden_name: "Root" } as Config;
    const mockGarden = {
      id: "1",
      name: "Root Garden",
      version: "1.0.0",
      children: [],
      receiving_connections: [],
      publishing_connections: [],
    };

    vi.mocked(configService.GetConfig).mockResolvedValue(mockConfig);
    vi.mocked(gardenService.GetRootGarden).mockResolvedValue(mockGarden);
    vi.mocked(gardenService.SyncGarden).mockResolvedValue(mockGarden);

    render(<GardenTable listeners={{}} />);

    const syncButton = await screen.findByText("Sync All");
    await userEvent.click(syncButton);

    await waitFor(() => {
      expect(gardenService.SyncGarden).toHaveBeenCalled();
    });
  });

  test("calls RescanGarden when Rescan Downstream Configurations button clicked", async () => {
    const mockConfig = { garden_name: "Root" } as Config;
    const mockGarden = {
      id: "1",
      name: "Root Garden",
      version: "1.0.0",
      children: [],
      receiving_connections: [],
      publishing_connections: [],
    };

    vi.mocked(configService.GetConfig).mockResolvedValue(mockConfig);
    vi.mocked(gardenService.GetRootGarden).mockResolvedValue(mockGarden);
    vi.mocked(gardenService.RescanGarden).mockResolvedValue(mockGarden);

    render(<GardenTable listeners={{}} />);

    const rescanButton = await screen.findByText(
      "Rescan Downstream Configurations",
    );
    await userEvent.click(rescanButton);

    await waitFor(() => {
      expect(gardenService.RescanGarden).toHaveBeenCalled();
    });
  });

  test("handles child gardens in tree structure", async () => {
    const mockConfig = { garden_name: "Root" } as Config;
    const mockGarden = {
      id: "1",
      name: "Root Garden",
      version: "1.0.0",
      children: [
        {
          id: "2",
          name: "Child Garden",
          version: "1.0.0",
          children: [],
          receiving_connections: [],
          publishing_connections: [],
        },
      ],
      receiving_connections: [],
      publishing_connections: [],
    };

    vi.mocked(configService.GetConfig).mockResolvedValue(mockConfig);
    vi.mocked(gardenService.GetRootGarden).mockResolvedValue(mockGarden);

    render(<GardenTable listeners={{}} />);

    await waitFor(() => {
      expect(screen.getByText("Child Garden")).toBeInTheDocument();
    });
  });

  test("handles connection status display", async () => {
    const mockConfig = { garden_name: "Root" } as Config;
    const mockGarden = {
      id: "1",
      name: "Root Garden",
      version: "1.0.0",
      children: [
        {
          id: "2",
          name: "Child Garden",
          version: "1.0.0",
          children: [],
          receiving_connections: [
            { api: "HTTP", status: "RECEIVING", config: {} },
          ],
          publishing_connections: [
            { api: "HTTP", status: "PUBLISHING", config: {} },
          ],
        },
      ],
      receiving_connections: [],
      publishing_connections: [],
    };

    vi.mocked(configService.GetConfig).mockResolvedValue(mockConfig);
    vi.mocked(gardenService.GetRootGarden).mockResolvedValue(mockGarden);

    render(<GardenTable listeners={{}} />);

    await waitFor(() => {
      expect(screen.getByText("RECEIVING")).toBeInTheDocument();
      expect(screen.getByText("PUBLISHING")).toBeInTheDocument();
    });
  });

  test("handles http status buttons display", async () => {
    const mockConfig = { garden_name: "Root" } as Config;
    const mockGarden = {
      id: "1",
      name: "Root Garden",
      version: "1.0.0",
      children: [
        {
          id: "2",
          name: "Child Garden",
          version: "1.0.0",
          children: [],
          receiving_connections: [
            { api: "HTTP", status: "RECEIVING", config: {} },
          ],
          publishing_connections: [
            { api: "HTTP", status: "PUBLISHING", config: {} },
          ],
        },
      ],
      receiving_connections: [],
      publishing_connections: [],
    };

    vi.mocked(configService.GetConfig).mockResolvedValue(mockConfig);
    vi.mocked(gardenService.GetRootGarden).mockResolvedValue(mockGarden);

    render(<GardenTable listeners={{}} />);

    await waitFor(() => {
      expect(screen.getByTestId("2_http_publishing_START")).toBeInTheDocument();
      expect(screen.getByTestId("2_http_publishing_STOP")).toBeInTheDocument();
      expect(screen.getByTestId("2_http_receiving_START")).toBeInTheDocument();
      expect(screen.getByTestId("2_http_receiving_STOP")).toBeInTheDocument();
    });
  });

  test("calls http receiving start", async () => {
    const mockConfig = { garden_name: "Root" } as Config;
    const mockGarden = {
      id: "1",
      name: "Root Garden",
      version: "1.0.0",
      children: [
        {
          id: "2",
          name: "Child Garden",
          version: "1.0.0",
          children: [],
          receiving_connections: [
            { api: "HTTP", status: "RECEIVING", config: {} },
          ],
          publishing_connections: [
            { api: "HTTP", status: "PUBLISHING", config: {} },
          ],
        },
      ],
      receiving_connections: [],
      publishing_connections: [],
    };

    vi.mocked(configService.GetConfig).mockResolvedValue(mockConfig);
    vi.mocked(gardenService.GetRootGarden).mockResolvedValue(mockGarden);
    vi.mocked(gardenService.UpdateApiGarden).mockResolvedValue(mockGarden);

    render(<GardenTable listeners={{}} />);

    const httpReceivingStartButton = await screen.findByTestId(
      "2_http_receiving_START",
    );
    await userEvent.click(httpReceivingStartButton);

    await waitFor(() => {
      expect(gardenService.UpdateApiGarden).toHaveBeenCalledWith(
        "Child Garden",
        "RECEIVING",
        "HTTP",
        "RECEIVING",
      );
    });
  });

  test("calls http receiving stop", async () => {
    const mockConfig = { garden_name: "Root" } as Config;
    const mockGarden = {
      id: "1",
      name: "Root Garden",
      version: "1.0.0",
      children: [
        {
          id: "2",
          name: "Child Garden",
          version: "1.0.0",
          children: [],
          receiving_connections: [
            { api: "HTTP", status: "RECEIVING", config: {} },
          ],
          publishing_connections: [
            { api: "HTTP", status: "PUBLISHING", config: {} },
          ],
        },
      ],
      receiving_connections: [],
      publishing_connections: [],
    };

    vi.mocked(configService.GetConfig).mockResolvedValue(mockConfig);
    vi.mocked(gardenService.GetRootGarden).mockResolvedValue(mockGarden);
    vi.mocked(gardenService.UpdateApiGarden).mockResolvedValue(mockGarden);

    render(<GardenTable listeners={{}} />);

    const httpReceivingStopButton = await screen.findByTestId(
      "2_http_receiving_STOP",
    );
    await userEvent.click(httpReceivingStopButton);

    await waitFor(() => {
      expect(gardenService.UpdateApiGarden).toHaveBeenCalledWith(
        "Child Garden",
        "DISABLED",
        "HTTP",
        "RECEIVING",
      );
    });
  });

  test("calls http publishing start", async () => {
    const mockConfig = { garden_name: "Root" } as Config;
    const mockGarden = {
      id: "1",
      name: "Root Garden",
      version: "1.0.0",
      children: [
        {
          id: "2",
          name: "Child Garden",
          version: "1.0.0",
          children: [],
          receiving_connections: [
            { api: "HTTP", status: "RECEIVING", config: {} },
          ],
          publishing_connections: [
            { api: "HTTP", status: "PUBLISHING", config: {} },
          ],
        },
      ],
      receiving_connections: [],
      publishing_connections: [],
    };

    vi.mocked(configService.GetConfig).mockResolvedValue(mockConfig);
    vi.mocked(gardenService.GetRootGarden).mockResolvedValue(mockGarden);
    vi.mocked(gardenService.UpdateApiGarden).mockResolvedValue(mockGarden);

    render(<GardenTable listeners={{}} />);

    const httpPublishingStartButton = await screen.findByTestId(
      "2_http_publishing_START",
    );
    await userEvent.click(httpPublishingStartButton);

    await waitFor(() => {
      expect(gardenService.UpdateApiGarden).toHaveBeenCalledWith(
        "Child Garden",
        "PUBLISHING",
        "HTTP",
        "PUBLISHING",
      );
    });
  });

  test("calls http publishing stop", async () => {
    const mockConfig = { garden_name: "Root" } as Config;
    const mockGarden = {
      id: "1",
      name: "Root Garden",
      version: "1.0.0",
      children: [
        {
          id: "2",
          name: "Child Garden",
          version: "1.0.0",
          children: [],
          receiving_connections: [
            { api: "HTTP", status: "RECEIVING", config: {} },
          ],
          publishing_connections: [
            { api: "HTTP", status: "PUBLISHING", config: {} },
          ],
        },
      ],
      receiving_connections: [],
      publishing_connections: [],
    };

    vi.mocked(configService.GetConfig).mockResolvedValue(mockConfig);
    vi.mocked(gardenService.GetRootGarden).mockResolvedValue(mockGarden);
    vi.mocked(gardenService.UpdateApiGarden).mockResolvedValue(mockGarden);

    render(<GardenTable listeners={{}} />);

    const httpPublishingStopButton = await screen.findByTestId(
      "2_http_publishing_STOP",
    );
    await userEvent.click(httpPublishingStopButton);

    await waitFor(() => {
      expect(gardenService.UpdateApiGarden).toHaveBeenCalledWith(
        "Child Garden",
        "DISABLED",
        "HTTP",
        "PUBLISHING",
      );
    });
  });

  test("calls garden sync", async () => {
    const mockConfig = { garden_name: "Root" } as Config;
    const mockGarden = {
      id: "1",
      name: "Root Garden",
      version: "1.0.0",
      children: [
        {
          id: "2",
          name: "Child Garden",
          version: "1.0.0",
          children: [],
          receiving_connections: [
            { api: "HTTP", status: "RECEIVING", config: {} },
          ],
          publishing_connections: [
            { api: "HTTP", status: "PUBLISHING", config: {} },
          ],
        },
      ],
      receiving_connections: [],
      publishing_connections: [],
    };

    vi.mocked(configService.GetConfig).mockResolvedValue(mockConfig);
    vi.mocked(gardenService.GetRootGarden).mockResolvedValue(mockGarden);
    vi.mocked(gardenService.SyncGarden).mockResolvedValue(mockGarden);

    render(<GardenTable listeners={{}} />);

    const syncGardenActionButton = await screen.findByTestId("2_ACTIONS");
    expect(syncGardenActionButton).toBeInTheDocument();
    const buttons = within(syncGardenActionButton).getAllByRole("button");

    await userEvent.click(buttons[0]);

    await waitFor(() => {
      expect(gardenService.SyncGarden).toBeCalled();
      expect(gardenService.SyncGarden).toHaveBeenCalledWith("Child Garden");
    });
  });

  test("calls garden actions delete", async () => {
    const mockConfig = { garden_name: "Root" } as Config;
    const mockGarden = {
      id: "1",
      name: "Root Garden",
      version: "1.0.0",
      children: [
        {
          id: "2",
          name: "Child Garden",
          version: "1.0.0",
          children: [],
          receiving_connections: [
            { api: "HTTP", status: "RECEIVING", config: {} },
          ],
          publishing_connections: [
            { api: "HTTP", status: "PUBLISHING", config: {} },
          ],
        },
      ],
      receiving_connections: [],
      publishing_connections: [],
    };

    vi.mocked(configService.GetConfig).mockResolvedValue(mockConfig);
    vi.mocked(gardenService.GetRootGarden).mockResolvedValue(mockGarden);
    vi.mocked(gardenService.DeleteGarden).mockResolvedValue(mockGarden);

    render(<GardenTable listeners={{}} />);

    const syncGardenActionButton = await screen.findByTestId("2_ACTIONS");

    expect(syncGardenActionButton).toBeInTheDocument();
    const buttons = within(syncGardenActionButton).getAllByRole("button");

    await userEvent.click(buttons[1]);

    const deleteButton = await screen.findByText("Delete");

    await userEvent.click(deleteButton);

    await waitFor(() => {
      expect(gardenService.DeleteGarden).toBeCalled();
      expect(gardenService.DeleteGarden).toHaveBeenCalledWith("Child Garden");
    });
  });

  test("calls garden actions rescan plugins", async () => {
    const mockConfig = { garden_name: "Root" } as Config;
    const mockGarden = {
      id: "1",
      name: "Root Garden",
      version: "1.0.0",
      children: [
        {
          id: "2",
          name: "Child Garden",
          version: "1.0.0",
          children: [],
          receiving_connections: [
            { api: "HTTP", status: "RECEIVING", config: {} },
          ],
          publishing_connections: [
            { api: "HTTP", status: "PUBLISHING", config: {} },
          ],
        },
      ],
      receiving_connections: [],
      publishing_connections: [],
    };

    vi.mocked(configService.GetConfig).mockResolvedValue(mockConfig);
    vi.mocked(gardenService.GetRootGarden).mockResolvedValue(mockGarden);
    vi.mocked(systemService.Rescan);

    render(<GardenTable listeners={{}} />);

    const syncGardenActionButton = await screen.findByTestId("2_ACTIONS");

    expect(syncGardenActionButton).toBeInTheDocument();
    const buttons = within(syncGardenActionButton).getAllByRole("button");

    await userEvent.click(buttons[1]);

    const rescanButton = await screen.findByText("Rescan Plugins");

    await userEvent.click(rescanButton);

    await waitFor(() => {
      expect(systemService.Rescan).toBeCalled();
      expect(systemService.Rescan).toHaveBeenCalledWith("Child Garden");
    });
  });

  test("calls garden actions rescan downstream", async () => {
    const mockConfig = { garden_name: "Root" } as Config;
    const mockGarden = {
      id: "1",
      name: "Root Garden",
      version: "1.0.0",
      children: [
        {
          id: "2",
          name: "Child Garden",
          version: "1.0.0",
          children: [],
          receiving_connections: [
            { api: "HTTP", status: "RECEIVING", config: {} },
          ],
          publishing_connections: [
            { api: "HTTP", status: "PUBLISHING", config: {} },
          ],
        },
      ],
      receiving_connections: [],
      publishing_connections: [],
    };

    vi.mocked(configService.GetConfig).mockResolvedValue(mockConfig);
    vi.mocked(gardenService.GetRootGarden).mockResolvedValue(mockGarden);
    vi.mocked(gardenService.RescanGarden).mockResolvedValue(mockGarden);

    render(<GardenTable listeners={{}} />);

    const syncGardenActionButton = await screen.findByTestId("2_ACTIONS");

    expect(syncGardenActionButton).toBeInTheDocument();
    const buttons = within(syncGardenActionButton).getAllByRole("button");

    await userEvent.click(buttons[1]);

    const rescanButton = await screen.findByText("Rescan Downstream");

    await userEvent.click(rescanButton);

    await waitFor(() => {
      expect(gardenService.RescanGarden).toBeCalled();
      expect(gardenService.RescanGarden).toHaveBeenCalledWith("Child Garden");
    });
  });

  test("calls garden actions clear plugin queue", async () => {
    const mockConfig = { garden_name: "Root" } as Config;
    const mockGarden = {
      id: "1",
      name: "Root Garden",
      version: "1.0.0",
      children: [
        {
          id: "2",
          name: "Child Garden",
          version: "1.0.0",
          children: [],
          receiving_connections: [
            { api: "HTTP", status: "RECEIVING", config: {} },
          ],
          publishing_connections: [
            { api: "HTTP", status: "PUBLISHING", config: {} },
          ],
        },
      ],
      receiving_connections: [],
      publishing_connections: [],
    };

    vi.mocked(configService.GetConfig).mockResolvedValue(mockConfig);
    vi.mocked(gardenService.GetRootGarden).mockResolvedValue(mockGarden);
    vi.mocked(gardenService.RescanGarden).mockResolvedValue(mockGarden);

    render(<GardenTable listeners={{}} />);

    const syncGardenActionButton = await screen.findByTestId("2_ACTIONS");

    expect(syncGardenActionButton).toBeInTheDocument();
    const buttons = within(syncGardenActionButton).getAllByRole("button");

    await userEvent.click(buttons[1]);

    const clearQueueButton = await screen.findByText("Clear Plugin Queues");

    await userEvent.click(clearQueueButton);

    await waitFor(() => {
      // expect(false).toBe(true); // Fail until we merge and update it
      expect(queueService.ClearAllQueues).toBeCalled();
      expect(queueService.ClearAllQueues).toHaveBeenCalledWith("Child Garden");
    });
  });

  test("calls garden actions sync users", async () => {
    const mockConfig = { garden_name: "Root" } as Config;
    const mockGarden = {
      id: "1",
      name: "Root Garden",
      version: "1.0.0",
      children: [
        {
          id: "2",
          name: "Child Garden",
          version: "1.0.0",
          children: [],
          receiving_connections: [
            { api: "HTTP", status: "RECEIVING", config: {} },
          ],
          publishing_connections: [
            { api: "HTTP", status: "PUBLISHING", config: {} },
          ],
        },
      ],
      receiving_connections: [],
      publishing_connections: [],
    };

    vi.mocked(configService.GetConfig).mockResolvedValue(mockConfig);
    vi.mocked(gardenService.GetRootGarden).mockResolvedValue(mockGarden);
    vi.mocked(gardenService.SyncUsersGarden).mockResolvedValue(mockGarden);

    render(<GardenTable listeners={{}} />);

    const syncGardenActionButton = await screen.findByTestId("2_ACTIONS");

    expect(syncGardenActionButton).toBeInTheDocument();
    const buttons = within(syncGardenActionButton).getAllByRole("button");

    await userEvent.click(buttons[1]);

    const clearQueueButton = await screen.findByText("Sync Users");

    await userEvent.click(clearQueueButton);

    await waitFor(() => {
      expect(gardenService.SyncUsersGarden).toBeCalled();
      expect(gardenService.SyncUsersGarden).toHaveBeenCalledWith(
        "Child Garden",
      );
    });
  });
});
