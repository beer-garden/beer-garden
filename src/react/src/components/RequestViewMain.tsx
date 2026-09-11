import { Grid, Typography } from "@mui/material";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Chip from "@mui/material/Chip";
import Skeleton from "@mui/material/Skeleton";
import Tab from "@mui/material/Tab";
import Tabs from "@mui/material/Tabs";
import { useEffect, useRef, useState } from "react";

import CommandForm from "../components/CommandForm";
import { ColumnField } from "../components/EnhancedTable//models/EnhancedTableModels";
import EnhancedTable from "../components/EnhancedTable/components/EnhancedTable";
import RequestOptions from "../components/RequestOptions";
import RequestOutput from "../components/RequestOutput";
import { Request, System } from "../models/brewtils-types";
import { Config, RequestCommand, RequestItem } from "../models/models";
import { useSnackbar } from "../providers/SnackbarProvider";
import { GetRequestProjections } from "../services/request_service";
import { GetSystemList } from "../services/system_service";
import { GetSeverity } from "../services/util_service";
import RequestTimeline from "./RequestTimeline";

function UnformattedInput(request: Request) {
  return (
    <Box>
      <Alert severity="warning">Unable to find source System/Command</Alert>
      <pre>{JSON.stringify(request.parameters, null, 2)}</pre>
    </Box>
  );
}

