import { useMemo } from "react";
import { useSearchParams } from "react-router-dom";

import { RequestCommand } from "../models/models";

function AppParams({ addRequestItem }: { addRequestItem: any }) {
  const [searchParams, _setSearchParams] = useSearchParams();

  useMemo(() => {
    const paramsNamespace = searchParams.get("namespace") ?? undefined;
    const paramsSystem = searchParams.get("system") ?? undefined;
    const paramsSystemVersion = searchParams.get("system_version") ?? undefined;
    const paramsInstanceName = searchParams.get("instance_name") ?? undefined;
    const paramsCommand = searchParams.get("command") ?? undefined;

    if (
      paramsNamespace ||
      paramsSystem ||
      paramsSystemVersion ||
      paramsInstanceName ||
      paramsCommand
    ) {
      addRequestItem({
        type: "REQUEST",
        requestCommandInput: {
          namespace: paramsNamespace,
          systemName: paramsSystem,
          version: paramsSystemVersion,
          instance: paramsInstanceName,
          command: paramsCommand,
        } as RequestCommand,
      });
    }
  }, []);

  return null;
}

export default AppParams;
