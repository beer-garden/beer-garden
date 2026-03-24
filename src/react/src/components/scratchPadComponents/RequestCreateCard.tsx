import { Card } from "primereact/card";
import { SplitButton } from "primereact/splitbutton";
import { Toast } from "primereact/toast";
import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import CommandCreate from "../../components/CommandCreate";
import { Request } from "../../models/brewtils-types";
import { ScratchPadValue } from "../../models/models";
import { RequestCommand } from "../../models/models";
import { PostRequest } from "../../services/request_service";
import { PushToScratchPad } from "../../services/scratchpad_service";
import { GetBaseURL } from "../../services/util_service";

function RequestCreateCard({
  padItem,
  updatePadItem,
  reloadScratchPad,
}: {
  padItem: ScratchPadValue;
  updatePadItem: (padItem: ScratchPadValue) => void;
  reloadScratchPad: () => void;
}) {
  const navigate = useNavigate();
  const [request, setRequest] = useState<Request | undefined>(
    padItem?.values?.request ? padItem.values.request : undefined,
  );

  const toast = useRef(null as null | any);

  // System Panel
  const [requestCommand, setRequestCommand] = useState<RequestCommand>(
    padItem?.values?.requestCommand
      ? padItem.values.requestCommand
      : {
          namespace: null,
          systemName: null,
          version: null,
          instance: null,
          command: null,
        },
  );

  const updateScratchPadValues = () => {
    updatePadItem({
      ...padItem,
      values: {
        ...padItem.values,
        requestCommand: requestCommand,
        request: request,
      },
    });
  };

  const submitRequest = (openRequest: boolean, addToScratchPad?: boolean) => {
    if (request) {
      PostRequest(request)
        .then((response_request) => {
          if (openRequest) {
            if (addToScratchPad) {
              PushToScratchPad("REQUEST_VIEW", {
                requestId: response_request.id,
                request: response_request,
              });
              reloadScratchPad();
            } else {
              navigate(`${GetBaseURL()}/request/${response_request.id}`);
            }
          } else {
            toast?.current?.show({
              severity: "info",
              summary: "Info",
              detail: "Request Created: " + response_request.id,
            });
          }
        })
        .catch((error) => {
          console.error("Error creating request:", error);
        });
    }
  };

  return (
    <Card title="Create Request">
      <Toast ref={toast} />
      <CommandCreate
        request={request}
        setRequest={setRequest}
        requestCommand={requestCommand}
        setRequestCommand={setRequestCommand}
        callback={updateScratchPadValues}
      />
      <SplitButton
        label="Run"
        icon="pi pi-plus"
        onClick={() => {
          submitRequest(false);
        }}
        model={[
          {
            label: " Run and Open",
            // icon: <FontAwesomeIcon icon="arrow-up-right-from-square" />,
            command: () => {
              submitRequest(true);
            },
          },
          {
            label: " Run and Add to Scratch Pad",
            // icon: <FontAwesomeIcon icon="arrow-up-from-bracket" />,
            command: () => {
              submitRequest(true, true);
            },
          },
        ]}
      />
    </Card>
  );
}

export default RequestCreateCard;
