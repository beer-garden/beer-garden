import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, test, vi } from "vitest";

import {
  CronTrigger,
  DateTrigger,
  FileTrigger,
  IntervalTrigger,
  Job,
  Request,
} from "../models/brewtils-types";
import { ConfirmDialogProvider } from "../providers/ConfirmDialogProvider";
import { SnackbarProvider } from "../providers/SnackbarProvider";
import * as jobService from "../services/job_service";
import * as requestService from "../services/request_service";
import SchedulerViewCard from "./SchedulerViewCard";

vi.mock("../services/job_service");
vi.mock("../services/request_service");
vi.mock("../services/util_service");

describe("SchedulerViewCard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    cleanup();

    vi.mock("react-router-dom", async () => {
      const actual = await vi.importActual("react-router-dom");
      return {
        ...actual,
        useNavigate: () => vi.fn(),
      };
    });
  });

  test("renders Cron Scheduler View Card", async () => {
    const mockJob = {
      id: "1",
      name: "example_job",
      trigger_type: "cron",
      trigger: {
        year: "*",
        month: "*",
        day: "*",
        week: "*",
        dayOfWeek: "*",
        hour: "*",
        minute: "*",
        second: "*",
      } as CronTrigger,
      coalesce: false,
      misfire_grace_time: 1,
      next_run_time: null,
      status: "RUNNING",
      max_instances: 1,
      timeout: 5,
    } as Job;

    vi.mocked(jobService.GetJob).mockResolvedValue(mockJob);
    vi.mocked(requestService.GetRequestList).mockResolvedValue([
      [],
      new Headers(),
    ]);

    render(
      <SnackbarProvider>
        <ConfirmDialogProvider>
          <SchedulerViewCard
            listeners={{}}
            jobId="1"
            editJob={() => {}}
            deleteJob={() => {}}
            config={{}}
          />
        </ConfirmDialogProvider>
      </SnackbarProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("example_job")).toBeInTheDocument();
      expect(screen.getAllByRole("paragraph")[0]).toHaveTextContent("RUNNING");
      expect(screen.getAllByRole("paragraph")[1]).toHaveTextContent("False");
      expect(screen.getAllByRole("paragraph")[2]).toHaveTextContent("1");
      expect(screen.getAllByRole("paragraph")[3]).toHaveTextContent("1");
      expect(screen.getAllByRole("paragraph")[4]).toHaveTextContent("5");
      expect(screen.getAllByRole("paragraph")[5]).toHaveTextContent("CRON");
      expect(screen.getAllByRole("paragraph")[6]).toHaveTextContent(
        "* * * * * * *",
      );
      expect(screen.getAllByRole("paragraph")[7]).toHaveTextContent("N/A");
      expect(screen.getAllByRole("paragraph")[8]).toHaveTextContent("N/A");
      expect(screen.getAllByRole("paragraph")[9]).toHaveTextContent("N/A");
      expect(screen.getAllByRole("paragraph")[10]).toHaveTextContent("N/A");
    });
  });

  it.each([
    {
      trigger: {
        year: "*",

        dayOfWeek: "*",
        month: "*",
        day: "*",
        hour: "*",
        minute: "*",
        second: "*",
      },
      expected: "* * * * * * *",
    },
    {
      trigger: {
        year: "*",

        dayOfWeek: "*",
        month: "*",
        day: "*",
        hour: "*",
        minute: "*",
        second: "0",
      },
      expected: "0 * * * * * *",
    },
    {
      trigger: {
        year: "*",

        dayOfWeek: "*",
        month: "*",
        day: "*",
        hour: "*",
        minute: "0",
        second: "*",
      },
      expected: "* 0 * * * * *",
    },
    {
      trigger: {
        year: "*",

        dayOfWeek: "*",
        month: "*",
        day: "*",
        hour: "0",
        minute: "*",
        second: "*",
      },
      expected: "* * 0 * * * *",
    },
    {
      trigger: {
        year: "*",

        dayOfWeek: "*",
        month: "*",
        day: "0",
        hour: "*",
        minute: "*",
        second: "*",
      },
      expected: "* * * 0 * * *",
    },
    {
      trigger: {
        year: "*",
        dayOfWeek: "*",
        month: "0",
        day: "*",
        hour: "*",
        minute: "*",
        second: "*",
      },
      expected: "* * * * 0 * *",
    },
    {
      trigger: {
        year: "*",
        dayOfWeek: "0",
        month: "*",
        day: "*",
        hour: "*",
        minute: "*",
        second: "*",
      },
      expected: "* * * * * 0 *",
    },
    {
      trigger: {
        year: "0",
        dayOfWeek: "*",
        month: "*",
        day: "*",
        hour: "*",
        minute: "*",
        second: "*",
      },
      expected: "* * * * * * 0",
    },
    {
      trigger: {
        year: "7",
        dayOfWeek: "6",
        month: "5",
        day: "4",
        hour: "3",
        minute: "2",
        second: "1",
      },
      expected: "1 2 3 4 5 6 7",
    },
  ])("renders cron test for $expected", async ({ trigger, expected }) => {
    const mockJob = {
      id: "1",
      name: "example_job",
      trigger_type: "cron",
      trigger: trigger as CronTrigger,
      coalesce: false,
      misfire_grace_time: 1,
      next_run_time: null,
      status: "RUNNING",
      max_instances: 1,
      timeout: 5,
    } as Job;

    vi.mocked(jobService.GetJob).mockResolvedValue(mockJob);
    vi.mocked(requestService.GetRequestList).mockResolvedValue([
      [],
      new Headers(),
    ]);

    render(
      <SnackbarProvider>
        <ConfirmDialogProvider>
          <SchedulerViewCard
            listeners={{}}
            jobId="1"
            editJob={() => {}}
            deleteJob={() => {}}
            config={{}}
          />
        </ConfirmDialogProvider>
      </SnackbarProvider>,
    );

    await waitFor(() => {
      expect(screen.getAllByRole("paragraph")[5]).toHaveTextContent("CRON");
      expect(screen.getAllByRole("paragraph")[6]).toHaveTextContent(
        `${expected}`,
      );
    });
  });

  test("renders Cron Scheduler View Card", async () => {
    const mockJob = {
      id: "1",
      name: "example_job",
      trigger_type: "interval",
      trigger: {
        weeks: undefined,
        days: undefined,
        hours: undefined,
        minutes: undefined,
        seconds: 5,
      } as IntervalTrigger,
      coalesce: false,
      misfire_grace_time: 1,
      next_run_time: null,
      status: "RUNNING",
      max_instances: 1,
      timeout: 5,
    } as Job;

    vi.mocked(jobService.GetJob).mockResolvedValue(mockJob);
    vi.mocked(requestService.GetRequestList).mockResolvedValue([
      [],
      new Headers(),
    ]);

    render(
      <SnackbarProvider>
        <ConfirmDialogProvider>
          <SchedulerViewCard
            listeners={{}}
            jobId="1"
            editJob={() => {}}
            deleteJob={() => {}}
            config={{}}
          />
        </ConfirmDialogProvider>
      </SnackbarProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("example_job")).toBeInTheDocument();
      expect(screen.getAllByRole("paragraph")[0]).toHaveTextContent("RUNNING");
      expect(screen.getAllByRole("paragraph")[1]).toHaveTextContent("False");
      expect(screen.getAllByRole("paragraph")[2]).toHaveTextContent("1");
      expect(screen.getAllByRole("paragraph")[3]).toHaveTextContent("1");
      expect(screen.getAllByRole("paragraph")[4]).toHaveTextContent("5");
      expect(screen.getAllByRole("paragraph")[5]).toHaveTextContent("INTERVAL");
      expect(screen.getAllByRole("paragraph")[6]).toHaveTextContent(
        "Every 5 Seconds",
      );
      expect(screen.getAllByRole("paragraph")[7]).toHaveTextContent("N/A");
      expect(screen.getAllByRole("paragraph")[8]).toHaveTextContent("N/A");
      expect(screen.getAllByRole("paragraph")[9]).toHaveTextContent("N/A");
      expect(screen.getAllByRole("paragraph")[10]).toHaveTextContent("N/A");
    });
  });

  it.each([
    {
      trigger: {
        seconds: 5,
      },
      expected: "Seconds",
    },
    {
      trigger: {
        minutes: 5,
      },
      expected: "Minutes",
    },
    {
      trigger: {
        hours: 5,
      },
      expected: "Hours",
    },
    {
      trigger: {
        days: 5,
      },
      expected: "Days",
    },
    {
      trigger: {
        weeks: 5,
      },
      expected: "Weeks",
    },
  ])("renders interval test for $expected", async ({ trigger, expected }) => {
    const mockJob = {
      id: "1",
      name: "example_job",
      trigger_type: "interval",
      trigger: trigger as IntervalTrigger,
      coalesce: false,
      misfire_grace_time: 1,
      next_run_time: null,
      status: "RUNNING",
      max_instances: 1,
      timeout: 5,
    } as Job;

    vi.mocked(jobService.GetJob).mockResolvedValue(mockJob);
    vi.mocked(requestService.GetRequestList).mockResolvedValue([
      [],
      new Headers(),
    ]);

    render(
      <SnackbarProvider>
        <ConfirmDialogProvider>
          <SchedulerViewCard
            listeners={{}}
            jobId="1"
            editJob={() => {}}
            deleteJob={() => {}}
            config={{}}
          />
        </ConfirmDialogProvider>
      </SnackbarProvider>,
    );

    await waitFor(() => {
      expect(screen.getAllByRole("paragraph")[5]).toHaveTextContent("INTERVAL");
      expect(screen.getAllByRole("paragraph")[6]).toHaveTextContent(
        `Every 5 ${expected}`,
      );
    });
  });

  test("renders Date Scheduler View Card", async () => {
    const mockJob = {
      id: "1",
      name: "example_job",
      trigger_type: "date",
      trigger: {
        run_date: "0",
        timezone: "UTC",
      } as DateTrigger,
      coalesce: false,
      misfire_grace_time: 1,
      next_run_time: null,
      status: "RUNNING",
      max_instances: 1,
      timeout: 5,
    } as Job;

    vi.mocked(jobService.GetJob).mockResolvedValue(mockJob);
    vi.mocked(requestService.GetRequestList).mockResolvedValue([
      [],
      new Headers(),
    ]);

    render(
      <SnackbarProvider>
        <ConfirmDialogProvider>
          <SchedulerViewCard
            listeners={{}}
            jobId="1"
            editJob={() => {}}
            deleteJob={() => {}}
            config={{}}
          />
        </ConfirmDialogProvider>
      </SnackbarProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("example_job")).toBeInTheDocument();
      expect(screen.getAllByRole("paragraph")[0]).toHaveTextContent("RUNNING");
      expect(screen.getAllByRole("paragraph")[1]).toHaveTextContent("False");
      expect(screen.getAllByRole("paragraph")[2]).toHaveTextContent("1");
      expect(screen.getAllByRole("paragraph")[3]).toHaveTextContent("1");
      expect(screen.getAllByRole("paragraph")[4]).toHaveTextContent("5");
      expect(screen.getAllByRole("paragraph")[5]).toHaveTextContent("DATE");
      expect(screen.getAllByRole("paragraph")[6]).toHaveTextContent(
        "1/1/2000 12:00:00 AM",
      );
      expect(screen.getAllByRole("paragraph")[7]).toHaveTextContent("UTC");
    });
  });

  test("renders Date Scheduler View Card", async () => {
    const mockJob = {
      id: "1",
      name: "example_job",
      trigger_type: "file",
      trigger: {
        path: "/path/to/files",
        pattern: "*.txt",
        recursive: true,
        create: true,
        modify: true,
        move: true,
        delete: true,
      } as FileTrigger,
      coalesce: false,
      misfire_grace_time: 1,
      next_run_time: null,
      status: "RUNNING",
      max_instances: 1,
      timeout: 5,
    } as Job;

    vi.mocked(jobService.GetJob).mockResolvedValue(mockJob);
    vi.mocked(requestService.GetRequestList).mockResolvedValue([
      [],
      new Headers(),
    ]);

    render(
      <SnackbarProvider>
        <ConfirmDialogProvider>
          <SchedulerViewCard
            listeners={{}}
            jobId="1"
            editJob={() => {}}
            deleteJob={() => {}}
            config={{}}
          />
        </ConfirmDialogProvider>
      </SnackbarProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("example_job")).toBeInTheDocument();
      expect(screen.getAllByRole("paragraph")[0]).toHaveTextContent("RUNNING");
      expect(screen.getAllByRole("paragraph")[1]).toHaveTextContent("False");
      expect(screen.getAllByRole("paragraph")[2]).toHaveTextContent("1");
      expect(screen.getAllByRole("paragraph")[3]).toHaveTextContent("1");
      expect(screen.getAllByRole("paragraph")[4]).toHaveTextContent("5");
      expect(screen.getAllByRole("paragraph")[5]).toHaveTextContent("FILE");
      expect(screen.getAllByRole("paragraph")[6]).toHaveTextContent(
        "/path/to/files",
      );
      expect(screen.getAllByRole("paragraph")[7]).toHaveTextContent("*.txt");
      expect(screen.getAllByRole("paragraph")[8]).toHaveTextContent("True");
      expect(screen.getAllByRole("paragraph")[9]).toHaveTextContent("True");
      expect(screen.getAllByRole("paragraph")[10]).toHaveTextContent("True");
      expect(screen.getAllByRole("paragraph")[11]).toHaveTextContent("True");
      expect(screen.getAllByRole("paragraph")[12]).toHaveTextContent("True");
    });
  });

  // Button Clicking
  test("Pause Button", async () => {
    const mockJob = {
      id: "1",
      name: "example_job",
      trigger_type: "cron",
      trigger: {
        year: "*",
        month: "*",
        day: "*",
        week: "*",
        dayOfWeek: "*",
        hour: "*",
        minute: "*",
        second: "*",
      } as CronTrigger,
      coalesce: false,
      misfire_grace_time: 1,
      next_run_time: null,
      status: "RUNNING",
      max_instances: 1,
      timeout: 5,
    } as Job;

    vi.mocked(jobService.GetJob).mockResolvedValue(mockJob);
    vi.mocked(requestService.GetRequestList).mockResolvedValue([
      [],
      new Headers(),
    ]);

    vi.mocked(jobService.PauseJob).mockResolvedValue({
      ...mockJob,
      status: "PAUSED",
    } as Job);

    render(
      <SnackbarProvider>
        <ConfirmDialogProvider>
          <SchedulerViewCard
            listeners={{}}
            jobId="1"
            editJob={() => {}}
            deleteJob={() => {}}
            config={{}}
          />
        </ConfirmDialogProvider>
      </SnackbarProvider>,
    );

    const pauseButton = await screen.findByRole("button", {
      name: /Pause Job/i,
    });
    await userEvent.click(pauseButton);

    await waitFor(() => {
      expect(screen.getByText("example_job")).toBeInTheDocument();
      expect(jobService.PauseJob).toHaveBeenCalled();
      expect(screen.getAllByRole("paragraph")[0]).toHaveTextContent("PAUSED");
    });
  });

  test("Resume Button", async () => {
    const mockJob = {
      id: "1",
      name: "example_job",
      trigger_type: "cron",
      trigger: {
        year: "*",
        month: "*",
        day: "*",
        week: "*",
        dayOfWeek: "*",
        hour: "*",
        minute: "*",
        second: "*",
      } as CronTrigger,
      coalesce: false,
      misfire_grace_time: 1,
      next_run_time: null,
      status: "PAUSED",
      max_instances: 1,
      timeout: 5,
    } as Job;

    vi.mocked(jobService.GetJob).mockResolvedValue(mockJob);
    vi.mocked(requestService.GetRequestList).mockResolvedValue([
      [],
      new Headers(),
    ]);

    vi.mocked(jobService.ResumeJob).mockResolvedValue({
      ...mockJob,
      status: "RUNNING",
    } as Job);

    render(
      <SnackbarProvider>
        <ConfirmDialogProvider>
          <SchedulerViewCard
            listeners={{}}
            jobId="1"
            editJob={() => {}}
            deleteJob={() => {}}
            config={{}}
          />
        </ConfirmDialogProvider>
      </SnackbarProvider>,
    );

    const resumeButton = await screen.findByRole("button", {
      name: /Resume Job/i,
    });

    await userEvent.click(resumeButton);

    await waitFor(() => {
      expect(screen.getByText("example_job")).toBeInTheDocument();
      expect(jobService.ResumeJob).toHaveBeenCalled();
      expect(screen.getAllByRole("paragraph")[0]).toHaveTextContent("RUNNING");
    });
  });

  test("Delete Button", async () => {
    const mockJob = {
      id: "1",
      name: "example_job",
      trigger_type: "cron",
      trigger: {
        year: "*",
        month: "*",
        day: "*",
        week: "*",
        dayOfWeek: "*",
        hour: "*",
        minute: "*",
        second: "*",
      } as CronTrigger,
      coalesce: false,
      misfire_grace_time: 1,
      next_run_time: null,
      status: "PAUSED",
      max_instances: 1,
      timeout: 5,
    } as Job;

    vi.mocked(jobService.GetJob).mockResolvedValue(mockJob);
    vi.mocked(requestService.GetRequestList).mockResolvedValue([
      [],
      new Headers(),
    ]);

    const deleteJobMock = vi.fn().mockResolvedValue({} as Job);

    // Simulate ConfirmDialog in parent (i.e. App.tsx)
    render(
      <SnackbarProvider>
        <ConfirmDialogProvider>
          <SchedulerViewCard
            listeners={{}}
            jobId="1"
            editJob={() => {}}
            deleteJob={deleteJobMock}
            config={{}}
          />
        </ConfirmDialogProvider>
      </SnackbarProvider>,
    );

    const deleteButton = await screen.findByRole("button", {
      name: /Delete Job/i,
    });
    await userEvent.click(deleteButton);
    await userEvent.click(screen.getByRole("button", { name: /Accept/i }));

    await waitFor(() => {
      expect(screen.getByText("example_job")).toBeInTheDocument();
      expect(deleteJobMock).toHaveBeenCalled();
    });
  });

  test("Run Now Button", async () => {
    const mockJob = {
      id: "1",
      name: "example_job",
      trigger_type: "cron",
      trigger: {
        year: "*",
        month: "*",
        day: "*",
        week: "*",
        dayOfWeek: "*",
        hour: "*",
        minute: "*",
        second: "*",
      } as CronTrigger,
      coalesce: false,
      misfire_grace_time: 1,
      next_run_time: null,
      status: "PAUSED",
      max_instances: 1,
      timeout: 5,
    } as Job;

    vi.mocked(jobService.GetJob).mockResolvedValue(mockJob);
    vi.mocked(requestService.GetRequestList).mockResolvedValue([
      [],
      new Headers(),
    ]);

    vi.mocked(jobService.RunAdhocJob);

    render(
      <SnackbarProvider>
        <ConfirmDialogProvider>
          <SchedulerViewCard
            listeners={{}}
            jobId="1"
            editJob={() => {}}
            deleteJob={() => {}}
            config={{}}
          />
        </ConfirmDialogProvider>
      </SnackbarProvider>,
    );

    const runNowButton = await screen.findByRole("button", {
      name: /Run Now/i,
    });
    await userEvent.click(runNowButton);

    await waitFor(() => {
      expect(screen.getByText("example_job")).toBeInTheDocument();
      expect(jobService.RunAdhocJob).toHaveBeenCalled();
    });
  });

  // Request Population Testing

  test("View Requests", async () => {
    const mockJob = {
      id: "1",
      name: "example_job",
      trigger_type: "cron",
      trigger: {
        year: "*",
        month: "*",
        day: "*",
        week: "*",
        dayOfWeek: "*",
        hour: "*",
        minute: "*",
        second: "*",
      } as CronTrigger,
      coalesce: false,
      misfire_grace_time: 1,
      next_run_time: null,
      status: "PAUSED",
      max_instances: 1,
      timeout: 5,
    } as Job;

    const mockRequest = {
      id: "1",
      command: "example_command",
      arguments: {},
      status: "SUCCESS",
      created_at: "0",
    } as Request;

    vi.mocked(jobService.GetJob).mockResolvedValue(mockJob);
    vi.mocked(requestService.GetRequestList).mockResolvedValue([
      [mockRequest],
      new Headers(),
    ]);

    render(
      <SnackbarProvider>
        <ConfirmDialogProvider>
          <SchedulerViewCard
            listeners={{}}
            jobId="1"
            editJob={() => {}}
            deleteJob={() => {}}
            config={{}}
          />
        </ConfirmDialogProvider>
      </SnackbarProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("example_job")).toBeInTheDocument();
      expect(screen.getByText("example_command")).toBeInTheDocument();
      expect(screen.getByText("SUCCESS")).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /Open Request/i }),
      ).toBeInTheDocument();
    });
  });
});
