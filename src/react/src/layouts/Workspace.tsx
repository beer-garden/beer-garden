import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Button } from "primereact/button";
import { DataView } from "primereact/dataview";
import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { v4 as uuidv4 } from "uuid";

import RequestCreateCard from "../components/RequestCreateCard";
import RequestViewCard from "../components/RequestViewCard";
import { RequestItem } from "../models/models";

function Workspace({ listeners }: { listeners: Record<string, any> }) {
  const { requestId } = useParams<{ requestId: string }>();
  const { jobId } = useParams<{ jobId: string }>();
  const { display } = useParams<{ display: string }>();

  const { paramNamespace } = useParams<{ paramNamespace: string }>();
  const { paramSystem } = useParams<{ paramSystem: string }>();
  const { paramVersion } = useParams<{ paramVersion: string }>();
  const { paramInstance } = useParams<{ paramInstance: string }>();
  const { paramCommand } = useParams<{ paramCommand: string }>();

  const [items, setItems] = useState<RequestItem[] | undefined>(undefined);
  const requestItemsRef = useRef<RequestItem[] | undefined>(undefined);

  const [requestItemsKey, setRequestItemsKey] = useState("0");

  useEffect(() => {
    if (requestItemsRef.current === undefined) {
      const saved = localStorage.getItem("requestItems");

      const loadedItems = [] as RequestItem[];
      if (requestId) {
        loadedItems.push({
          itemId: uuidv4(),
          type: display ? "VIEW_REQUEST" : "REQUEST",
          requestId: requestId,
        });
      } else if (jobId) {
        loadedItems.push({
          itemId: uuidv4(),

          type: "REQUEST",
          jobId: jobId,
          showSchedule: true,
        });
      } else if (
        paramNamespace ||
        paramSystem ||
        paramVersion ||
        paramInstance ||
        paramCommand
      ) {
        loadedItems.push({
          itemId: uuidv4(),

          type: "REQUEST",
          requestCommandInput: {
            namespace: paramNamespace,
            systemName: paramSystem,
            version: paramVersion,
            instance: paramInstance,
            command: paramCommand,
          },
        });
      }

      if (saved) {
        updateItems([...loadedItems, ...JSON.parse(saved)]);
      } else {
        updateItems(loadedItems);
      }
    }
  });

  const updateItems = (updatedItems: RequestItem[]) => {
    requestItemsRef.current = updatedItems;
    setItems(requestItemsRef.current);
    localStorage.setItem(
      "requestItems",
      JSON.stringify(requestItemsRef.current),
    );
  };

  const addItem = (itemParams?: Partial<RequestItem>) => {
    const newItem: RequestItem = {
      itemId: uuidv4(),
      type: "REQUEST",
      ...itemParams,
    };
    if (requestItemsRef.current) {
      updateItems([...requestItemsRef.current, newItem]);
    } else {
      updateItems([newItem]);
    }
  };

  const updateItem = (updated: RequestItem) => {
    if (requestItemsRef.current) {
      updateItems(
        requestItemsRef.current.map((item) =>
          item.itemId === updated.itemId ? updated : item,
        ),
      );
    }
  };

  const deleteItem = (id: string) => {
    if (requestItemsRef.current) {
      // Need to determine if the item is the last item, if not then we need to redraw the entire list
      const lastIndex =
        requestItemsRef.current.findIndex((item) => item.itemId === id) ===
        requestItemsRef.current.length - 1;
      updateItems(requestItemsRef.current.filter((item) => item.itemId !== id));

      if (!lastIndex) {
        setRequestItemsKey(
          JSON.stringify(requestItemsRef.current.map((item) => item.itemId)),
        );
      }
    }
  };

  const listTemplate = () => {
    if (!items || items.length === 0) return null;

    const list = [] as Array<any>;

    items.forEach((value: RequestItem) => {
      if (value !== null && value !== undefined) {
        if (value.type === "REQUEST") {
          list.push(
            <RequestCreateCard
              requestItem={value}
              updateRequestItem={updateItem}
              removeItem={deleteItem}
            />,
          );
        } else if (value.type === "VIEW_REQUEST") {
          list.push(
            <RequestViewCard
              requestItem={value}
              updateRequestItem={updateItem}
              removeItem={deleteItem}
              listeners={listeners}
              addItem={addItem}
            />,
          );
        }
      }
    });

    return (
      <div className="flex-grow-1 flex-wrap grid grid-nogutter">{list}</div>
    );
  };

  return (
    <div>
      <h1>Workspace</h1>
      <Button onClick={() => addItem()}>
        <FontAwesomeIcon icon="file-pen" />
      </Button>

      <DataView
        value={items}
        listTemplate={listTemplate}
        layout="grid"
        key={requestItemsKey}
        style={{
          height: "auto", // Adjust height to auto
          width: "auto", // Adjust width to auto
          overflow: "visible", // Allow overflow to be visible
        }}
      />
    </div>
  );
}

export default Workspace;
