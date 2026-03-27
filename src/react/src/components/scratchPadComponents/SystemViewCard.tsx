import { useEffect, useRef, useState } from "react";

import { Instance, System } from "../../models/brewtils-types";
import { ScratchPadValue } from "../../models/models";
import { GetSystem } from "../../services/system_service";
import SystemCard from "../SystemCard";

function SystemViewCard({
  padItem,
  updatePadItem,
  removePadItem,
  reloadScratchPad,
  listeners,
}: {
  padItem: ScratchPadValue;
  updatePadItem: (padItem: ScratchPadValue) => void;
  removePadItem: (padItem: ScratchPadValue) => void;
  reloadScratchPad: () => void;
  listeners: Record<string, any>;
}) {
  const systemId = useRef<string | null | undefined>(null);
  const [system, setSystem] = useState<System | null>(
    padItem?.values?.system ? padItem.values.system : null,
  );

  if (!system) {
    return;
  }

  const updateScratchPadValues = () => {
    updatePadItem({
      ...padItem,
      values: {
        ...padItem.values,
        system: system,
        systemId: systemId,
      },
    });
  };

  const MonitorSystemId = (message: any) => {
    if (message.payload_type === "System") {
      if (
        systemId.current &&
        message.payload.id &&
        message.payload.id === systemId.current
      ) {
        if (message.name === "SYSTEM_REMOVED") {
          removePadItem(padItem);
        } else {
          setSystem(message.payload as System);
          updateScratchPadValues();
        }
      }
    }
    if (message.payload_type === "Instance") {
      if (system && systemId.current && message.payload.id) {
        if (system.instances) {
          const inst_index = system.instances.findIndex(
            (i) => i.id == message.payload.id,
          );
          if (inst_index > -1) {
            // Update on status changes
            if (system.instances[inst_index].status != message.payload.status) {
              system.instances[inst_index] = message.payload as Instance;
              setSystem(system);
              updateScratchPadValues();
              // Must call this to force scratchpad to trigger reload
              reloadScratchPad();
            }
          }
        }
      }
    }
  };

  if (!systemId.current) {
    systemId.current = padItem?.values?.systemId
      ? padItem.values.systemId
      : null;
  }

  useEffect(() => {
    if (!system && systemId.current) {
      GetSystem(systemId.current, {})
        .then((data: System) => {
          setSystem(data);
          updateScratchPadValues();

          if (systemId.current && !(systemId.current in listeners)) {
            listeners[systemId.current] = {
              listener: MonitorSystemId,
            };
          }
        })
        .catch((error) => {
          console.error("Error fetching system:", error);
        });
    }

    if (system && systemId.current && !(systemId.current in listeners)) {
      listeners[systemId.current] = {
        listener: MonitorSystemId,
      };
    }

    return () => {
      if (systemId.current) {
        delete listeners[systemId.current];
      }
    };
  }, [system, listeners, padItem, updatePadItem]);

  return <SystemCard system={system} />;
}

export default SystemViewCard;
