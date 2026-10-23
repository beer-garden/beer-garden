import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { DataView } from "primereact/dataview";
import { RefObject, useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { v4 as uuidv4 } from "uuid";

import AccessButton from "../components/AccessButton";
import RequestItemCard from "../components/RequestItemCard";
import { Config, RequestItem, TourStepProps } from "../models/models";
import {
  AddTourStep,
  ClearTourSteps,
  GenerateTourProps,
} from "../services/tour_service";

function Workspace({
  listeners,
  display,
  tourStepsRef,
  config,
}: {
  listeners: Record<string, any>;
  display?: boolean;
  tourStepsRef: RefObject<Array<TourStepProps>>;
  config: Config;
}) {
  const { requestId } = useParams<{ requestId: string }>();
  const { jobId } = useParams<{ jobId: string }>();

  const { defaultType } = useParams<{ defaultType: string }>();

  const { paramNamespace } = useParams<{ paramNamespace: string }>();
  const { paramSystem } = useParams<{ paramSystem: string }>();
  const { paramVersion } = useParams<{ paramVersion: string }>();
  const { paramInstance } = useParams<{ paramInstance: string }>();
  const { paramCommand } = useParams<{ paramCommand: string }>();

  const [items, setItems] = useState<RequestItem[] | undefined>(undefined);
  const requestItemsRef = useRef<RequestItem[] | undefined>(undefined);

  const [requestItemsKey, setRequestItemsKey] = useState("0");

  const tourUuid = "workspace_tour";
  const tourPrefix = "workspace";

  const addRequestTourStep: TourStepProps = {
    prefix: tourPrefix,
    uuid: tourUuid,
    label: "Add Request",
    content: "Create a new scheduled job to run requests on a schedule.",
    layer: "LAYOUT",
    pos: 0,
  };

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

          type: display ? "VIEW_JOB" : "REQUEST",
          jobId: jobId,
          showSchedule: true,
        });
      } else if (
        defaultType ||
        paramNamespace ||
        paramSystem ||
        paramVersion ||
        paramInstance ||
        paramCommand
      ) {
        loadedItems.push({
          itemId: uuidv4(),
          showSchedule:
            defaultType !== undefined &&
            defaultType.toLocaleLowerCase() === "job",
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

    AddTourStep(tourStepsRef, addRequestTourStep);

    return () => {
      ClearTourSteps(tourStepsRef, tourPrefix, tourUuid);
    };
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
      updateItems([newItem, ...requestItemsRef.current]);
    } else {
      updateItems([newItem]);
    }
  };

  const updateItem = (updated?: Partial<RequestItem>) => {
    if (requestItemsRef.current) {
      if (
        updated?.itemId &&
        requestItemsRef.current.some((item) => item.itemId === updated.itemId)
      ) {
        updateItems(
          requestItemsRef.current.map((item) =>
            item.itemId === updated?.itemId ? { ...item, ...updated } : item,
          ),
        );
      } else {
        addItem(updated);
      }
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
      list.push(
        <div
          key={value.itemId}
          className="mr-2 mb-2 mt-2"
          style={{ minWidth: "49%" }}
        >
          <RequestItemCard
            removeItem={deleteItem}
            updateRequestItem={updateItem}
            requestItem={value}
            listeners={listeners}
            isDialog={false}
            config={config}
          />
        </div>,
      );
    });

    return (
      <div className="flex-grow-1 flex-wrap grid grid-nogutter">{list}</div>
    );
  };

  return (
    <div>
      <h1>Workspace</h1>
      <AccessButton
        basic
        raised
        onClick={() => addItem()}
        aria-label="Add Request"
        tooltip="Add Request"
        {...GenerateTourProps(addRequestTourStep)}
      >
        <FontAwesomeIcon icon="file-pen" />
      </AccessButton>

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
