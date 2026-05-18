import { useState } from "react";

import { Config, RequestItem } from "../models/models";
import { DeleteJob } from "../services/job_service";
import RequestCreateCard from "./RequestCreateCard";
import RequestViewCard from "./RequestViewCard";
import RequestWizard from "./RequestWizard";
import SchedulerViewCard from "./SchedulerViewCard";

function RequestItemCard({
  requestItem,
  listeners,
  updateRequestItem,
  removeItem,
  addItem,
  isDialog,
  config,
}: {
  requestItem: RequestItem;
  listeners: Record<string, any>;
  updateRequestItem: (item: RequestItem) => void;
  removeItem: (id: string) => void;
  addItem: (itemParams?: Partial<RequestItem>) => void;
  isDialog: boolean;
  config: Config;
}) {
  const [useWizard] = useState<boolean>(
    localStorage.getItem("user_advanced") === "true" ? false : true,
  );

  return (
    <>
      {requestItem?.type === "REQUEST" && useWizard && (
        <RequestWizard
          requestItem={requestItem}
          updateRequestItem={updateRequestItem}
          removeItem={removeItem}
          isDialog={isDialog}
          config={config}
        />
      )}
      {requestItem?.type === "REQUEST" && !useWizard && (
        <RequestCreateCard
          requestItem={requestItem}
          updateRequestItem={updateRequestItem}
          removeItem={removeItem}
          isDialog={isDialog}
          config={config}
        />
      )}
      {requestItem?.type === "VIEW_REQUEST" && (
        <RequestViewCard
          requestItem={requestItem}
          updateRequestItem={updateRequestItem}
          removeItem={removeItem}
          listeners={listeners}
          addItem={addItem}
          isDialog={isDialog}
          config={config}
        />
      )}

      {requestItem?.type === "VIEW_JOB" && requestItem?.jobId && (
        <SchedulerViewCard
          jobId={requestItem.jobId}
          removeItem={removeItem}
          listeners={listeners}
          isDialog={isDialog}
          config={config}
          editJob={() => {
            updateRequestItem({
              ...requestItem,
              type: "REQUEST",
            });
          }}
          deleteJob={() => {
            if (requestItem.jobId) {
              DeleteJob({ id: requestItem.jobId } as any)
                .then(() => {
                  removeItem(requestItem.itemId);
                })
                .catch((error) => {
                  console.error("Error deleting job:", error);
                });
            }
          }}
        />
      )}
    </>
  );
}

export default RequestItemCard;
