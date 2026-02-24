import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Button } from "primereact/button";
import { DataView } from "primereact/dataview";
import React, { useEffect, useState } from "react";

import { ScratchPadValue } from "../models/models";
import {
  GetScratchPadItems,
  PushToScratchPad,
  RemoveScratchPadItem,
  UpdateScratchPadItem,
} from "../services/scratchpad_service";
import { CompareObjects } from "../services/util_service";
import RequestCreateCard from "./scratchPadComponents/RequestCreateCard";
import RequestViewCard from "./scratchPadComponents/RequestViewCard";
import SystemViewCard from "./scratchPadComponents/SystemViewCard";

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

  const ScratchPadTemplate = (value: ScratchPadValue) => {
    if (value.padType === "REQUEST") {
      return (
        <RequestCreateCard
          padItem={value}
          updatePadItem={updatePadValue}
          reloadScratchPad={reloadScratchPad}
        />
      );
    } else if (value.padType === "REQUEST_VIEW") {
      return (
        <RequestViewCard
          padItem={value}
          updatePadItem={updatePadValue}
          reloadScratchPad={reloadScratchPad}
          listeners={listeners}
        />
      );
    } else if (value.padType === "SYSTEM_VIEW") {
      return (
        <SystemViewCard
          padItem={value}
          updatePadItem={updatePadValue}
          removePadItem={removePadItem}
          reloadScratchPad={reloadScratchPad}
          listeners={listeners}
        />
      );
    }
    return <div>ERROR</div>;
  };

  const updatePadValue = (padValue: ScratchPadValue) => {
    // Need to verify it is still in the list and changed
    if (
      scratchPadItems.some(
        (item) =>
          item.padId === padValue.padId && !CompareObjects(item, padValue),
      )
    ) {
      setScratchPadItems(UpdateScratchPadItem(padValue));
    }
  };

  const removePadItem = (padValue: ScratchPadValue) => {
    if (scratchPadItems.some((item) => item.padId === padValue.padId)) {
      setShowItems(false);
      setScratchPadItems(RemoveScratchPadItem(padValue.padId));
      setShowItems(true);
    }
  };

  const listTemplate = (items: any) => {
    if (!items || items.length === 0) return null;

    const list = [] as Array<any>;

    items.forEach((value: ScratchPadValue) => {
      if (value !== null && value !== undefined) {
        list.push(
          <div key={value.padId}>
            <Button
              onClick={() => {
                removePadItem(value);
              }}
            >
              <FontAwesomeIcon icon="minus" />
            </Button>
            {ScratchPadTemplate(value)}
          </div>,
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
