import {
  cleanup,
  render,
  screen,
  waitFor,
  waitForElementToBeRemoved,
  within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, test, vi } from "vitest";

import { Config } from "../models/models";
import * as configService from "../services/config_service";
import * as systemService from "../services/system_service";
import * as queueService from "../services/queue_service";
import * as instanceService from "../services/instance_service"
import SystemCards from "./SystemCards";

vi.mock("../services/system_service");
vi.mock("../services/instance_service");
vi.mock("../services/queue_service");
vi.mock("../services/config_service");

const mockSystems = [
  {
    id: "1",
    name: "Test",
    description: "Test System",
    version: "1.0.0.dev0",
    namespace: "default",
    max_instances: -1,
    instances: [
      {
        id: "2",
        name: "default",
        status: "RUNNING",
        status_info: {
          heartbeat: "2026-03-09T12:43:51.871Z",
          history: [
            {
              status: "RUNNING",
              heartbeat: "2026-03-09T12:43:51.871Z",
            },
          ],
        },
        queue_info: {
          admin: { name: "admin.default.test.11-0-0-dev0.default" },
          request: { name: "default.test.1-0-0-dev0.default" },
          connection: {
            host: "localhost",
            port: 5672,
            user: "beer_garden",
            password: "password",
            virtual_host: "/",
            ssl: {
              enabled: false,
              ca_cert: null,
              ca_verify: true,
              client_cert: null,
            },
          },
        },
        metadata: { runner_id: "NiYiHSsrrL" },
        queue_type: "rabbitmq",
      },
    ],
    commands: [],
    icon_name: "fa-comment",
    metadata: {},
    local: true,
    groups: [],
    requires: [],
    requires_timeout: 300,
    garden_name: "default",
    display_name: "",
    template: "",
  },
];

