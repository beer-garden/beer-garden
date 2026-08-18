import { Autocomplete, TextField } from "@mui/material";
import { useState } from "react";

import { System } from "../models/brewtils-types";
import {
  CompareVersions,
  DetermineLatestSystemVersion,
} from "../services/system_service";

function VersionList({
  system,
  systems,
  setSystems,
}: {
  system: System;
  systems: System[];
  setSystems: any;
}) {
  const versions = systems
    .filter((s) => s.namespace === system.namespace && s.name == system.name)
    .map((s) => s.version!)
    .sort((a: string, b: string) => {
      return CompareVersions(a, b);
    });

  const versionOptions = [...versions, "latest"];

  const [selectedVersion, setSelectedVersion] = useState<string | undefined>(
    getLatestVersion(system).version ?? undefined,
  );

  function getLatestVersion(system: System): System {
    return DetermineLatestSystemVersion(
      systems,
      system.name,
      system.namespace,
      undefined,
    );
  }

  return (
    <Autocomplete
      sx={{ width: "200px" }}
      id={`${system.name}-version`}
      options={versionOptions}
      disabled={!versionOptions}
      value={selectedVersion ?? null}
      onChange={(_event: any, newValue: string | null | undefined) => {
        const chosenVersion = newValue === null ? undefined : newValue;
        setSelectedVersion(chosenVersion);
        if (chosenVersion) {
          setSystems((prevSystems: System[]) =>
            prevSystems.map((sys: System) =>
              sys.name === system.name
                ? { ...sys, version: chosenVersion }
                : sys,
            ),
          );
        }
      }}
      renderInput={(params) => <TextField {...params} label="Version" />}
    />
  );
}

export default VersionList;
