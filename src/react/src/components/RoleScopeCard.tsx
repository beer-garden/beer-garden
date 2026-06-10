import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { AutoComplete } from "primereact/autocomplete";
import { Card } from "primereact/card";
import React, { useEffect, useRef, useState } from "react";

import { GetSystemList } from "../services/system_service";
import AccessButton from "./AccessButton";

interface RoleScopeCardProps {
  scopeName: string;
  scopeList: Array<string>;
  setScopeList: React.Dispatch<React.SetStateAction<Array<string>>>;
  disabled: boolean;
}

function RoleScopeCard({
  scopeName,
  scopeList,
  setScopeList,
  disabled,
}: RoleScopeCardProps) {
  const [filteredItems, setFilteredItems] = useState([] as Array<string>);
  const items = useRef<Array<string>>([]);

  useEffect(() => {
    GetSystemList()
      .then((data) => {
        if (scopeName == "garden") {
          const gardens = new Set(
            data
              .map((system) => system.garden_name)
              .filter((item) => item !== undefined),
          );
          items.current = Array.from(gardens);
        } else if (scopeName == "namespace") {
          const namespaces = new Set(
            data
              .map((system) => system.namespace)
              .filter((item) => item !== undefined),
          );
          items.current = Array.from(namespaces);
        } else if (scopeName == "system") {
          const systems = new Set(
            data
              .map((system) => system.name)
              .filter((item) => item !== undefined),
          );
          items.current = Array.from(systems);
        } else if (scopeName == "version") {
          const versions = new Set(
            data
              .map((system) => system.version)
              .filter((item) => item !== undefined),
          );
          items.current = Array.from(versions);
        } else if (scopeName == "instance") {
          const instances = new Set(
            data
              .map((system) => system.instances?.map((i) => i?.name))
              .flat()
              .filter((item) => item !== undefined),
          );
          items.current = Array.from(instances);
        } else if (scopeName == "command") {
          const commands = new Set(
            data
              .map((system) => system.commands?.map((i) => i?.name))
              .flat()
              .filter((item) => item !== undefined),
          );
          items.current = Array.from(commands);
        }
      })
      .catch((error) => {
        console.error("Error fetching system list:", error);
      });
  }, []);

  function header(index: number) {
    if (disabled) {
      return <></>;
    }
    return (
      <div className="flex justify-content-between p-3 pb-0 items-end">
        <div className="flex flex-1"></div>
        <AccessButton tooltip="Remove" onClick={() => handleClose(index)}>
          <FontAwesomeIcon icon="close" />
        </AccessButton>
      </div>
    );
  }

  function handleClose(indexToRemove: number) {
    setScopeList((currentList) => {
      return [
        ...currentList.slice(0, indexToRemove),
        ...currentList.slice(indexToRemove + 1),
      ];
    });
  }

  function handleAddScope() {
    setScopeList([...scopeList, ""]);
  }

  function handleUpdateScope(inputValue: any, inputIndex: number) {
    if (inputValue.trim()) {
      setScopeList((currentList) => {
        const newList = currentList.map((scope, index) => {
          if (index == inputIndex) {
            scope = inputValue;
          }
          return scope;
        });
        return newList;
      });
    }
  }

  const searchItems = (event: any) => {
    if (items.current) {
      const query = event.query.toLowerCase();
      const filtered = items.current.filter((item) =>
        item.toLowerCase().includes(query),
      );
      setFilteredItems(filtered);
    }
  };

  return (
    <div className="flex flex-column gap-2">
      <label className="font-bold" htmlFor={`${scopeName}Scopes`}>
        {scopeName.charAt(0).toUpperCase() + scopeName.slice(1)} Scopes
      </label>
      <div className="card" id={`${scopeName}Scopes`}>
        {scopeList.map((item, index) => (
          <Card
            key={index}
            className="card flex flex-column gap-2 border-1"
            header={() => header(index)}
          >
            <label className="font-bold" htmlFor={`${scopeName}Scope-${index}`}>
              Scope
            </label>
            <AutoComplete
              dropdown
              id={`${scopeName}Scope-${index}`}
              value={item}
              suggestions={filteredItems}
              completeMethod={searchItems}
              onChange={(e) => handleUpdateScope(e.target.value, index)}
              disabled={disabled}
            />
          </Card>
        ))}
        {!disabled && (
          <div className="flex">
            <AccessButton
              className="mt-1 mb-3"
              label={`Add ${scopeName}`}
              onClick={handleAddScope}
            />
          </div>
        )}
      </div>
    </div>
  );
}

export default RoleScopeCard;
