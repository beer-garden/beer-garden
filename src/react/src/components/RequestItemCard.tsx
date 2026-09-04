import { useState } from "react";

import { Config, RequestItem } from "../models/models";
import { useSnackbar } from "../providers/SnackbarProvider";
import { DeleteJob } from "../services/job_service";
import RequestCreateCard from "./RequestCreateCard";
import RequestViewCard from "./RequestViewCard";
import RequestWizard from "./RequestWizard";
import SchedulerViewCard from "./SchedulerViewCard";
import TopicCard from "./TopicCard";

function RequestItemCard({
  requestItem,
  listeners,
  updateRequestItem,
  removeItem,
  isDialog,
  config,
}: {
  requestItem: RequestItem;
  listeners: Record<string, any>;
  updateRequestItem: (itemParams?: Partial<RequestItem>) => void;
  removeItem: (id?: string) => void;
  isDialog: boolean;
  config: Config;
}) {
  const [useWizard] = useState<boolean>(
    localStorage.getItem("user_advanced") === "true" ? false : true,
  );

  const showSnackbar = useSnackbar();

  return (
    <>
      {requestItem?.type === "REQUEST" && useWizard && (
        <RequestWizard
          requestItem={requestItem}
          updateRequestItem={updateRequestItem}
          config={config}
        />
      )}
      {requestItem?.type === "REQUEST" && !useWizard && (
        <RequestCreateCard
          requestItem={requestItem}
          updateRequestItem={updateRequestItem}
          config={config}
        />
      )}
      {requestItem?.type === "VIEW_REQUEST" && (
        <RequestViewCard
          requestItem={requestItem}
          updateRequestItem={updateRequestItem}
          removeItem={removeItem}
          listeners={listeners}
          isDialog={isDialog}
          config={config}
        />
      )}

      {requestItem?.type === "VIEW_JOB" && requestItem?.jobId && (
        <SchedulerViewCard
          jobId={requestItem.jobId}
          listeners={listeners}
          config={config}
          updateRequestItem={updateRequestItem}
          removeItem={removeItem}
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
                  showSnackbar({
                    severity: "error",
                    summary: "Error",
                    detail: `Error deleting job: ${error}`,
                    life: 3000,
                  });
                });
            }
          }}
        />
      )}
      {requestItem?.type === "VIEW_TOPIC" && requestItem?.topic && (
        <TopicCard
          requestItem={requestItem}
          removeItem={removeItem}
          listeners={listeners}
        />
      )}
    </>
  );
}

export default RequestItemCard;
