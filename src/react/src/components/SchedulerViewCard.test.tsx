import {
  cleanup,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, test, vi } from "vitest";

import {
  CronTrigger,
  DateTrigger,
  FileTrigger,
  IntervalTrigger,
  Job,
} from "../models/brewtils-types";
import { Config } from "../models/models";
import * as jobService from "../services/job_service";
import * as requestService from "../services/request_service";
import * as utilService from "../services/util_service";
import SchedulerViewCard from "./SchedulerViewCard";

vi.mock("../services/job_service");
vi.mock("../services/request_service");
vi.mock("../services/util_service");

describe("SchedulerViewCard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    cleanup();
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
      <SchedulerViewCard
        listeners={{}}
        jobId="1"
        editJob={() => {}}
        deleteJob={() => {}}
        removeItem={() => {}}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText("example_job")).toBeInTheDocument();
      expect(screen.getAllByRole("paragraph")[0]).toHaveTextContent(
        "Status:RUNNING",
      );
      expect(screen.getAllByRole("paragraph")[1]).toHaveTextContent(
        "Coalesce:False",
      );
      expect(screen.getAllByRole("paragraph")[2]).toHaveTextContent(
        "Misfire Grace Time:1",
      );
      expect(screen.getAllByRole("paragraph")[3]).toHaveTextContent(
        "Max Instances:1",
      );
      expect(screen.getAllByRole("paragraph")[4]).toHaveTextContent(
        "Timeout:5",
      );
      expect(screen.getAllByRole("paragraph")[5]).toHaveTextContent(
        "Trigger Type:CRON",
      );
      expect(screen.getAllByRole("paragraph")[6]).toHaveTextContent(
        "Cron Expression:* * * * * * *",
      );
      expect(screen.getAllByRole("paragraph")[7]).toHaveTextContent(
        "Start Date:N/A",
      );
      expect(screen.getAllByRole("paragraph")[8]).toHaveTextContent(
        "End Date:N/A",
      );
      expect(screen.getAllByRole("paragraph")[9]).toHaveTextContent(
        "Timezone:N/A",
      );
      expect(screen.getAllByRole("paragraph")[10]).toHaveTextContent(
        "Jitter:N/A",
      );
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
      <SchedulerViewCard
        listeners={{}}
        jobId="1"
        editJob={() => {}}
        deleteJob={() => {}}
        removeItem={() => {}}
      />,
    );

    await waitFor(() => {
      expect(screen.getAllByRole("paragraph")[5]).toHaveTextContent(
        "Trigger Type:CRON",
      );
      expect(screen.getAllByRole("paragraph")[6]).toHaveTextContent(
        `Cron Expression:${expected}`,
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
      <SchedulerViewCard
        listeners={{}}
        jobId="1"
        editJob={() => {}}
        deleteJob={() => {}}
        removeItem={() => {}}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText("example_job")).toBeInTheDocument();
      expect(screen.getAllByRole("paragraph")[0]).toHaveTextContent(
        "Status:RUNNING",
      );
      expect(screen.getAllByRole("paragraph")[1]).toHaveTextContent(
        "Coalesce:False",
      );
      expect(screen.getAllByRole("paragraph")[2]).toHaveTextContent(
        "Misfire Grace Time:1",
      );
      expect(screen.getAllByRole("paragraph")[3]).toHaveTextContent(
        "Max Instances:1",
      );
      expect(screen.getAllByRole("paragraph")[4]).toHaveTextContent(
        "Timeout:5",
      );
      expect(screen.getAllByRole("paragraph")[5]).toHaveTextContent(
        "Trigger Type:INTERVAL",
      );
      expect(screen.getAllByRole("paragraph")[6]).toHaveTextContent(
        "Interval:Every 5 Seconds",
      );
      expect(screen.getAllByRole("paragraph")[7]).toHaveTextContent(
        "Start Date:N/A",
      );
      expect(screen.getAllByRole("paragraph")[8]).toHaveTextContent(
        "End Date:N/A",
      );
      expect(screen.getAllByRole("paragraph")[9]).toHaveTextContent(
        "Timezone:N/A",
      );
      expect(screen.getAllByRole("paragraph")[10]).toHaveTextContent(
        "Jitter:N/A",
      );
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
      <SchedulerViewCard
        listeners={{}}
        jobId="1"
        editJob={() => {}}
        deleteJob={() => {}}
        removeItem={() => {}}
      />,
    );

    await waitFor(() => {
      expect(screen.getAllByRole("paragraph")[5]).toHaveTextContent(
        "Trigger Type:INTERVAL",
      );
      expect(screen.getAllByRole("paragraph")[6]).toHaveTextContent(
        `Interval:Every 5 ${expected}`,
      );
    });
  });

  test("renders Date Scheduler View Card", async () => {
    const mockJob = {
      id: "1",
      name: "example_job",
      trigger_type: "date",
      trigger: {
        runDate: "0",
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
      <SchedulerViewCard
        listeners={{}}
        jobId="1"
        editJob={() => {}}
        deleteJob={() => {}}
        removeItem={() => {}}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText("example_job")).toBeInTheDocument();
      expect(screen.getAllByRole("paragraph")[0]).toHaveTextContent(
        "Status:RUNNING",
      );
      expect(screen.getAllByRole("paragraph")[1]).toHaveTextContent(
        "Coalesce:False",
      );
      expect(screen.getAllByRole("paragraph")[2]).toHaveTextContent(
        "Misfire Grace Time:1",
      );
      expect(screen.getAllByRole("paragraph")[3]).toHaveTextContent(
        "Max Instances:1",
      );
      expect(screen.getAllByRole("paragraph")[4]).toHaveTextContent(
        "Timeout:5",
      );
      expect(screen.getAllByRole("paragraph")[5]).toHaveTextContent(
        "Trigger Type:DATE",
      );
      expect(screen.getAllByRole("paragraph")[6]).toHaveTextContent(
        "Run Date:1/1/2000 12:00:00 AM",
      );
      expect(screen.getAllByRole("paragraph")[7]).toHaveTextContent(
        "Timezone:UTC",
      );
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
      <SchedulerViewCard
        listeners={{}}
        jobId="1"
        editJob={() => {}}
        deleteJob={() => {}}
        removeItem={() => {}}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText("example_job")).toBeInTheDocument();
      expect(screen.getAllByRole("paragraph")[0]).toHaveTextContent(
        "Status:RUNNING",
      );
      expect(screen.getAllByRole("paragraph")[1]).toHaveTextContent(
        "Coalesce:False",
      );
      expect(screen.getAllByRole("paragraph")[2]).toHaveTextContent(
        "Misfire Grace Time:1",
      );
      expect(screen.getAllByRole("paragraph")[3]).toHaveTextContent(
        "Max Instances:1",
      );
      expect(screen.getAllByRole("paragraph")[4]).toHaveTextContent(
        "Timeout:5",
      );
      expect(screen.getAllByRole("paragraph")[5]).toHaveTextContent(
        "Trigger Type:FILE",
      );
      expect(screen.getAllByRole("paragraph")[6]).toHaveTextContent(
        "Path:/path/to/files",
      );
      expect(screen.getAllByRole("paragraph")[7]).toHaveTextContent(
        "Pattern:*.txt",
      );
      expect(screen.getAllByRole("paragraph")[8]).toHaveTextContent(
        "Recursive:True",
      );
      expect(screen.getAllByRole("paragraph")[9]).toHaveTextContent(
        "Create:True",
      );
      expect(screen.getAllByRole("paragraph")[10]).toHaveTextContent(
        "Modify:True",
      );
      expect(screen.getAllByRole("paragraph")[11]).toHaveTextContent(
        "Delete:True",
      );
      expect(screen.getAllByRole("paragraph")[12]).toHaveTextContent(
        "Move:True",
      );
    });
  });

  // TODO Request Population Testing

  // Button Clicking
});