describe("SystemCards", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    cleanup();
  });

  test("renders system page", async () => {
    const mockConfig = { garden_name: "Root" } as Config;
    const mockSystems = [] as any;

    vi.mocked(configService.GetConfig).mockResolvedValue(mockConfig);
    vi.mocked(systemService.GetSystemList).mockResolvedValue(mockSystems);

    render(<SystemCards listeners={{}} setReloadScratchPad={() => {}} />);

    await waitFor(() => {
      expect(screen.getByText("Systems Management")).toBeInTheDocument();
    });
  });

  test("renders system cards", async () => {
    // vi.mocked(configService.GetConfig).mockResolvedValue(mockConfig);
    vi.mocked(systemService.GetSystemList).mockResolvedValue(mockSystems);

    render(<SystemCards listeners={{}} setReloadScratchPad={() => {}} />);

    await waitFor(() => {
      expect(screen.getByText(/Test\/ 1.0.0.dev0/)).toBeInTheDocument();
    });
  });

  test("calls Rescan when Rescan Plugin Directory button clicked", async () => {
    const mockSystems = [] as any;

    vi.mocked(systemService.Rescan).mockResolvedValue();

    render(<SystemCards listeners={{}} setReloadScratchPad={() => {}} />);

    const rescanButton = await screen.findByText("Rescan Plugin Directory");
    await userEvent.click(rescanButton);

    await waitFor(() => {
      expect(systemService.Rescan).toHaveBeenCalled();
    });
  });

  test("calls ClearAllQueues when Clear All Queues button clicked", async () => {
    const mockSystems = [] as any;

    vi.mocked(queueService.ClearAllQueues).mockResolvedValue();

    render(<SystemCards listeners={{}} setReloadScratchPad={() => {}} />);

    const clearQueuesButton = await screen.findByText("Clear All Queues");
    await userEvent.click(clearQueuesButton);

    // screen.debug(clearQueuesButton);

    //Say yes to confirmation
    const confirmYes = await screen.findByRole('button', {name: "Yes"})
    await userEvent.click(confirmYes);

    await waitFor(() => {
      expect(queueService.ClearAllQueues).toHaveBeenCalled();
    });
  });

  //Test toggle menu
  test("System menu button toggles menu", async () => {

    // vi.mocked(configService.GetConfig).mockResolvedValue(mockConfig);
    vi.mocked(systemService.GetSystemList).mockResolvedValue(mockSystems);

    render(<SystemCards listeners={{}} setReloadScratchPad={() => {}} />);

    const systemMenuButton = await screen.findByTestId("system-menu-Test-button")
    await userEvent.click(systemMenuButton)

    await waitFor(() => {
      expect(screen.getByTestId("system-menu-Test")).toBeInTheDocument();
    });
  });

  //Test delete system
  test("Test delete system", async () => {

    vi.mocked(systemService.DeleteSystem).mockResolvedValue();
    vi.mocked(systemService.GetSystemList).mockResolvedValue(mockSystems);

    render(<SystemCards listeners={{}} setReloadScratchPad={() => {}} />);

    const systemCard = await screen.findByText(/Test\/ 1.0.0.dev0/);
    await waitFor(() => {
      expect(systemCard).toBeInTheDocument();
    });

    const systemMenuButton = await screen.findByTestId("system-menu-Test-button")
    await userEvent.click(systemMenuButton)

    const systemDeleteButton = await screen.findByTestId("system-menu-item-Test-Delete");
    await userEvent.click(systemDeleteButton);

    //Say yes to confirm
    const confirmYes = await screen.findByRole('button', {name: "Yes"})
    await userEvent.click(confirmYes)

    await waitFor(() => {
      expect(systemService.DeleteSystem).toHaveBeenCalled()
    });

    // This won't work until MonitorSystemEvents is working
    // await waitForElementToBeRemoved(systemCard);
    // expect(systemCard).not.toBeInTheDocument();
  });

  //Test start system
  test("Test system menu start system", async () => {
    vi.mocked(systemService.GetSystemList).mockResolvedValue(mockSystems);

    render(<SystemCards listeners={{}} setReloadScratchPad={() => {}} />);

    const systemCard = await screen.findByText(/Test\/ 1.0.0.dev0/);
    await waitFor(() => {
      expect(systemCard).toBeInTheDocument();
    });

    const systemMenuButton = await screen.findByTestId("system-menu-Test-button")
    await userEvent.click(systemMenuButton)

    const systemButton = await screen.findByTestId("system-menu-item-Test-Start");
    await userEvent.click(systemButton);

    await waitFor(() => {
      expect(instanceService.StartInstance).toHaveBeenCalledTimes(1)
    });
  });

  //Test stop system
  test("Test system menu stop system", async () => {

    vi.mocked(systemService.DeleteSystem).mockResolvedValue();
    vi.mocked(systemService.GetSystemList).mockResolvedValue(mockSystems);

    render(<SystemCards listeners={{}} setReloadScratchPad={() => {}} />);

    const systemCard = await screen.findByText(/Test\/ 1.0.0.dev0/);
    await waitFor(() => {
      expect(systemCard).toBeInTheDocument();
    });

    const systemMenuButton = await screen.findByTestId("system-menu-Test-button")
    await userEvent.click(systemMenuButton)

    const systemButton = await screen.findByTestId("system-menu-item-Test-Stop");
    await userEvent.click(systemButton);

    await waitFor(() => {
      expect(instanceService.StopInstance).toHaveBeenCalledTimes(1)
    });
  });

  //Test restart system
  test("Test system menu restart system", async () => {

    vi.mocked(systemService.DeleteSystem).mockResolvedValue();
    vi.mocked(systemService.GetSystemList).mockResolvedValue(mockSystems);

    render(<SystemCards listeners={{}} setReloadScratchPad={() => {}} />);

    const systemCard = await screen.findByText(/Test\/ 1.0.0.dev0/);
    await waitFor(() => {
      expect(systemCard).toBeInTheDocument();
    });

    const systemMenuButton = await screen.findByTestId("system-menu-Test-button")
    await userEvent.click(systemMenuButton)

    const systemButton = await screen.findByTestId("system-menu-item-Test-Restart");
    await userEvent.click(systemButton);

    await waitFor(() => {
      expect(systemService.ReloadSystem).toHaveBeenCalled()
    });
  });

  //Test expand panel
  test("Test toggle button expands panel", async () => {

    // vi.mocked(configService.GetConfig).mockResolvedValue(mockConfig);
    vi.mocked(systemService.GetSystemList).mockResolvedValue(mockSystems);

    render(<SystemCards listeners={{}} setReloadScratchPad={() => {}} />);

    const expandButton = await screen.findByTestId("panel-toggler-Test-button")
    await userEvent.click(expandButton)

    await waitFor(() => {
      expect(screen.getByTestId("instance-template-Test")).toBeVisible();
    });
  });

  //Test panel start instance
  test("Test start instance", async () => {
    vi.mocked(systemService.GetSystemList).mockResolvedValue(mockSystems);

    render(<SystemCards listeners={{}} setReloadScratchPad={() => {}} />);

    const systemCard = await screen.findByText(/Test\/ 1.0.0.dev0/);
    await waitFor(() => {
      expect(systemCard).toBeInTheDocument();
    });

    const expandButton = await screen.findByTestId("panel-toggler-Test-button")
    await userEvent.click(expandButton)

    await waitFor(() => {
      expect(screen.getByTestId("instance-template-Test")).toBeVisible();
    });

    //Click instance button
    // screen.debug(undefined, Infinity)
    await userEvent.click(screen.getByTitle(`Start Instance ${mockSystems[0].instances[0].name}`))

    await waitFor(() => {
      expect(instanceService.StartInstance).toHaveBeenCalled()
    });
  });

  //Test panel stop instancee
  test("Test stop instance", async () => {

    vi.mocked(systemService.DeleteSystem).mockResolvedValue();
    vi.mocked(systemService.GetSystemList).mockResolvedValue(mockSystems);

    render(<SystemCards listeners={{}} setReloadScratchPad={() => {}} />);

    const systemCard = await screen.findByText(/Test\/ 1.0.0.dev0/);
    await waitFor(() => {
      expect(systemCard).toBeInTheDocument();
    });

    const expandButton = await screen.findByTestId("panel-toggler-Test-button")
    await userEvent.click(expandButton)

    await waitFor(() => {
      expect(screen.getByTestId("instance-template-Test")).toBeVisible();
    });

    await userEvent.click(screen.getByTitle(`Stop Instance ${mockSystems[0].instances[0].name}`))

    await waitFor(() => {
      expect(instanceService.StopInstance).toHaveBeenCalled()
    });
  });
  
  // Test Show Logs Dialog opens
  test("Test instance show logs dialog", async () => {

    vi.mocked(systemService.DeleteSystem).mockResolvedValue();
    vi.mocked(systemService.GetSystemList).mockResolvedValue(mockSystems);

    render(<SystemCards listeners={{}} setReloadScratchPad={() => {}} />);

    const systemCard = await screen.findByText(/Test\/ 1.0.0.dev0/);
    await waitFor(() => {
      expect(systemCard).toBeInTheDocument();
    });

    const expandButton = await screen.findByTestId("panel-toggler-Test-button")
    await userEvent.click(expandButton)

    await waitFor(() => {
      expect(screen.getByTestId("instance-template-Test")).toBeVisible();
    });

    await userEvent.click(screen.getByTitle(`Admin Tools for ${mockSystems[0].instances[0].name}`))

    //Wait for menu to show
    await waitFor(() => {
      expect(screen.getByTestId("instance-menu-default")).toBeInTheDocument();
    });

    await userEvent.click(screen.getByText("Show Logs"))

    //Wait for dialog to show
    await waitFor(() => {
      expect(screen.getByTestId("instance-show-logs-dialog")).toBeVisible();
    });
  });

  // Test Manage queue dialog open
  test("Test instance manage queue dialog", async () => {

    vi.mocked(systemService.DeleteSystem).mockResolvedValue();
    vi.mocked(systemService.GetSystemList).mockResolvedValue(mockSystems);

    render(<SystemCards listeners={{}} setReloadScratchPad={() => {}} />);

    const systemCard = await screen.findByText(/Test\/ 1.0.0.dev0/);
    await waitFor(() => {
      expect(systemCard).toBeInTheDocument();
    });

    const expandButton = await screen.findByTestId("panel-toggler-Test-button")
    await userEvent.click(expandButton)

    await waitFor(() => {
      expect(screen.getByTestId("instance-template-Test")).toBeVisible();
    });

    await userEvent.click(screen.getByTitle(`Admin Tools for ${mockSystems[0].instances[0].name}`))

    //Wait for menu to show
    await waitFor(() => {
      expect(screen.getByTestId("instance-menu-default")).toBeInTheDocument();
    });

    await userEvent.click(screen.getByText("Manage Queue"))

    //Wait for dialog to show
    await waitFor(() => {
      expect(screen.getByTestId("instance-manage-queue-dialog")).toBeVisible();
    });
  });

  // Test Cancel Delete Dialog opens
  test("Test cancel delete requests dialog", async () => {

    vi.mocked(systemService.DeleteSystem).mockResolvedValue();
    vi.mocked(systemService.GetSystemList).mockResolvedValue(mockSystems);

    render(<SystemCards listeners={{}} setReloadScratchPad={() => {}} />);

    const systemCard = await screen.findByText(/Test\/ 1.0.0.dev0/);
    await waitFor(() => {
      expect(systemCard).toBeInTheDocument();
    });

    const expandButton = await screen.findByTestId("panel-toggler-Test-button")
    await userEvent.click(expandButton)

    await waitFor(() => {
      expect(screen.getByTestId("instance-template-Test")).toBeVisible();
    });

    await userEvent.click(screen.getByTitle(`Admin Tools for ${mockSystems[0].instances[0].name}`))

    //Wait for menu to show
    await waitFor(() => {
      expect(screen.getByTestId("instance-menu-default")).toBeInTheDocument();
    });

    await userEvent.click(screen.getByText("Cancel/Delete Requests"))

    //Wait for dialog to show
    await waitFor(() => {
      expect(screen.getByTestId("instance-cancel-delete-requests-dialog")).toBeVisible();
    });
  });
});
