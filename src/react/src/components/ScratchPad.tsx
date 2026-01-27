import React, { useState, useEffect } from "react";
import { Button } from "primereact/button";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { DataView } from "primereact/dataview";

import RequestCreateCard from "./scratchPadComponents/RequestCreateCard";
import RequestViewCard from "./scratchPadComponents/RequestViewCard";

import {
  GetScratchPadItems,
  UpdateScratchPadItem,
  PushToScratchPad,
  RemoveScratchPadItem,
} from "../services/scratchpad_service";

function ScratchPad({
  listeners,
  reloadTrigger,
}: {
  listeners: Record<string, any>;
  reloadTrigger: any;
}) {
  const [scratchPadItems, setScratchPadItems] = useState(GetScratchPadItems());

  const reloadScratchPad = () => {
    setScratchPadItems(GetScratchPadItems());
  };

  const [showitems, setShowItems] = useState(true);

  const ScratchPadTemplate = (value: any, index: any) => {
    if (value.padType === "REQUEST") {
      return (
        <RequestCreateCard
          values={value.values}
          updateValues={(values) => {
            updateIndex(index, values);
          }}
        />
      );
    } else if (value.padType === "REQUEST_VIEW") {
      return (
        <RequestViewCard
          values={value.values}
          updateValues={(values) => {
            updateIndex(index, values);
          }}
          listeners={listeners}
        />
      );
    }
    return <div>ERROR</div>;
  };

  const updateIndex = (updateIndex: number, updateValue: any) => {
    setScratchPadItems(UpdateScratchPadItem(updateIndex, updateValue));
  };

  const removeIndex = (removeIndex: number) => {
    setShowItems(false);
    setScratchPadItems(RemoveScratchPadItem(removeIndex));
    setShowItems(true);
  };

  const listTemplate = (items: any) => {
    if (!items || items.length === 0) return null;

    let list = items.map((value: any, index: number) => {
      if (value !== null && value !== undefined) {
        return (
          <div>
            <Button
              onClick={() => {
                removeIndex(index);
              }}
            >
              <FontAwesomeIcon icon="minus" />
            </Button>
            {ScratchPadTemplate(value, index)}
          </div>
        );
      }
    });

    return <div className="grid grid-nogutter">{list}</div>;
  };

  useEffect(() => {
    localStorage.setItem("scratchPadItems", JSON.stringify(scratchPadItems));
  }, [scratchPadItems]);

  useEffect(() => {
    reloadScratchPad();
  }, [reloadTrigger]);

  const addRequest = () => {
    setScratchPadItems(PushToScratchPad("REQUEST", {}));
  };

  return (
    <div>
      <h2>Scratch Pad</h2>
      <Button onClick={() => addRequest()}>
        <FontAwesomeIcon icon="file-pen" />
      </Button>
      {showitems && (
        <DataView value={scratchPadItems} listTemplate={listTemplate} />
      )}
    </div>
  );
}

export default ScratchPad;
