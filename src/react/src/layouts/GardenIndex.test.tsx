import { cleanup,render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, test, vi } from "vitest";

import { Config } from "../models/models";
import * as configService from "../services/config_service";
import * as gardenService from "../services/garden_service";
import GardenTable from "./GardenIndex";

vi.mock("../services/garden_service");
vi.mock("../services/config_service");

describe("GardenTable", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    cleanup();
  });

  test('renders garden table', async () => {
      const mockConfig = { garden_name: 'Root' } as Config;
      const mockGarden = {
          id: '1',
          name: 'Root',
          version: '1.0.0',
          children: [],
          receiving_connections: [],
          publishing_connections: [],
      };

      vi.mocked(configService.GetConfig).mockResolvedValue(mockConfig);
      vi.mocked(gardenService.GetRootGarden).mockResolvedValue(mockGarden);

      render(<GardenTable />);

      await waitFor(() => {
          expect(screen.getByText('Sync All')).toBeInTheDocument();
      });
  });

  test('fetches root garden on mount', async () => {
      const mockConfig = { garden_name: 'Root' } as Config;
      const mockGarden = {
          id: '1',
          name: 'Root Garden',
          version: '1.0.0',
          children: [],
          receiving_connections: [],
          publishing_connections: [],
      };

      vi.mocked(configService.GetConfig).mockResolvedValue(mockConfig);
      vi.mocked(gardenService.GetRootGarden).mockResolvedValue(mockGarden);

      render(<GardenTable />);

      await waitFor(() => {
          expect(configService.GetConfig).toHaveBeenCalled();
          expect(gardenService.GetRootGarden).toHaveBeenCalledWith(mockConfig, {});
      });
  });

  test('calls SyncGarden when Sync All button clicked', async () => {
      const mockConfig = { garden_name: 'Root' } as Config;
      const mockGarden = {
          id: '1',
          name: 'Root Garden',
          version: '1.0.0',
          children: [],
          receiving_connections: [],
          publishing_connections: [],
      };

      vi.mocked(configService.GetConfig).mockResolvedValue(mockConfig);
      vi.mocked(gardenService.GetRootGarden).mockResolvedValue(mockGarden);
      vi.mocked(gardenService.SyncGarden).mockResolvedValue(mockGarden);

      render(<GardenTable />);

      const syncButton = await screen.findByText('Sync All');
      await userEvent.click(syncButton);

      await waitFor(() => {
          expect(gardenService.SyncGarden).toHaveBeenCalled();
      });
  });

  test('calls RescanGarden when Rescan Downstream Configurations button clicked', async () => {
      const mockConfig = { garden_name: 'Root' } as Config;
      const mockGarden = {
          id: '1',
          name: 'Root Garden',
          version: '1.0.0',
          children: [],
          receiving_connections: [],
          publishing_connections: [],
      };

      vi.mocked(configService.GetConfig).mockResolvedValue(mockConfig);
      vi.mocked(gardenService.GetRootGarden).mockResolvedValue(mockGarden);
      vi.mocked(gardenService.RescanGarden).mockResolvedValue(mockGarden);

      render(<GardenTable />);

      const rescanButton = await screen.findByText('Rescan Downstream Configurations');
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

    render(<GardenTable />);

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

    render(<GardenTable />);

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

    render(<GardenTable />);

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

    render(<GardenTable />);

    const httpPublishingStartButton = await screen.findByTestId("2_http_publishing_START");
    await userEvent.click(httpPublishingStartButton);

    await waitFor(() => {
        expect(gardenService.UpdateApiGarden).not.toHaveBeenCalled();
    });

  });
});
