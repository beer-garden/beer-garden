import { Button } from "primereact/button";
import { Column } from "primereact/column";
import { DataTable } from "primereact/datatable";
import { Dropdown } from "primereact/dropdown";
import { Stepper } from "primereact/stepper";
import { RefObject, useEffect, useRef, useState } from "react";

import { Command, Instance, System } from "../models/brewtils-types";

function CommandList({
  stepperRef,
  selectedSystem,
  setSelectedCommand,
  instances,
  selectedInstance,
  setSelectedInstance,
}: {
  stepperRef: RefObject<Stepper | null>;
  selectedSystem?: System;
  setSelectedCommand: any;
  instances: Array<Record<string, any>>;
  selectedInstance: Instance;
  setSelectedInstance: any;
}) {
  const [commands, setCommands] = useState<Command[]>([]);
  // const [instances, setInstances] = useState<Array<Instance>>();
  // const instanceList: Array<any> = [];
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

  function actionTemplate(command: Command) {
    return (
      <Button
        disabled={buttonsDisabled.current}
        onClick={() => {
          setSelectedCommand(command);
          stepperRef.current?.nextCallback();
        }}
      >
        Make It So!
      </Button>
    );
  }

  //Get a list of commands and output them to a table
  return (
    <>
      <label htmlFor="instanceSelect" className="mr-2 font-semibold">
        Instance:
      </label>
      <Dropdown
        id="instanceSelect"
        className="mb-2"
        value={selectedInstance}
        placeholder="Select Instance"
        onChange={(e) => {
          setSelectedInstance(e.value);
          buttonsDisabled.current = false;
        }}
        invalid={!selectedInstance || undefined}
        options={instances}
      />
      <DataTable
        key={buttonsDisabled.current}
        value={commands}
        paginator
        rows={10}
      >
        <Column field="name" header="Command" />
        <Column field="description" header="Description" />
        <Column header="Actions" body={actionTemplate} />
      </DataTable>
    </>
  );
}

export default CommandList;
