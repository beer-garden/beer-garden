import { RequestItem } from "../models/models";
import { DeleteJob } from "../services/job_service";
import RequestCreateCard from "./RequestCreateCard";
import RequestViewCard from "./RequestViewCard";
import SchedulerViewCard from "./SchedulerViewCard";

function RequestItemCard({
  requestItem,
  listeners,
  updateRequestItem,
  removeItem,
  addItem,
}: {
  requestItem: RequestItem;
  listeners: Record<string, any>;
  updateRequestItem: (item: RequestItem) => void;
  removeItem: (id: string) => void;
  addItem: (itemParams?: Partial<RequestItem>) => void;
}) {
  return (
    <>
      {requestItem?.type === "REQUEST" && (
        <RequestCreateCard
          requestItem={requestItem}
          updateRequestItem={updateRequestItem}
          removeItem={removeItem}
        />
      )}
      {requestItem?.type === "VIEW_REQUEST" && (
        <RequestViewCard
          requestItem={requestItem}
          updateRequestItem={updateRequestItem}
          removeItem={removeItem}
          listeners={listeners}
          addItem={addItem}
        />
      )}

      {requestItem?.type === "VIEW_JOB" && requestItem?.jobId && (
        <SchedulerViewCard
          jobId={requestItem.jobId}
          removeItem={removeItem}
          listeners={listeners}
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
