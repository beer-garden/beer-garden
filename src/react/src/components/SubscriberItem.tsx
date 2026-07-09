import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { AutoComplete } from "primereact/autocomplete";
import { Card } from "primereact/card";
import React, { useEffect, useRef, useState } from "react";

import { Subscriber } from "../models/brewtils-types";
import { useToast } from "../providers/ToastProvider";
import { GetSystemList } from "../services/system_service";
import AccessButton from "./AccessButton";

interface SubscriberItemProps {
  subscriberList: Array<Subscriber>;
  setSubscriberList: React.Dispatch<React.SetStateAction<Array<Subscriber>>>;
  isEdit: boolean;
}

function SubscriberItem({
  subscriberList,
  setSubscriberList,
  isEdit,
}: SubscriberItemProps) {
  const [filteredGardenItems, setFilteredGardenItems] = useState(
    [] as Array<string>,
  );
  const [filteredNamespaceItems, setFilteredNamespaceItems] = useState(
    [] as Array<string>,
  );
  const [filteredSystemItems, setFilteredSystemItems] = useState(
    [] as Array<string>,
  );
  const [filteredVersionItems, setFilteredVersionItems] = useState(
    [] as Array<string>,
  );
  const [filteredInstanceItems, setFilteredInstanceItems] = useState(
    [] as Array<string>,
  );
  const [filteredCommandItems, setFilteredCommandItems] = useState(
    [] as Array<string>,
  );
  const gardenItems = useRef<Array<string>>([]);
  const namespaceItems = useRef<Array<string>>([]);
  const systemItems = useRef<Array<string>>([]);
  const versionItems = useRef<Array<string>>([]);
  const instanceItems = useRef<Array<string>>([]);
  const commandItems = useRef<Array<string>>([]);

  const showToast = useToast();

  useEffect(() => {
    GetSystemList()
      .then((data) => {
        //Gardens
        const gardens = new Set(
          data
            .map((system) => system.garden_name)
            .filter((item) => item !== undefined),
        );
        gardenItems.current = Array.from(gardens);
        //Namespaces
        const namespaces = new Set(
          data
            .map((system) => system.namespace)
            .filter((item) => item !== undefined),
        );
        namespaceItems.current = Array.from(namespaces);
        //Systems
        const systems = new Set(
          data
            .map((system) => system.name)
            .filter((item) => item !== undefined),
        );
        systemItems.current = Array.from(systems);
        //Versions
        const versions = new Set(
          data
            .map((system) => system.version)
            .filter((item) => item !== undefined),
        );
        versionItems.current = Array.from(versions);
        //Instance
        const instances = new Set(
          data
            .map((system) => system.instances?.map((i) => i?.name))
            .flat()
            .filter((item) => item !== undefined),
        );
        instanceItems.current = Array.from(instances);
        const commands = new Set(
          data
            .map((system) => system.commands?.map((i) => i?.name))
            .flat()
            .filter((item) => item !== undefined),
        );
        commandItems.current = Array.from(commands);
      })
      .catch((error) => {
        console.error("Error fetching system list:", error);
        showToast({
          severity: "error",
          summary: "Error",
          detail: `Error fetching system list: ${error}`,
          life: 3000,
        });
      });
  }, []);

  function header(index: number) {
    return (
      <div className="flex justify-content-between p-3 pb-0 items-end">
        <div className="flex flex-1"></div>
        {!isEdit && (
          <AccessButton tooltip="Remove" onClick={() => handleClose(index)}>
            <FontAwesomeIcon icon="close" />
          </AccessButton>
        )}
      </div>
    );
  }

  function handleClose(indexToRemove: number) {
    setSubscriberList((currentList) => {
      return [
        ...currentList.slice(0, indexToRemove),
        ...currentList.slice(indexToRemove + 1),
      ];
    });
  }

  function handleAddSubscriber() {
    setSubscriberList([
      ...subscriberList,
      {
        namespace: "",
        garden: "",
        system: "",
        version: "",
        instance: "",
        command: "",
      } as Subscriber,
    ]);
  }

  function handleUpdateSubscriber(
    inputKey: "namespace" | "garden" | "system" | "version" | "instance",
    inputValue: any,
    inputIndex: number,
  ) {
    if (inputValue.trim()) {
      setSubscriberList((currentList) => {
        const newList = currentList.map((subscriber, index) => {
          if (index == inputIndex) {
            subscriber[inputKey] = inputValue;
          }
          return subscriber;
        });
        return newList;
      });
    }
  }

  const searchGardenItems = (event: any) => {
    if (gardenItems.current) {
      const query = event.query.toLowerCase();
      const filtered = gardenItems.current.filter((item) =>
        item.toLowerCase().includes(query),
      );
      setFilteredGardenItems(
        filtered.sort((a: string, b: string) => a.localeCompare(b)),
      );
    }
  };

  const searchNamespaceItems = (event: any) => {
    if (namespaceItems.current) {
      const query = event.query.toLowerCase();
      const filtered = namespaceItems.current.filter((item) =>
        item.toLowerCase().includes(query),
      );
      setFilteredNamespaceItems(
        filtered.sort((a: string, b: string) => a.localeCompare(b)),
      );
    }
  };

  const searchSystemItems = (event: any) => {
    if (systemItems.current) {
      const query = event.query.toLowerCase();
      const filtered = systemItems.current.filter((item) =>
        item.toLowerCase().includes(query),
      );
      setFilteredSystemItems(
        filtered.sort((a: string, b: string) => a.localeCompare(b)),
      );
    }
  };

  const searchVersionItems = (event: any) => {
    if (systemItems.current) {
      const query = event.query.toLowerCase();
      const filtered = versionItems.current.filter((item) =>
        item.toLowerCase().includes(query),
      );
      setFilteredVersionItems(
        filtered.sort((a: string, b: string) => a.localeCompare(b)),
      );
    }
  };

  const searchInstanceItems = (event: any) => {
    if (instanceItems.current) {
      const query = event.query.toLowerCase();
      const filtered = instanceItems.current.filter((item) =>
        item.toLowerCase().includes(query),
      );
      setFilteredInstanceItems(
        filtered.sort((a: string, b: string) => a.localeCompare(b)),
      );
    }
  };

  const searchCommandItems = (event: any) => {
    if (commandItems.current) {
      const query = event.query.toLowerCase();
      const filtered = commandItems.current.filter((item) =>
        item.toLowerCase().includes(query),
      );
      setFilteredCommandItems(
        filtered.sort((a: string, b: string) => a.localeCompare(b)),
      );
    }
  };

  return (
    <div className="flex flex-column gap-2">
      {!isEdit && (
        <label className="font-bold" htmlFor="subscribers">
          Subscribers
        </label>
      )}
      <div className="card" id="subscribers">
        {subscriberList.map((subscriber, index) => (
          <Card
            key={index}
            className="card flex flex-column gap-2 border-1"
            header={() => header(index)}
          >
            <div className="mb-2">
              <label className="font-bold flex" htmlFor={`garden-${index}`}>
                Garden
              </label>
              <datalist id="selectGardenDropdown" aria-hidden="true">
                {filteredGardenItems?.map((value: string) => (
                  <option key={value} value={value} />
                ))}
              </datalist>
              <AutoComplete
                dropdown
                id={`garden-${index}`}
                value={subscriber.garden}
                suggestions={filteredGardenItems}
                completeMethod={searchGardenItems}
                onChange={(e) =>
                  handleUpdateSubscriber("garden", e.target.value, index)
                }
                dropdownIcon="pi pi-chevron-down"
                pt={{
                  input: {
                    root: {
                      "aria-controls": "selectGardenDropdown",
                    },
                  },
                }}
              />
            </div>
            <div className="mb-2">
              <label className="font-bold flex" htmlFor={`namespace-${index}`}>
                Namespace
              </label>
              <datalist id="selectNamespaceDropdown" aria-hidden="true">
                {filteredNamespaceItems?.map((value: string) => (
                  <option key={value} value={value} />
                ))}
              </datalist>
              <AutoComplete
                dropdown
                id={`namespace-${index}`}
                value={subscriber.namespace}
                suggestions={filteredNamespaceItems}
                completeMethod={searchNamespaceItems}
                onChange={(e) =>
                  handleUpdateSubscriber("namespace", e.target.value, index)
                }
                dropdownIcon="pi pi-chevron-down"
                pt={{
                  input: {
                    root: {
                      "aria-controls": "selectNamespaceDropdown",
                    },
                  },
                }}
              />
            </div>
            <div className="mb-2">
              <label className="font-bold flex" htmlFor={`system-${index}`}>
                System
              </label>
              <datalist id="selectSystemDropdown" aria-hidden="true">
                {filteredSystemItems?.map((value: string) => (
                  <option key={value} value={value} />
                ))}
              </datalist>
              <AutoComplete
                dropdown
                id={`system-${index}`}
                value={subscriber.system}
                suggestions={filteredSystemItems}
                completeMethod={searchSystemItems}
                onChange={(e) =>
                  handleUpdateSubscriber("system", e.target.value, index)
                }
                dropdownIcon="pi pi-chevron-down"
                pt={{
                  input: {
                    root: {
                      "aria-controls": "selectSystemDropdown",
                    },
                  },
                }}
              />
            </div>
            <div className="mb-2">
              <label className="font-bold flex" htmlFor={`system-${index}`}>
                Version
              </label>
              <datalist id="selectVersionDropdown" aria-hidden="true">
                {filteredVersionItems?.map((value: string) => (
                  <option key={value} value={value} />
                ))}
              </datalist>
              <AutoComplete
                dropdown
                id={`version-${index}`}
                value={subscriber.version}
                suggestions={filteredVersionItems}
                completeMethod={searchVersionItems}
                onChange={(e) =>
                  handleUpdateSubscriber("version", e.target.value, index)
                }
                dropdownIcon="pi pi-chevron-down"
                pt={{
                  input: {
                    root: {
                      "aria-controls": "selectVersionDropdown",
                    },
                  },
                }}
              />
            </div>
            <div className="mb-2">
              <label className="font-bold flex" htmlFor={`system-${index}`}>
                Instance
              </label>
              <datalist id="selectInstanceDropdown" aria-hidden="true">
                {filteredInstanceItems?.map((value: string) => (
                  <option key={value} value={value} />
                ))}
              </datalist>
              <AutoComplete
                dropdown
                id={`instance-${index}`}
                value={subscriber.instance}
                suggestions={filteredInstanceItems}
                completeMethod={searchInstanceItems}
                onChange={(e) =>
                  handleUpdateSubscriber("instance", e.target.value, index)
                }
                dropdownIcon="pi pi-chevron-down"
                pt={{
                  input: {
                    root: {
                      "aria-controls": "selectInstanceDropdown",
                    },
                  },
                }}
              />
            </div>
            <div className="mb-2">
              <label className="font-bold flex" htmlFor={`system-${index}`}>
                Command
              </label>
              <datalist id="selectCommandDropdown" aria-hidden="true">
                {filteredCommandItems?.map((value: string) => (
                  <option key={value} value={value} />
                ))}
              </datalist>
              <AutoComplete
                dropdown
                id={`command-${index}`}
                value={subscriber.command}
                suggestions={filteredCommandItems}
                completeMethod={searchCommandItems}
                onChange={(e) =>
                  handleUpdateSubscriber("command", e.target.value, index)
                }
                dropdownIcon="pi pi-chevron-down"
                pt={{
                  input: {
                    root: {
                      "aria-controls": "selectCommandDropdown",
                    },
                  },
                }}
              />
            </div>
          </Card>
        ))}
        {!isEdit && (
          <div className="flex">
            <AccessButton
              className="mt-1 mb-3"
              label={"Add subscriber"}
              onClick={handleAddSubscriber}
            />
          </div>
        )}
      </div>
    </div>
  );
}

export default SubscriberItem;
