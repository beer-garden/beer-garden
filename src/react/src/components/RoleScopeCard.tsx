import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Button } from "primereact/button";
import { Card } from "primereact/card";
import { InputText } from "primereact/inputtext";
import React from "react";

interface RoleScopeCardProps {
  scopeName: string;
  scopeList: Array<string>;
  setScopeList: React.Dispatch<React.SetStateAction<Array<string>>>;
}

function RoleScopeCard({
  scopeName,
  scopeList,
  setScopeList,
}: RoleScopeCardProps) {
  function handleClose(indexToRemove: number) {
    setScopeList((currentList) => {
      return [
        ...currentList.slice(0, indexToRemove),
        ...currentList.slice(indexToRemove + 1),
      ];
    });
  }

  function header(index: number) {
    return (
      <div className="flex justify-content-between p-3 pb-0 items-end">
        <div className="flex flex-1"></div>
        <Button tooltip="Remove" onClick={() => handleClose(index)}>
          <FontAwesomeIcon icon="close" />
        </Button>
      </div>
    );
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

  return (
    <div className="flex flex-column gap-2">
      <label htmlFor={`${scopeName}Scopes`}>
        {scopeName.charAt(0).toUpperCase() + scopeName.slice(1)} Scopes
      </label>
      <div className="card" id={`${scopeName}Scopes`}>
        {scopeList.map((item, index) => (
          <Card
            key={index}
            className="card flex flex-column gap-2"
            header={() => header(index)}
          >
            <label htmlFor={`${scopeName}Scope-${index}`}>Scope</label>
            <InputText
              id={`${scopeName}Scope-${index}`}
              value={item}
              onChange={(e) => handleUpdateScope(e.target.value, index)}
            />
          </Card>
        ))}
        <Button label="Add" onClick={handleAddScope} />
      </div>
    </div>
  );
}

export default RoleScopeCard;
