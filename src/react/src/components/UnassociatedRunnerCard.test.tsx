import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, test, vi } from "vitest";

import { Runner } from "../models/brewtils-types";
import { RunnerGroup } from "../models/models";
import { SnackbarProvider } from "../providers/SnackbarProvider";
import * as runnerService from "../services/runner_service";
import UnassociatedRunnerCard from "./UnassociatedRunnerCard";

vi.mock("../services/runner_service");

describe("UnassociatedRunnerCard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    cleanup();
  });

  const mock_runner_group = {
    path: "test/path",
    runners: [
      { id: "1", dead: true } as Runner,
      { id: "2", dead: false } as Runner,
    ],
  } as RunnerGroup;

  test("renders Runner Group", async () => {
    render(
      <SnackbarProvider>
        <UnassociatedRunnerCard runnerGroup={mock_runner_group} config={{}} />
      </SnackbarProvider>,
    );

    await waitFor(() => {
      expect(
        screen.getByText(`Unassociated Runners: ${mock_runner_group.path}`),
      ).toBeInTheDocument();
      expect(screen.getByText("DEAD")).toBeInTheDocument();
      expect(screen.getByText("UNRESPONSIVE")).toBeInTheDocument();
    });
  });

  test("renders Runner Group Stop", async () => {
    vi.mocked(runnerService.StopRunner);

    render(
      <SnackbarProvider>
        <UnassociatedRunnerCard runnerGroup={mock_runner_group} config={{}} />
      </SnackbarProvider>,
    );

    const target_button = await screen.findByTestId("STOP_GROUP");
    expect(target_button).toBeInTheDocument();

    await userEvent.click(target_button);

    await waitFor(() => {
      expect(runnerService.StopRunner).toBeCalledTimes(2);
    });
  });

  test("renders Runner Group Start", async () => {
    vi.mocked(runnerService.StartRunner);

    render(
      <SnackbarProvider>
        <UnassociatedRunnerCard runnerGroup={mock_runner_group} config={{}} />
      </SnackbarProvider>,
    );

    const target_button = await screen.findByTestId("START_GROUP");
    expect(target_button).toBeInTheDocument();

    await userEvent.click(target_button);

    await waitFor(() => {
      expect(runnerService.StartRunner).toBeCalledTimes(2);
    });
  });

  test("renders Runner Group Delete", async () => {
    vi.mocked(runnerService.RemoveRunner);

    render(
      <SnackbarProvider>
        <UnassociatedRunnerCard runnerGroup={mock_runner_group} config={{}} />
      </SnackbarProvider>,
    );

    const target_button = await screen.findByTestId("DELETE_GROUP");
    expect(target_button).toBeInTheDocument();

    await userEvent.click(target_button);

    await waitFor(() => {
      expect(runnerService.RemoveRunner).toBeCalledTimes(2);
    });
  });

  test("renders Runner Group Reload", async () => {
    vi.mocked(runnerService.ReloadRunner);

    render(
      <SnackbarProvider>
        <UnassociatedRunnerCard runnerGroup={mock_runner_group} config={{}} />
      </SnackbarProvider>,
    );

    const target_button = await screen.findByTestId("RELOAD_GROUP");
    expect(target_button).toBeInTheDocument();

    await userEvent.click(target_button);

    await waitFor(() => {
      expect(runnerService.ReloadRunner).toBeCalledTimes(1);
      expect(runnerService.ReloadRunner).toBeCalledWith(mock_runner_group.path);
    });
  });

  test("renders Runner Start", async () => {
    vi.mocked(runnerService.StartRunner);

    render(
      <SnackbarProvider>
        <UnassociatedRunnerCard runnerGroup={mock_runner_group} config={{}} />
      </SnackbarProvider>,
    );

    const target_button = await screen.findByTestId(
      `START_${mock_runner_group.runners[0].id}`,
    );
    expect(target_button).toBeInTheDocument();

    await userEvent.click(target_button);

    await waitFor(() => {
      expect(runnerService.StartRunner).toBeCalledTimes(1);
      expect(runnerService.StartRunner).toBeCalledWith(
        mock_runner_group.runners[0],
      );
    });
  });

  test("renders Runner Stop", async () => {
    vi.mocked(runnerService.StopRunner);

    render(
      <SnackbarProvider>
        <UnassociatedRunnerCard runnerGroup={mock_runner_group} config={{}} />
      </SnackbarProvider>,
    );

    const target_button = await screen.findByTestId(
      `STOP_${mock_runner_group.runners[0].id}`,
    );
    expect(target_button).toBeInTheDocument();

    await userEvent.click(target_button);

    await waitFor(() => {
      expect(runnerService.StopRunner).toBeCalledTimes(1);
      expect(runnerService.StopRunner).toBeCalledWith(
        mock_runner_group.runners[0],
      );
    });
  });

  test("renders Runner Delete", async () => {
    vi.mocked(runnerService.RemoveRunner);

    render(
      <SnackbarProvider>
        <UnassociatedRunnerCard runnerGroup={mock_runner_group} config={{}} />
      </SnackbarProvider>,
    );

    const target_button = await screen.findByTestId(
      `DELETE_${mock_runner_group.runners[0].id}`,
    );
    expect(target_button).toBeInTheDocument();

    await userEvent.click(target_button);

    await waitFor(() => {
      expect(runnerService.RemoveRunner).toBeCalledTimes(1);
      expect(runnerService.RemoveRunner).toBeCalledWith(
        mock_runner_group.runners[0],
      );
    });
  });
});