function RequestViewMain({
  request,
  setRequest,
  config,
  addRequestItem,
  showProjections,
  isCard,
  openRequest,
  closeRequest,
}: {
  request: Request;
  setRequest: (request: Request | undefined) => void;
  config: Config;
  showProjections: boolean;
  addRequestItem: (itemParams?: Partial<RequestItem>) => void;
  isCard: boolean;
  openRequest?: () => void;
  closeRequest?: () => void;
}) {
  const [activeIndex, setActiveIndex] = useState(0);
  const [showCommandForm, setShowCommandForm] = useState(false);
  const [command, setCommand] = useState<any>(null);
  const [system, setSystem] = useState<System | null>(null);
  const showSnackbar = useSnackbar();

  const [requestProjections, setRequestProjections] = useState<
    RequestCommand[] | undefined
  >(undefined);
  const requestProjectionSelectedRef = useRef<RequestCommand | undefined>(
    undefined,
  );

  const statusTemplate = (request: Request) => {
    return (
      <Chip
        label={request?.status}
        color={GetSeverity(request?.status)}
        id={`request_view_status_${request?.id}`}
      />
    );
  };

  const formatDate = (value: string) => {
    const date = new Date(value);
    return date.toLocaleDateString() + " " + date.toLocaleTimeString();
  };

  const updatedTemplate = (request: Request) => {
    return (
      <Box sx={{ display: "flex" }}>
        <Typography sx={{ mr: 1, alignContent: "center" }}>
          {formatDate(request.updated_at)}
        </Typography>
        <RequestTimeline request={request} />
      </Box>
    );
  };

  const buildColumns = () => {
    const requestColumns = [] as ColumnField[];

    // Adding Columns in Order
    if (isCard) {
      requestColumns.push({
        id: "command",
        field: "command",
        label: "Command",
        isString: true,
        template: (rowData: any) =>
          rowData.command_display_name ?? rowData.command,
      });
    }
    requestColumns.push({
      id: "namespace",
      field: "namespace",
      label: "Namespace",
      isString: true,
    });
    requestColumns.push({
      id: "system",
      field: "system",
      label: "System",
      isString: true,
    });
    requestColumns.push({
      id: "system_version",
      field: "system_version",
      label: "Version",
      isString: true,
    });

    requestColumns.push({
      id: "instance_name",
      field: "instance_name",
      label: "Instance",
      isString: true,
    });
    requestColumns.push({
      id: "Status",
      field: "status",
      label: "Status",
      isString: true,
      template: statusTemplate,
    });

    if (!isCard) {
      requestColumns.push({
        id: "created_at",
        field: "created_at",
        label: "Created",
        isDate: true,
      });
      requestColumns.push({
        id: "status_updated_at",
        field: "status_updated_at",
        label: "Status Updated",
        isDate: true,
        template: updatedTemplate,
      });
    }

    requestColumns.push({
      id: "comment",
      field: "comment",
      label: "Comment",
      isString: true,
    });

    if (isCard) {
      requestColumns.push({
        id: "action",
        label: "Action",
        template: () => {
          return (
            <RequestOptions
              request={request}
              setRequest={setRequest}
              config={config}
              addRequestItem={addRequestItem}
              requestProjections={requestProjections}
              requestProjectionSelectedRef={requestProjectionSelectedRef}
              isCard={isCard}
              openRequest={openRequest}
              closeRequest={closeRequest}
            />
          );
        },
      });
    }

    return requestColumns;
  };

  useEffect(() => {
    if (request) {
      if (showProjections && request) {
        GetRequestProjections(request)
          .then((projections) => {
            setRequestProjections(projections);
            requestProjectionSelectedRef.current = projections[0];
          })
          .catch((error) => {
            console.error("Error fetching request projections:", error);
            showSnackbar({
              severity: "error",
              summary: "Error",
              detail: `Error fetching request projections: ${error}`,
              life: 3000,
            });
          });
      }

      if (
        request &&
        request.status &&
        ["CANCELED", "SUCCESS", "ERROR", "INVALID"].includes(request.status)
      ) {
        setActiveIndex(1);
      }
      if (!system && !showCommandForm) {
        GetSystemList({
          name: request.system,
          version: request.system_version,
          namespace: request.namespace,
          garden_name: request.target_garden,
        })
          .then((data) => {
            if (data.length > 0) {
              setSystem(data[0]);
            } else {
              setShowCommandForm(true);
            }
          })
          .catch((error) => {
            console.error("Error fetching system list:", error);
            showSnackbar({
              severity: "error",
              summary: "Error",
              detail: `Error fetching system list: ${error}`,
              life: 3000,
            });
            setShowCommandForm(true);
          });
      } else if (!showCommandForm && system && system.commands) {
        const commandData = system.commands.find(
          (cmd) => cmd.name === request.command,
        );
        setCommand(commandData);
        setShowCommandForm(true);
      }
    }
  }, [request, showProjections, system]);

  function CustomTabPanel(props: {
    children?: React.ReactNode;
    index: number;
    value: number;
  }) {
    const { children, value, index, ...other } = props;

    return (
      <div
        role="tabpanel"
        hidden={value !== index}
        id={`simple-tabpanel-${index}`}
        aria-labelledby={`simple-tab-${index}`}
        {...other}
      >
        {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
      </div>
    );
  }

  // ARC Toolkit Errors:
  //     1) The tab role is missing the {{requiredContextRole}} required context role
  //     2) The list element is not expected inside the tablist role
  //     3) A relationship attribute (such as <label for="...">, or an ARIA attribute such as aria-controls="...") is pointing to a non-existent id.
  // Stepper Panel Content is not loaded into DOM until loaded causing checks to fail

  // ARC Toolkit Errors:
  //     1) Found an <ol> ordered list or <ul> unordered list that contains no list items.
  // PrimeReact CSS styling is `list-style-type:none` that hides it from check in DOM
  return (
    <Box sx={{ m: 1 }}>
      {isCard === false && (
        <Grid container sx={{ m: 2 }}>
          <Grid size="grow">
            <Typography variant="h3" component="h1">
              Request View: {request.id}
            </Typography>
          </Grid>
          <Grid>
            {request && (
              <>
                <RequestOptions
                  request={request}
                  setRequest={setRequest}
                  config={config}
                  addRequestItem={addRequestItem}
                  requestProjections={requestProjections}
                  requestProjectionSelectedRef={requestProjectionSelectedRef}
                  isCard={isCard}
                  openRequest={openRequest}
                  closeRequest={closeRequest}
                />
              </>
            )}
          </Grid>
        </Grid>
      )}
      <EnhancedTable
        data={[request]}
        columns={buildColumns()}
        displayAll={true}
      />

      {request && (
        <Box sx={{ m: 1 }}>
          <Tabs
            value={activeIndex}
            onChange={(_, number) => setActiveIndex(number)}
            sx={{ my: 2 }}
          >
            <Tab label="Request Parameters" id="simple-tab-0"></Tab>
            <Tab label="Request Output" id="simple-tab-1"></Tab>
          </Tabs>
          <CustomTabPanel value={activeIndex} index={0}>
            <>
              {!showCommandForm && <Skeleton width="100%" height="10rem" />}
              {showCommandForm && command && (
                <CommandForm
                  {...{
                    command: command,
                    request: request,
                    setRequest: () => {},
                    resetForm: false,
                    setResetForm: () => {},
                    setIsFormValid: () => {},
                  }}
                />
              )}
              {showCommandForm && !command && <UnformattedInput {...request} />}
            </>
          </CustomTabPanel>
          <CustomTabPanel value={activeIndex} index={1}>
            <RequestOutput request={request} />
          </CustomTabPanel>
        </Box>
      )}
    </Box>
  );
}

export default RequestViewMain;
