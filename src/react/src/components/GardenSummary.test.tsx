import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, test, vi } from "vitest";

import { Connection, Garden, Instance, System } from "../models/brewtils-types";
import { TourStepProps } from "../models/models";
import { ToastProvider } from "../providers/ToastProvider";
import * as gardenService from "../services/garden_service";
import * as queueService from "../services/queue_service";
import * as systemService from "../services/system_service";
import GardenSummary from "./GardenSummary";

vi.mock("../services/garden_service");
vi.mock("../services/system_service");
vi.mock("../services/queue_service");

const mockTourSteps = () => {
  const mockRef = {
    current: [] as TourStepProps[], // Mocking the value property
  };
  return mockRef as React.RefObject<TourStepProps[]>;
};

describe("GardenSummary", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    cleanup();
  });

  const getRootGarden = () => {
    return {
      id: "1",
      name: "Root",
      version: "1.0.0",
      children: [getChildGardenOne(), getChildGardenTwo()],
      receiving_connections: [
        { status: "RECEIVING", api: "HTTP" } as Connection,
      ],
      publishing_connections: [
        { status: "PUBLISHING", api: "STOMP" } as Connection,
      ],
    } as Garden;
  };

  const getChildGardenOne = () => {
    return {
      id: "11",
      name: "child_one",
      version: "1.0.0",
      has_parent: true,
      parent: "Root",
      receiving_connections: [
        { status: "RECEIVING", api: "HTTP" } as Connection,
      ],
      publishing_connections: [
        { status: "PUBLISHING", api: "STOMP" } as Connection,
      ],
    } as Garden;
  };

  const getChildGardenTwo = () => {
    return {
      id: "12",
      name: "child_two",
      version: "2.0.0",
      has_parent: true,
      parent: "Root",
      receiving_connections: [
        { status: "CONFIGURATION_ERROR", api: "HTTP" } as Connection,
      ],
      publishing_connections: [
        { status: "DISABLED", api: "STOMP" } as Connection,
      ],
    } as Garden;
  };

  test("renders root garden summary", async () => {
    const mockGarden = getRootGarden();
    const refGarden = getRootGarden();

    render(
      <ToastProvider>
        <GardenSummary
          gardenRef={{ current: refGarden }}
          selectedGarden={mockGarden}
          config={{}}
          tourStepsRef={mockTourSteps()}
          selectedSystems={[]}
          associatedRunners={{ current: [] }}
        />
      </ToastProvider>,
    );

    await waitFor(() => {
      expect(
        screen.getByText(`Garden Summary: ${mockGarden?.name}`),
      ).toBeVisible();
      expect(screen.getByText("1.0.0")).toBeInTheDocument();
      expect(screen.getByText("child_one")).toBeInTheDocument();
      expect(screen.getByText("child_two")).toBeInTheDocument();
      expect(screen.getByText("RECEIVING")).toBeInTheDocument();
      expect(screen.getByText("PUBLISHING")).toBeInTheDocument();
    });
  });

  test("renders child one garden summary", async () => {
    const mockGarden = getChildGardenOne();
    const refGarden = getRootGarden();

    render(
      <ToastProvider>
        <GardenSummary
          gardenRef={{ current: refGarden }}
          selectedGarden={mockGarden}
          config={{}}
          tourStepsRef={mockTourSteps()}
          selectedSystems={[]}
          associatedRunners={{ current: [] }}
        />
      </ToastProvider>,
    );

    await waitFor(() => {
      expect(
        screen.getByText(`Garden Summary: ${mockGarden?.name}`),
      ).toBeVisible();
      expect(screen.getByText(`${mockGarden.version}`)).toBeInTheDocument();
      expect(screen.getByText(`${mockGarden.parent}`)).toBeInTheDocument();
      expect(
        screen.getByText(`${mockGarden.receiving_connections[0].status}`),
      ).toBeInTheDocument();
      expect(
        screen.getByText(`${mockGarden.publishing_connections[0].status}`),
      ).toBeInTheDocument();
    });
  });

  test("renders child two garden summary", async () => {
    const mockGarden = getChildGardenTwo();
    const refGarden = getRootGarden();

    render(
      <ToastProvider>
        <GardenSummary
          gardenRef={{ current: refGarden }}
          selectedGarden={mockGarden}
          config={{}}
          tourStepsRef={mockTourSteps()}
          selectedSystems={[]}
          associatedRunners={{ current: [] }}
        />
      </ToastProvider>,
    );

    await waitFor(() => {
      expect(
        screen.getByText(`Garden Summary: ${mockGarden?.name}`),
      ).toBeVisible();
      expect(screen.getByText(`${mockGarden.version}`)).toBeInTheDocument();
      expect(screen.getByText(`${mockGarden.parent}`)).toBeInTheDocument();
      expect(
        screen.getByText(`${mockGarden.receiving_connections[0].status}`),
      ).toBeInTheDocument();
      expect(
        screen.getByText(`${mockGarden.publishing_connections[0].status}`),
      ).toBeInTheDocument();
    });
  });

  it.each([
    { mockGarden: getRootGarden() },
    { mockGarden: getChildGardenOne() },
    { mockGarden: getChildGardenTwo() },
  ])("Button Visibility $mockGarden.name", async ({ mockGarden }) => {
    const refGarden = getRootGarden();

    render(
      <ToastProvider>
        <GardenSummary
          gardenRef={{ current: refGarden }}
          selectedGarden={mockGarden}
          config={{}}
          tourStepsRef={mockTourSteps()}
          selectedSystems={[]}
          associatedRunners={{ current: [] }}
        />
      </ToastProvider>,
    );

    // Global
    await waitFor(() => {
      expect(screen.getByTestId("RESCAN_PLUGINS")).toBeInTheDocument();
      expect(screen.getByTestId("RESCAN_DOWNSTREAM")).toBeInTheDocument();
      expect(screen.getByTestId("CLEAR_PLUGIN_QUEUES")).toBeInTheDocument();
    });

    const sync_garden = screen.queryByTestId("SYNC_GARDEN");
    const sync_users = screen.queryByTestId("SYNC_USERS");
    const delete_garden = screen.queryByTestId("DELETE_GARDEN");
    const sync_all = screen.queryByTestId("SYNC_ALL");

    // Root Only
    if (mockGarden.name === refGarden.name) {
      await waitFor(() => {
        expect(sync_garden).toBeNull();
        expect(sync_users).toBeNull();
        expect(delete_garden).toBeNull();
        expect(sync_all).toBeInTheDocument();
      });
    }
    // Downstream Only
    if (mockGarden.name !== refGarden.name) {
      await waitFor(() => {
        expect(sync_garden).toBeInTheDocument();
        expect(sync_users).toBeInTheDocument();
        expect(delete_garden).toBeInTheDocument();
        expect(sync_all).toBeNull();
      });
    }
  });

  test("Rescan Plugin", async () => {
    const mockGarden = getRootGarden();
    const refGarden = getRootGarden();

    vi.mocked(systemService.Rescan);

    render(
      <ToastProvider>
        <GardenSummary
          gardenRef={{ current: refGarden }}
          selectedGarden={mockGarden}
          config={{}}
          tourStepsRef={mockTourSteps()}
          selectedSystems={[]}
          associatedRunners={{ current: [] }}
        />
      </ToastProvider>,
    );

    const target_button = await screen.findByTestId("RESCAN_PLUGINS");
    expect(target_button).toBeInTheDocument();

    await userEvent.click(target_button);

    await waitFor(() => {
      expect(systemService.Rescan).toBeCalled();
      expect(systemService.Rescan).toHaveBeenCalledWith(mockGarden.name);
    });
  });

  test("Rescan Downstream", async () => {
    const mockGarden = getRootGarden();
    const refGarden = getRootGarden();

    vi.mocked(gardenService.RescanGarden).mockResolvedValue(mockGarden);

    render(
      <ToastProvider>
        <GardenSummary
          gardenRef={{ current: refGarden }}
          selectedGarden={mockGarden}
          config={{}}
          tourStepsRef={mockTourSteps()}
          selectedSystems={[]}
          associatedRunners={{ current: [] }}
        />
      </ToastProvider>,
    );

    const target_button = await screen.findByTestId("RESCAN_DOWNSTREAM");
    expect(target_button).toBeInTheDocument();

    await userEvent.click(target_button);

    await waitFor(() => {
      expect(gardenService.RescanGarden).toBeCalled();
      expect(gardenService.RescanGarden).toHaveBeenCalledWith(mockGarden.name);
    });
  });

  test("Clear Plugin Queues", async () => {
    const mockGarden = getRootGarden();
    const refGarden = getRootGarden();

    vi.mocked(queueService.ClearAllQueues);

    render(
      <ToastProvider>
        <GardenSummary
          gardenRef={{ current: refGarden }}
          selectedGarden={mockGarden}
          config={{}}
          tourStepsRef={mockTourSteps()}
          selectedSystems={[]}
          associatedRunners={{ current: [] }}
        />
      </ToastProvider>,
    );

    const target_button = await screen.findByTestId("CLEAR_PLUGIN_QUEUES");
    expect(target_button).toBeInTheDocument();

    await userEvent.click(target_button);

    await waitFor(() => {
      expect(queueService.ClearAllQueues).toBeCalled();
      expect(queueService.ClearAllQueues).toHaveBeenCalledWith(mockGarden.name);
    });
  });

  test("Sync All", async () => {
    const mockGarden = getRootGarden();
    const refGarden = getRootGarden();

    vi.mocked(gardenService.SyncGarden);

    render(
      <ToastProvider>
        <GardenSummary
          gardenRef={{ current: refGarden }}
          selectedGarden={mockGarden}
          config={{}}
          tourStepsRef={mockTourSteps()}
          selectedSystems={[]}
          associatedRunners={{ current: [] }}
        />
      </ToastProvider>,
    );

    const target_button = await screen.findByTestId("SYNC_ALL");
    expect(target_button).toBeInTheDocument();

    await userEvent.click(target_button);

    await waitFor(() => {
      expect(gardenService.SyncGarden).toBeCalled();
      expect(gardenService.SyncGarden).toHaveBeenCalledWith();
    });
  });

  test("Sync Garden", async () => {
    const mockGarden = getChildGardenOne();
    const refGarden = getRootGarden();

    vi.mocked(gardenService.SyncGarden);

    render(
      <ToastProvider>
        <GardenSummary
          gardenRef={{ current: refGarden }}
          selectedGarden={mockGarden}
          config={{}}
          tourStepsRef={mockTourSteps()}
          selectedSystems={[]}
          associatedRunners={{ current: [] }}
        />
      </ToastProvider>,
    );

    const target_button = await screen.findByTestId("SYNC_GARDEN");
    expect(target_button).toBeInTheDocument();

    await userEvent.click(target_button);

    await waitFor(() => {
      expect(gardenService.SyncGarden).toBeCalled();
      expect(gardenService.SyncGarden).toHaveBeenCalledWith(mockGarden.name);
    });
  });

  test("Sync Users", async () => {
    const mockGarden = getChildGardenOne();
    const refGarden = getRootGarden();

    vi.mocked(gardenService.SyncUsersGarden);

    render(
      <ToastProvider>
        <GardenSummary
          gardenRef={{ current: refGarden }}
          selectedGarden={mockGarden}
          config={{}}
          tourStepsRef={mockTourSteps()}
          selectedSystems={[]}
          associatedRunners={{ current: [] }}
        />
      </ToastProvider>,
    );

    const target_button = await screen.findByTestId("SYNC_USERS");
    expect(target_button).toBeInTheDocument();

    await userEvent.click(target_button);

    await waitFor(() => {
      expect(gardenService.SyncUsersGarden).toBeCalled();
      expect(gardenService.SyncUsersGarden).toHaveBeenCalledWith(
        mockGarden.name,
      );
    });
  });

  test("Delete Garden", async () => {
    const mockGarden = getChildGardenOne();
    const refGarden = getRootGarden();

    vi.mocked(gardenService.DeleteGarden);

    render(
      <ToastProvider>
        <GardenSummary
          gardenRef={{ current: refGarden }}
          selectedGarden={mockGarden}
          config={{}}
          tourStepsRef={mockTourSteps()}
          selectedSystems={[]}
          associatedRunners={{ current: [] }}
        />
      </ToastProvider>,
    );

    const target_button = await screen.findByTestId("DELETE_GARDEN");
    expect(target_button).toBeInTheDocument();

    await userEvent.click(target_button);

    await waitFor(() => {
      expect(gardenService.DeleteGarden).toBeCalled();
      expect(gardenService.DeleteGarden).toHaveBeenCalledWith(mockGarden.name);
    });
  });

  test("Receiving Start", async () => {
    const mockGarden = getChildGardenOne();
    const refGarden = getRootGarden();

    vi.mocked(gardenService.UpdateApiGarden);

    render(
      <ToastProvider>
        <GardenSummary
          gardenRef={{ current: refGarden }}
          selectedGarden={mockGarden}
          config={{}}
          tourStepsRef={mockTourSteps()}
          selectedSystems={[]}
          associatedRunners={{ current: [] }}
        />
      </ToastProvider>,
    );

    const target_button = await screen.findByTestId(
      `RECEIVING_${mockGarden.receiving_connections[0].api}_START`,
    );

    expect(target_button).toBeInTheDocument();

    await userEvent.click(target_button);

    await waitFor(() => {
      expect(gardenService.UpdateApiGarden).toBeCalled();
      expect(gardenService.UpdateApiGarden).toHaveBeenCalledWith(
        mockGarden.name,
        "RECEIVING",
        mockGarden.receiving_connections[0].api,
        "RECEIVING",
      );
    });
  });

  test("Receiving Stop", async () => {
    const mockGarden = getChildGardenOne();
    const refGarden = getRootGarden();

    vi.mocked(gardenService.UpdateApiGarden);

    render(
      <ToastProvider>
        <GardenSummary
          gardenRef={{ current: refGarden }}
          selectedGarden={mockGarden}
          config={{}}
          tourStepsRef={mockTourSteps()}
          selectedSystems={[]}
          associatedRunners={{ current: [] }}
        />
      </ToastProvider>,
    );

    const target_button = await screen.findByTestId(
      `RECEIVING_${mockGarden.receiving_connections[0].api}_STOP`,
    );
    expect(target_button).toBeInTheDocument();

    await userEvent.click(target_button);

    await waitFor(() => {
      expect(gardenService.UpdateApiGarden).toBeCalled();
      expect(gardenService.UpdateApiGarden).toHaveBeenCalledWith(
        mockGarden.name,
        "DISABLED",
        "HTTP",
        "RECEIVING",
      );
    });
  });

  test("Publishing Start", async () => {
    const mockGarden = getChildGardenOne();
    const refGarden = getRootGarden();

    vi.mocked(gardenService.UpdateApiGarden);

    render(
      <ToastProvider>
        <GardenSummary
          gardenRef={{ current: refGarden }}
          selectedGarden={mockGarden}
          config={{}}
          tourStepsRef={mockTourSteps()}
          selectedSystems={[]}
          associatedRunners={{ current: [] }}
        />
      </ToastProvider>,
    );

    const target_button = await screen.findByTestId(
      `PUBLISHING_${mockGarden.publishing_connections[0].api}_START`,
    );
    expect(target_button).toBeInTheDocument();

    await userEvent.click(target_button);

    await waitFor(() => {
      expect(gardenService.UpdateApiGarden).toBeCalled();
      expect(gardenService.UpdateApiGarden).toHaveBeenCalledWith(
        mockGarden.name,
        "PUBLISHING",
        "STOMP",
        "PUBLISHING",
      );
    });
  });

  test("Publishing Stop", async () => {
    const mockGarden = getChildGardenOne();
    const refGarden = getRootGarden();

    vi.mocked(gardenService.UpdateApiGarden);

    render(
      <ToastProvider>
        <GardenSummary
          gardenRef={{ current: refGarden }}
          selectedGarden={mockGarden}
          config={{}}
          tourStepsRef={mockTourSteps()}
          selectedSystems={[]}
          associatedRunners={{ current: [] }}
        />
      </ToastProvider>,
    );

    const target_button = await screen.findByTestId(
      `PUBLISHING_${mockGarden.publishing_connections[0].api}_STOP`,
    );
    expect(target_button).toBeInTheDocument();

    await userEvent.click(target_button);

    await waitFor(() => {
      expect(gardenService.UpdateApiGarden).toBeCalled();
      expect(gardenService.UpdateApiGarden).toHaveBeenCalledWith(
        mockGarden.name,
        "DISABLED",
        "STOMP",
        "PUBLISHING",
      );
    });
  });

  it.each([
    { status: "INITIALIZING" },
    { status: "RUNNING" },
    { status: "PAUSED" },
    { status: "STOPPED" },
    { status: "DEAD" },
    { status: "UNRESPONSIVE" },
    { status: "STARTING" },
    { status: "STOPPING" },
    { status: "UNKNOWN" },
    { status: "AWAITING_SYSTEM" },
    { status: "ERROR" },
  ])(`system severity" $status`, ({ status }) => {
    const mockGarden = getRootGarden();

    mockGarden.systems = [
      {
        instances: [{ status: status } as Instance],
        local: false,
        garden_name: mockGarden.name,
      } as System,
    ];

    const refGarden = { name: "rootGarden" };

    render(
      <ToastProvider>
        <GardenSummary
          gardenRef={{ current: refGarden }}
          selectedGarden={mockGarden}
          config={{}}
          tourStepsRef={mockTourSteps()}
          selectedSystems={mockGarden.systems}
          associatedRunners={{ current: [] }}
        />
      </ToastProvider>,
    );

    const summary = screen.queryByTestId(`${status}_severity_system_summary`);
    expect(summary).toBeInTheDocument();
    expect(summary).toHaveTextContent(`1`);
  });
});
