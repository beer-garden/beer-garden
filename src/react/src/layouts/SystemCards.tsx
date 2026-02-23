import "primeflex/primeflex.css";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Badge } from "primereact/badge";
import { Button } from "primereact/button";
import { ConfirmDialog, confirmDialog } from "primereact/confirmdialog";
import { Dialog } from "primereact/dialog";
import { DataView } from "primereact/dataview";
import { Menu } from "primereact/menu";
import { Panel } from "primereact/panel";
import { Toast } from "primereact/toast";
import { classNames } from "primereact/utils";
import { useEffect, useRef, useState } from "react";

import { Instance, Queue, Request, System } from "../models/brewtils-types";
import { GetRequestList } from "../services/request_service";
import { StartInstance, StopInstance } from "../services/instance_service";
import { ClearQueue, ClearAllQueues, GetInstanceQueues } from "../services/queue_service";
import {
  DeleteSystem,
  GetSystemList,
  ReloadSystem,
  Rescan,
} from "../services/system_service";
import { Message } from "primereact/message";

function SystemCards() {
  const [systems, setSystems] = useState<Array<System>>([]);
  const [updated, setUpdated] = useState<boolean>(false);

  useEffect(() => {
    GetSystemList()
      .then((data: Array<System>) => {
        console.log(data);
        setSystems(data);
      })
      .catch((error) => {
        console.error("Error fetching systems:", error);
      });
  }, [updated]);

  const getSeverity = (
    status?: string,
  ):
    | "warning"
    | "success"
    | "info"
    | "danger"
    | "secondary"
    | "contrast"
    | null
    | undefined => {
    if (status === "INITIALIZING") {
      return "warning";
    }
    if (status === "RUNNING") {
      return "success";
    }
    if (status === "PAUSED") {
      return "info";
    }
    if (status === "STOPPED") {
      return "info";
    }
    if (status === "DEAD") {
      return "danger";
    }
    if (status === "UNRESPONSIVE") {
      return "danger";
    }
    if (status === "STARTING") {
      return "warning";
    }
    if (status === "STOPPING") {
      return "warning";
    }
    if (status === "UNKNOWN") {
      return "danger";
    }
    if (status === "AWAITING_SYSTEM") {
      return "warning";
    }
    if (status === "ERROR") {
      return "danger";
    }
    return "danger";
  };

  const statusList = [
    "INITIALIZING",
    "RUNNING",
    "PAUSED",
    "STOPPED",
    "DEAD",
    "UNRESPONSIVE",
    "STARTING",
    "STOPPING",
    "UNKNOWN",
    "AWAITING_SYSTEM",
    "ERROR",
  ] as Array<string>;

  const systemTemplateGrid = (system: System) => {
    if (!system) {
      return;
    }

    const statusCounts = new Map();

    statusList.forEach((status) => {
      // statusCounts[status] = {count: 0, severity:getSeverity(status)}
      statusCounts.set(status, 0);
    });

    system?.instances?.forEach((instance) => {
      if (instance.status) {
        statusCounts.set(
          instance.status,
          (statusCounts.get(instance.status) || 0) + 1,
        );
      }
    });

    function startSystem(system: System) {
      system.instances?.forEach((instance) => {
        StartInstance(instance, system)
          .then(() => {
            setUpdated(!updated);
          })
          .catch((error) => {
            console.error("Error starting system:", error);
          });
      });
    }

    function stopSystem(system: System) {
      system.instances?.forEach((instance) => {
        StopInstance(instance, system)
          .then(() => {
            setUpdated(!updated);
          })
          .catch((error) => {
            console.error("Error stopping system:", error);
          });
      });
    }

    function reloadSystem(system: System) {
      ReloadSystem(system)
        .then(() => {
          setUpdated(!updated);
        })
        .catch((error) => {
          console.error("Error reloading system:", error);
        });
    }

    function hasRunningInstances(system: System) {
      return system.instances?.some((instance) => {
        return instance.status == "RUNNING";
      });
    }

    function deleteSystem(system: System) {
      const accept = () => {
        DeleteSystem(system)
          .then(() => {
            setUpdated(!updated);
            toast.current?.show({
              severity: "info",
              summary: "Confirmation",
              detail: `Deleted system ${system.name}`,
              life: 3000,
            });
          })
          .catch((error) => {
            console.error("Error deleting system:", error);
          });
      };
      const reject = () => {};
      const confirm = () => {
        confirmDialog({
          message:
            "Are you sure you want to delete a system with running instances?",
          header: `Confirm Delete ${system.name}`,
          icon: "pi pi-exclamation-triangle",
          defaultFocus: "accept",
          accept,
          reject,
        });
      };

      if (hasRunningInstances(system)) {
        confirm();
      } else {
        accept();
      }
    }

    function handleStartInstance(instance: Instance, system: System) {
      StartInstance(instance, system)
        .then(() => {
          setUpdated(!updated);
        })
        .catch((error) => {
          console.error("Error starting instance:", error);
        });
    }

    function handleStopInstance(instance: Instance, system: System) {
      StopInstance(instance, system)
        .then(() => {
          setUpdated(!updated);
        })
        .catch((error) => {
          console.error("Error deleting stopping instance:", error);
        });
    }

    const headerTemplate = (options: any) => {
      const className = `${options.className} justify-content-space-between`;
      const systemConfigMenu = useRef<Menu>(null);

      const systemMenuItems = [
        {
          label: "Start",
          icon: <FontAwesomeIcon icon="play" />,
          command: () => startSystem(system),
        },
        {
          label: "Stop",
          icon: <FontAwesomeIcon icon="stop" />,
          command: () => stopSystem(system),
        },
        {
          label: "Restart",
          icon: <FontAwesomeIcon icon="refresh" />,
          command: () => reloadSystem(system),
        },
        {
          separator: true,
        },
        {
          label: "Delete",
          icon: <FontAwesomeIcon icon="trash" />,
          command: () => deleteSystem(system),
        },
      ];

      return (
        <div className={className}>
          <div className="flex align-items-center gap-2">
            <label className="max-w-10rem">
              {system.name}/ {system.version}
            </label>

            {Array.from(statusCounts, ([status, count]) => {
              if (count && count > 0) {
                const statusSeverity = getSeverity(status);
                return (
                  <Badge
                    value={count}
                    severity={statusSeverity}
                    title={status}
                  />
                );
              }
              return null;
            })}
          </div>
          <div>
            <Menu
              model={systemMenuItems}
              popup
              ref={systemConfigMenu}
              id="config_menu"
            />
            <button
              className="p-panel-header-icon p-link mr-2"
              onClick={(e) => systemConfigMenu?.current?.toggle(e)}
            >
              <FontAwesomeIcon icon="cog" />
            </button>
            {options.togglerElement}
          </div>
        </div>
      );
    };

    const instanceTemplate = (
      system: System,
      instance: Instance,
      index: number,
    ) => {
      const instanceConfigMenu = useRef<Menu>(null);
      const [logsVisible, setLogsVisible] = useState(false)
      const [queueVisible, setQueueVisible] = useState(false)
      const [queues, setQueues] = useState<Array<Queue>>([])
      const [cancelDeleteVisible, setCancelDeleteVisible] = useState(false)

      const statusSeverity = getSeverity(instance?.status);

      const all_count = useRef<number>(0);
      const success_count = useRef<number>(0);
      const cancelled_count = useRef<number>(0);
      const error_count = useRef<number>(0);
      const created_count = useRef<number>(0);
      const received_count = useRef<number>(0);
      const in_progress_count = useRef<number>(0);


      function showLogs(system: System, instance: Instance){
        setLogsVisible(true);
          // $uibModal.open({
          //   template: readLogs,
          //   resolve: {
          //     system: system,
          //     instance: instance,
          //   },
          //   controller: 'AdminSystemLogsController',
          //   windowClass: 'app-modal-window',
          // });
      }

      function manageQueue(system: System, instance: Instance){
        GetInstanceQueues(instance.id)
          .then((data: Array<Queue>) => {
            setQueues(data);
            setQueueVisible(true);
          })
          .catch((error) => {
            console.error("Error fetching queues:", error);
          });
      }

      function clearQueue(queueName: string) {
        const accept = () => {
          void ClearQueue(queueName);
        }

        const reject = () => {}

        const confirm = () => {
          confirmDialog({
            message: "Are you sure you want to clear the Queue?",
            header: "Confirm",
            icon: <FontAwesomeIcon icon="exclamation" />,
            defaultFocus: "accept",
            accept,
            reject,
          });
        };
    
        confirm();
      }

      function buildFilter(status: string) {
        return {
          "include_children": true,
          "length": 1,
          "columns": [
            {
              "data": "namespace__exact",
              "name": "",
              "searchable": true,
              "orderable": true,
              "search": {
                "value": system.namespace,
                "regex": false
              }
            },
            {
              "data": "system__exact",
              "name": "",
              "searchable": true,
              "orderable": true,
              "search": {
                "value": system.name,
                "regex": false
              }
            },
            {
              "data": "system_version__exact",
              "name": "",
              "searchable": true,
              "orderable": true,
              "search": {
                "value": system.version,
                "regex": false
              }
            },
            {
              "data": "instance_name__exact",
              "name": "",
              "searchable": true,
              "orderable": true,
              "search": {
                "value": instance.name,
                "regex": false
              }
            },
            {
              "data": "status",
              "name": "",
              "searchable": true,
              "orderable": true,
              "search": {
                "value": ((status == "ALL") ? "" : status),
                "regex": false
              }
            },
          ]
        };
      }

      function loadRequests() {
        GetRequestList(buildFilter("SUCCESS")).then(
          (data: [Array<Request>, Headers]) => {
            let headers = data[1]
            success_count.current = parseInt(headers.get('recordsFiltered') ?? "0");
            all_count.current += success_count.current;
          },
          (response) => {
            let msg = 'Uh oh! It looks like there was a problem counting the SUCCESS Requests.\n';
            if (response.data !== undefined && response.data !== null) {
              msg += response.data;
            }
            console.log(msg);
            // $scope.alerts.push({
            //   type: 'danger',
            //   msg: msg,
            // });
          }
        );
    
        GetRequestList(buildFilter("CANCELED")).then(
          (data: [Array<Request>, Headers]) => {
            let headers = data[1]
            cancelled_count.current = parseInt(headers.get('recordsFiltered') ?? "0");
            all_count.current += cancelled_count.current;
          },
          (response) => {
            let msg = 'Uh oh! It looks like there was a problem counting the CANCELED Requests.\n';
            if (response.data !== undefined && response.data !== null) {
              msg += response.data;
            }
            console.log(msg);
            // $scope.alerts.push({
            //   type: 'danger',
            //   msg: msg,
            // });
          }
        );

        GetRequestList(buildFilter("ERROR")).then(
          (data: [Array<Request>, Headers]) => {
            let headers = data[1]
            error_count.current = parseInt(headers.get('recordsFiltered') ?? "0");
            all_count.current += error_count.current;
          },
          (response) => {
            let msg = 'Uh oh! It looks like there was a problem counting the ERROR Requests.\n';
            if (response.data !== undefined && response.data !== null) {
              msg += response.data;
            }
            console.log(msg);
            // $scope.alerts.push({
            //   type: 'danger',
            //   msg: msg,
            // });
          }
        );

        GetRequestList(buildFilter("CREATED")).then(
          (data: [Array<Request>, Headers]) => {
            let headers = data[1]
            created_count.current = parseInt(headers.get('recordsFiltered') ?? "0");
            all_count.current += created_count.current;
          },
          (response) => {
            let msg = 'Uh oh! It looks like there was a problem counting the CREATED Requests.\n';
            if (response.data !== undefined && response.data !== null) {
              msg += response.data;
            }
            console.log(msg);
            // $scope.alerts.push({
            //   type: 'danger',
            //   msg: msg,
            // });
          }
        );

        GetRequestList(buildFilter("RECEIVED")).then(
          (data: [Array<Request>, Headers]) => {
            let headers = data[1]
            received_count.current = parseInt(headers.get('recordsFiltered') ?? "0");
            all_count.current += received_count.current;
          },
          (response) => {
            let msg = 'Uh oh! It looks like there was a problem counting the RECEIVED Requests.\n';
            if (response.data !== undefined && response.data !== null) {
              msg += response.data;
            }
            console.log(msg);
            // $scope.alerts.push({
            //   type: 'danger',
            //   msg: msg,
            // });
          }
        );
    
        GetRequestList(buildFilter("IN_PROGRESS")).then(
          (data: [Array<Request>, Headers]) => {
            let headers = data[1]
            in_progress_count.current = parseInt(headers.get('recordsFiltered') ?? "0");
            all_count.current += in_progress_count.current;
          },
          (response) => {
            let msg = 'Uh oh! It looks like there was a problem counting the IN PROGRESS Requests.\n';
            if (response.data !== undefined && response.data !== null) {
              msg += response.data;
            }
            console.log(msg);
            // $scope.alerts.push({
            //   type: 'danger',
            //   msg: msg,
            // });
          }
        );
    
      };

      function cancelDeleteRequests(system: System, instance: Instance){
        loadRequests();
        setCancelDeleteVisible(true);
      }

      
      function deleteRequests(status: string, is_cancel: boolean=false) {
        let deleteParams = {
          "namespace": system.namespace,
          "system": system.name,
          "system_version": system.version,
          "instance_name": instance.name
        };
    
        if (is_cancel){
          deleteParams["is_cancel"] = true
        }
    
        if (status != "ALL") {
          deleteParams["status"] = status;
        }
    
        // DeleteRequests(deleteParams)
        //   .then(addSuccessAlert, addDeleteErrorAlert)
        //   .catch((error) => {
        //     console.error("Error fetching queues:", error);
        //   });
      }

      const instanceMenuItems = [
        {
          label: "Show Logs",
          command: () => showLogs(system, instance),
        },
        {
          label: "Manage Queue",
          command: () => manageQueue(system, instance),
        },
        {
          label: "Cancel/Delete Requests",
          command: () => cancelDeleteRequests(system, instance),
        },
      ];

      const filename = system.name + '[' + system.version +
      ']-' + instance.name +
      '.log';

      return (
        <div className="col-12" key={instance.id}>
          <div
            className={classNames(
              "flex flex-column xl:flex-row xl:align-items-start p-4 ",
              { "border-top-1 surface-border": index !== 0 },
            )}
          >
            <div className="mt-4">
              <div>
                <FontAwesomeIcon icon="folder" />
                <label>{instance.name}</label>
                <Badge value={instance.status} severity={statusSeverity} />
              </div>
              <div>
                <Button
                  className="mr-2"
                  title={`Start Instance ${instance.name}`}
                  onClick={() => handleStartInstance(instance, system)}
                >
                  <FontAwesomeIcon icon="play" />
                </Button>
                <Button
                  className="mr-2"
                  title={`Stop Instance ${instance.name}`}
                  onClick={() => handleStopInstance(instance, system)}
                >
                  <FontAwesomeIcon icon="stop" />
                </Button>
                <>
                  <Menu
                    model={instanceMenuItems}
                    popup
                    ref={instanceConfigMenu}
                    id="instance_menu"
                  />
                  <Dialog header={`Log File: ${system.name}[${system.version}]-${instance.name}`} footer={<Button onClick={() => setLogsVisible(false)}>Close Logs</Button>} visible={logsVisible} style={{ width: '50vw' }} onHide={() => {if (!logsVisible) return; setLogsVisible(false); }}>
                    <Message text="Plugin must be listening to the Admin Queue and logging to File for logs to be returned. This will only return information from the log file being actively written to." />
                    <div>
                      <form>
                        <input type="submit" name="start" value="Get Tail Logs" onClick={() => getLogsTail()} />
                        <input type="submit" name="stop" value="Stop Tail Logs" onClick={() => stopLogsTail()} />
                        <label htmlFor="tail_line_start">Tail Lines</label> 
                        <input
                          type="number"
                          id="tail_line_start"
                          min="0"
                          name="tail_line_start"
                          // ng-model="tail_line_start"
                        />
                      </form>
                    </div>
                    <div>
                      <a href={`api/v1/instances/${instance.id}/logs/?logs_only=true`} download={filename}
                        ><button>Get Full Logs</button></a
                      >
                    </div>
                  </Dialog>
                  <Dialog header={`Queue Manager: ${system.name}[${system.version}]-${instance.name}`} footer={<Button onClick={() => setQueueVisible(false)}>Close</Button>} visible={queueVisible} style={{ width: '50vw' }} onHide={() => {if (!queueVisible) return; setQueueVisible(false); }}>
                    <table className="table">
                      <thead>
                        <tr>
                          <th scope="col">Name</th>
                          <th scope="col">Message Size</th>
                          <th scope="col"></th>
                        </tr>
                      </thead>
                      <tbody>
                        {queues.map((queue, index) => (
                          <tr key={index}>
                            <td>{queue.name}</td>
                            <td>{queue.size}</td>
                            <td>
                              <ConfirmDialog message="Are you sure you want to clear the Queue?" />
                              <Button
                                onClick={() => clearQueue(queue.name)}
                              >
                                Clear Queue
                              </Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </Dialog>
                  <Dialog header={`Cancel/Delete Requests: ${system.name}[${system.version}]-${instance.name}`} footer={<Button onClick={() => setCancelDeleteVisible(false)}>Close</Button>} visible={cancelDeleteVisible} style={{ width: '50vw' }} onHide={() => {if (!cancelDeleteVisible) return; setCancelDeleteVisible(false); }}>
                  <div>
                    Currently {all_count.current} Requests present in the database
                  </div>
                  <br />
                  <table
                    id="requestDeleteCancelTable"
                    // dt-options="dtOptions"
                    // dt-columns="dtColumns"
                    // className="table table-striped table-bordered w-100"
                    >
                    <tbody>
                    <tr>
                      <th>Status</th>
                      <th>Count</th>
                      <th>Action</th>
                    </tr>
                    <tr>
                      <td>SUCCESS</td>
                      <td>{success_count.current}</td>
                      <td>
                        <Button onClick={() => deleteRequests('SUCCESS')}>
                          {/* confirm="Are you sure you want to delete Requests with status SUCCESS?"> */}
                          Delete SUCCESS
                        </Button>
                      </td>
                    </tr>
                    <tr>
                      <td>CANCELED</td>
                      <td>{cancelled_count.current}</td>
                      <td>
                        <Button onClick={() => deleteRequests('CANCELED')}>
                          {/* confirm="Are you sure you want to delete Requests with status CANCELED?" */}
                          Delete CANCELED
                        </Button>
                      </td>
                    </tr>
                    <tr>
                      <td>ERROR</td>
                      <td>
                        {error_count.current}
                      </td>
                      <td>
                        <Button onClick={() => deleteRequests('ERROR')}>
                          {/* confirm="Are you sure you want to delete Requests with status ERROR?" */}
                          Delete ERROR
                        </Button>
                      </td> 
                    </tr>
                    <tr>
                      <td>IN PROGRESS</td>
                      <td>{in_progress_count.current}</td>
                      <td>
                        <Button onClick={() => deleteRequests('IN PROGRESS', is_cancel=true)}>
                          {/* confirm="Are you sure you want to cancel Requests with status IN PROGRESS? There may be a plugin already running the request." */}
                          Cancel IN PROGRESS
                        </Button>
                      </td>
                    </tr>
                    <tr>
                      <td>RECEIVED</td>
                      <td>
                        {received_count.current}
                      </td>
                      <td>
                        <Button onClick={() => deleteRequests('RECEIVED', is_cancel=true)}>
                          {/* confirm="Are you sure you want to cancel Requests with status RECEIVED?"> */}
                          Cancel RECEIVED
                        </Button>
                      </td>
                    </tr>
                    <tr>
                      <td>CREATED</td>
                      <td>
                        {created_count.current}
                      </td>
                      <td>
                        <Button onClick={() => deleteRequests('CREATED', is_cancel=true)}>
                          {/* confirm="Are you sure you want to cancel Requests with status CREATED? Recommend clearing topics as well."> */}
                          Cancel CREATED
                        </Button>
                      </td>
                    </tr>
                    <tr>
                      <td>Non-Completed (CREATED/RECEIVED/IN PROGRESS)</td>
                      <td>
                      {in_progress_count.current + received_count.current + created_count.current}
                      </td>
                      <td>
                        <Button onClick={() => deleteRequests('ALL', is_cancel=true)}>
                          {/* confirm="Are you sure you want to cancel all non-completed Requests?"> */}
                          Cancel Non-Completed
                        </Button>
                      </td>     
                    </tr>
                    <tr>
                      <td>ALL</td>
                      <td>
                        {all_count.current}
                      </td>
                      <td>
                        <Button onClick={() => deleteRequests('ALL')}>
                          {/* confirm="Are you sure you want to delete all the Requests?"> */}
                          Delete All
                        </Button>
                      </td>
                    </tr>
                    </tbody>
                  </table>
                  </Dialog>
                  <Button
                    className="mr-2"
                    title={`Admin Tools for ${instance.name}`}
                    onClick={(e) => instanceConfigMenu?.current?.toggle(e)}
                  >
                    <FontAwesomeIcon icon="bars" />
                  </Button>
                </>
              </div>
            </div>
          </div>
        </div>
      );
    };

    const instanceListTemplate = (instances: Instance[]) => {
      if (!instances || instances.length === 0) return null;

      const list = instances.map((instance: Instance, index: number) => {
        return instanceTemplate(system, instance, index);
      });

      return <div className="grid grid-nogutter">{list}</div>;
    };

    return (
      <Panel
        headerTemplate={headerTemplate}
        key={system.id}
        className="m-2"
        style={{ width: "20%" }}
        toggleable
        collapsed
      >
        <p className="m-0">{system.description}</p>
        <DataView
          value={system.instances}
          listTemplate={instanceListTemplate}
        />
      </Panel>
    );
  };

  const systemListTemplate = (systems: System[]) => {
    if (!Array.isArray(systems) && typeof systems === "object") {
      const newSystems = [] as System[];
      Object.values(systems).forEach((system) => {
        newSystems.push(system as System);
      });
      systems = newSystems;
    }
    return (
      <div
        className="grid grid-nogutter"
        style={{ gridTemplateColumns: `repeat(auto-fit, minmax(250px, 1fr))` }}
      >
        {systems.map((system) => systemTemplateGrid(system))}
      </div>
    );
  };
  const systemGroup = new Map<string, System[]>();

  const groupField = "namespace";
  // const groupField = "version";
  systems.forEach((system) => {
    systemGroup.set(system[groupField] as string, [
      ...(systemGroup.get(system[groupField] as string) || []),
      ...[system],
    ]);
  });

  const groupHeaderTemplate = (options: any) => {
    const className = `${options.className} justify-content-space-between`;

    const statusCounts = new Map();

    statusList.forEach((status) => {
      // statusCounts[status] = {count: 0, severity:getSeverity(status)}
      statusCounts.set(status, 0);
    });
    const groupSystems = systemGroup.get(options.props.title) || [];
    groupSystems.forEach((system: System) => {
      system?.instances?.forEach((instance) => {
        if (instance.status) {
          statusCounts.set(
            instance.status,
            (statusCounts.get(instance.status) || 0) + 1,
          );
        }
      });
    });

    return (
      <div className={className}>
        <div className="flex align-items-center gap-2">
          <label>{options.props.title}</label>

          {Array.from(statusCounts, ([status, count]) => {
            if (count && count > 0) {
              const statusSeverity = getSeverity(status);
              return (
                <Badge value={count} severity={statusSeverity} title={status} />
              );
            }
            return null;
          })}
        </div>
        <div>{options.togglerElement}</div>
      </div>
    );
  };

  // Toast ref
  const toast = useRef<Toast>(null);

  function handleClearAllQueues() {
    const accept = () => {
      toast.current?.show({
        severity: "info",
        summary: "Confirmation",
        detail: "Clearing All Queues",
        life: 3000,
      });
      void ClearAllQueues();
    };

    const reject = () => {};

    const confirm = () => {
      confirmDialog({
        message: "Are you sure you want to delete all Queues?",
        header: "Confirmation",
        icon: "pi pi-exclamation-triangle",
        defaultFocus: "accept",
        accept,
        reject,
      });
    };

    confirm();
  }

  const handleRescan = () => {
    Rescan()
      .then(() => {
        setUpdated(!updated);
        toast.current?.show({
          severity: "info",
          summary: "Confirmation",
          detail: "Rescan complete",
          life: 3000,
        });
      })
      .catch((error) => {
        console.error("Error deleting system:", error);
      });
  };

  return (
    <>
      <div className="flex items-end ml-2 page-header">
        <h1 className="flex-1">Systems Management</h1>
        <div>
          <Toast ref={toast} />
          <ConfirmDialog />
          <Button onClick={handleClearAllQueues} label="Clear All Queues" />
          <Button onClick={handleRescan} label="Rescan Plugin Directory" />
        </div>
      </div>
      <div>
        {Array.from(systemGroup, ([group, groupedSystems]) => (
          <Panel
            headerTemplate={groupHeaderTemplate}
            toggleable
            // collapsed
            title={group}
            className="m-2"
            style={{ width: "100%" }}
          >
            <DataView
              value={groupedSystems}
              listTemplate={systemListTemplate}
              layout="grid"
            />
          </Panel>
        ))}
      </div>
    </>
  );
}
export default SystemCards;
