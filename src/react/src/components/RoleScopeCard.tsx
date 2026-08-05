import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  Autocomplete,
  Box,
  Card,
  CardContent,
  FormLabel,
  TextField,
} from "@mui/material";
import { grey } from "@mui/material/colors";
import React, { useEffect, useRef, useState } from "react";
import { CardHeader } from "react-bootstrap";

import { useSnackbar } from "../providers/SnackbarProvider";
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

  const showSnackbar = useSnackbar();

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
        setFilteredItems(items.current);
      })
      .catch((error) => {
        console.error("Error fetching system list:", error);
        showSnackbar({
          severity: "error",
          summary: "Error",
          detail: `Error fetching system list: ${error}`,
          life: 3000,
        });
      });
  }, []);

  function header(index: number) {
    if (disabled) {
      return <></>;
    }
    return (
      <Box sx={{ display: "flex", justifyContent: "flex-end", p: 1 }}>
        <AccessButton tooltip="Remove" onClick={() => handleClose(index)}>
          <FontAwesomeIcon icon="close" />
        </AccessButton>
      </Box>
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

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
      <FormLabel sx={{ fontWeight: "bold" }} htmlFor={`${scopeName}Scopes`}>
        {scopeName.charAt(0).toUpperCase() + scopeName.slice(1)} Scopes
      </FormLabel>
      <div id={`${scopeName}Scopes`}>
        {scopeList.map((item, index) => (
          <>
            <Card
              key={index}
              variant="outlined"
              sx={{ borderColor: grey[600] }}
            >
              <CardHeader>{header(index)}</CardHeader>
              <CardContent>
                <Autocomplete
                  sx={{ m: 2 }}
                  id={`${scopeName}Scope-${index}`}
                  options={filteredItems}
                  value={item ?? null}
                  onChange={(_event: any, newValue: string | null) => {
                    handleUpdateScope(
                      newValue === null ? undefined : newValue,
                      index,
                    );
                  }}
                  disabled={disabled}
                  renderInput={(params) => (
                    <TextField {...params} label="Scope" />
                  )}
                />
              </CardContent>
            </Card>
          </>
        ))}
        {!disabled && (
          <Box sx={{ display: "flex" }}>
            <AccessButton
              sx={{ mt: 1, mb: 3 }}
              label={`Add ${scopeName}`}
              onClick={handleAddScope}
            >{`Add ${scopeName}`}</AccessButton>
          </Box>
        )}
      </div>
    </Box>
  );
}

export default RoleScopeCard;
