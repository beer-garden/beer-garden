import {
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  SelectChangeEvent,
} from "@mui/material";
import { useEffect, useMemo, useRef, useState } from "react";

import { Command, System } from "../models/brewtils-types";
import AccessButton from "./AccessButton";
import EnhancedTable from "./EnhancedTable/components/EnhancedTable";

function CommandList({
  selectedSystem,
  commandListButtonClick,
  instances,
  selectedInstance,
  setSelectedInstance,
}: {
  selectedSystem?: System;
  commandListButtonClick: any;
  instances: Array<Record<string, any>>;
  selectedInstance: Record<string, any> | undefined;
  setSelectedInstance: any;
}) {
  const [instance, setInstance] = useState<string>(
    selectedInstance?.name ?? "",
  );
  const [commands, setCommands] = useState<Command[]>([]);
  const commandList: Array<Command> = [];
  const buttonsDisabled = useRef<any>(
    selectedInstance &&
      instances.some(
        (i) => JSON.stringify(i) == JSON.stringify(selectedInstance),
      )
      ? false
      : true,
  );

  useEffect(() => {
    if (
      selectedInstance &&
      instances.some(
        (i) => JSON.stringify(i) == JSON.stringify(selectedInstance),
      )
    ) {
      setInstance(selectedInstance.name);
      buttonsDisabled.current = false;
    } else {
      buttonsDisabled.current = true;
    }
  }, [selectedInstance, instances]);

  useEffect(() => {
    if (selectedSystem) {
      if (selectedInstance) {
        buttonsDisabled.current = false;
      }
      if (selectedSystem.commands) {
        selectedSystem.commands.forEach((command: Command) => {
          if (command.name && !commandList.includes(command)) {
            commandList.push(command);
          }
        });
        setCommands(commandList);
      }
    }
  }, []);

  const sortedInstances = useMemo(() => {
    return [...instances].sort((a, b) => a.name.localeCompare(b.name));
  }, [instances]);

  function actionTemplate(command: Command) {
    return (
      <AccessButton
        disabled={buttonsDisabled.current}
        onClick={() => {
          commandListButtonClick(command);
        }}
        tooltip={`Select Command ${command.name}`}
        label="Select"
      >
        Select
      </AccessButton>
    );
  }

  const handleChangeInstance = (event: SelectChangeEvent) => {
    setInstance(event.target.value);
    setSelectedInstance({
      name: event.target.value,
      label: event.target.value,
    });
    buttonsDisabled.current = false;
  };

  //Get a list of commands and output them to a table
  return (
    <>
      <FormControl fullWidth>
        <InputLabel id="instance-label-select">Instance</InputLabel>
        <Select
          labelId="instance-label-select"
          id="instance-select"
          value={instance}
          label="instance"
          disabled={sortedInstances.length == 1}
          onChange={handleChangeInstance}
        >
          {sortedInstances.map((i) => (
            <MenuItem value={i.name}>{i.label}</MenuItem>
          ))}
        </Select>
      </FormControl>
      <EnhancedTable
        key={buttonsDisabled.current}
        data={commands}
        columns={[
          {
            id: "name",
            label: "Command",
            field: "name",
            sortable: true,
            filterable: true,
            isString: true,
          },
          {
            id: "description",
            label: "Description",
            field: "description",
            sortable: true,
            filterable: true,
            isString: true,
          },
          {
            id: "actions",
            label: "Actions",
            template: actionTemplate,
          },
        ]}
      />
    </>
  );
}

export default CommandList;
