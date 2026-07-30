import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Box, Grid, Typography } from "@mui/material";
import { FilterMatchMode } from "primereact/api";
import { Checkbox } from "primereact/checkbox";
import { Column } from "primereact/column";
import { confirmDialog } from "primereact/confirmdialog";
import { DataTable, SortOrder } from "primereact/datatable";
import { Dialog } from "primereact/dialog";
import { Divider } from "primereact/divider";
import { InputText } from "primereact/inputtext";
import { Messages } from "primereact/messages";
import { ChangeEvent, useCallback, useEffect, useRef, useState } from "react";

import AccessButton from "../components/AccessButton";
import EnhancedTable from "../components/EnhancedTable/components/EnhancedTable";
import { ColumnField } from "../components/EnhancedTable/models/EnhancedTableModels";
import SubscriberItem from "../components/SubscriberItem";
import { Subscriber, Topic } from "../models/brewtils-types";
import { Config, RequestItem } from "../models/models";
import { useSnackbar } from "../providers/SnackbarProvider";
import {
  AddSubscriber,
  CreateTopic,
  DeleteTopic,
  GetTopics,
  RemoveSubscriber,
  ResetCount,
  SyncTopics,
} from "../services/topic_service";
import { PaginatorTemplate } from "../services/util_service";

interface TopicFlatten extends Omit<Topic, "subscribers"> {
  subscribers?: Subscriber;
}

function TopicIndex({
  config,
  addRequestItem,
}: {
  config: Config;
  listeners: Record<string, any>;
  addRequestItem: (itemParams?: Partial<RequestItem>) => void;
}) {
  const showSnackbar = useSnackbar();

  const [topics, setTopics] = useState<Topic[]>([]);
  const topicsRef = useRef<Topic[]>([]);
  const [reloadTopicsTrigger, setReloadTopicsTrigger] = useState(0);

  const updateTopics = (values: Topic[]) => {
    topicsRef.current = values;
    setTopics(values);
  };

  const [loading, setLoading] = useState(false);

  const [hideGenerated, setHideGenerated] = useState<boolean>(true);
  const generatedRef = useRef<boolean>(true);

  const [dialogVisible, setDialogVisible] = useState(false);
  const isEdit = useRef<boolean>(false);
  const topicId = useRef<string | undefined>(undefined);
  const [topicName, setTopicName] = useState<string>("");
  const [subscriberList, setSubscriberList] = useState<Array<Subscriber>>([
    {
      namespace: "",
      garden: "",
      system: "",
      version: "",
      instance: "",
      command: "",
    } as Subscriber,
  ]);

  const msgs = useRef<Messages>(null);
  const loadTopics = useCallback(() => {
    setLoading(true);

    GetTopics({ hide_generated: generatedRef.current })
      .then((topicValues: Array<Topic>) => {
        updateTopics(topicValues);
        setLoading(false);
      })
      .catch((error) => {
        setLoading(false);
        showSnackbar({
          severity: "error",
          summary: "Error",
          detail: `Error fetching topics: ${error}`,
          life: 3000,
        });
      });
  }, [topics]);

  useEffect(() => {
    loadTopics();
  }, []);

  useEffect(() => {
    setReloadTopicsTrigger(reloadTopicsTrigger + 1);
  }, [topics]);

  useEffect(() => {
    if (!dialogVisible) {
      //Reset all values to defaults
      topicId.current = undefined;
      isEdit.current = false;
      setTopicName("");
      setSubscriberList([
        {
          namespace: "",
          garden: "",
          system: "",
          version: "",
          instance: "",
          command: "",
        } as Subscriber,
      ]);
    }
  }, [dialogVisible]);

  function openTopicDialog() {
    setDialogVisible(true);
  }

  function TopicHeader() {
    function handleSync() {
      SyncTopics()
        .then(() => {
          loadTopics();
          showSnackbar({
            severity: "info",
            summary: "Confirmation",
            detail: "Sync Topics complete",
            life: 3000,
          });
        })
        .catch((error) => {
          showSnackbar({
            severity: "error",
            summary: "Error",
            detail: `Error syncing topics: ${error}`,
            life: 3000,
          });
        });
    }

    return (
      <Grid container>
        <Grid size="grow">
          <Typography variant="h2" component="h1">
            Topic Management
          </Typography>
        </Grid>

        <Grid sx={{ display: "flex", alignItems: "center" }}>
          <AccessButton
            raised
            onClick={handleSync}
            label="Sync Topics"
            data-testid="rescan-btn"
            config={config}
            permission="PLUGIN_ADMIN"
            sx={{ m: 2 }}
          >
            Sync Topics
          </AccessButton>
          <AccessButton
            raised
            onClick={openTopicDialog}
            label="Create Topic"
            data-testid="create-btn"
            config={config}
            permission="PLUGIN_ADMIN"
            sx={{ m: 2 }}
          >
            Create Topic
          </AccessButton>
        </Grid>
      </Grid>
    );
  }

  function TopicTable() {
    function clearCount(clearTopic: Topic, clearSubscriber?: Subscriber) {
      const accept = () => {
        ResetCount(clearTopic.id, clearSubscriber)
          .then((updatedTopic: Topic) => {
            console.error("Updating Topics");
            updateTopics(
              topicsRef.current.map((topicRefValue) => {
                console.log(
                  `Compare ${topicRefValue.id} === ${updatedTopic.id}`,
                );
                if (topicRefValue.id === updatedTopic.id) {
                  console.error("Map values");
                  if (clearSubscriber) {
                    const updatedTopicValue = {
                      ...updatedTopic,
                      subscribers: topicRefValue.subscribers?.map(
                        (valueSubscriber) => {
                          if (
                            valueSubscriber.command ==
                              clearSubscriber.command &&
                            valueSubscriber.instance ==
                              clearSubscriber.instance &&
                            valueSubscriber.version ==
                              clearSubscriber.version &&
                            valueSubscriber.system == clearSubscriber.system &&
                            valueSubscriber.garden == clearSubscriber.garden &&
                            valueSubscriber.namespace ==
                              clearSubscriber.namespace
                          ) {
                            return {
                              ...valueSubscriber,
                              consumer_count: 0,
                            } as Subscriber;
                          }
                          return valueSubscriber;
                        },
                      ),
                    };
                    console.log(`Return ${updatedTopicValue.id}`);
                    return updatedTopicValue;
                  }
                  console.log(`Return ${updatedTopic.id}`);
                  return updatedTopic;
                }
                console.log(`Return ${topicRefValue.id}`);
                return topicRefValue;
              }),
            );
            showSnackbar({
              severity: "info",
              summary: "Confirmation",
              detail: `Cleared ${clearSubscriber ? "consumer" : "publisher"} count for ${clearTopic.name}`,
              life: 3000,
            });
          })
          .catch((error) => {
            showSnackbar({
              severity: "error",
              summary: "Error",
              detail: `Error clearing count: ${error}`,
              life: 3000,
            });
          });
      };
      const reject = () => {};
      const confirm = () => {
        confirmDialog({
          message: `Are you sure you want to reset the ${clearSubscriber ? "consumer" : "publisher"} count?`,
          header: `Confirm Clear ${clearSubscriber ? "Consumer" : "Publisher"} Count ${clearTopic.name}`,
          icon: "pi pi-exclamation-triangle",
          defaultFocus: "accept",
          accept,
          reject,
        });
      };

      confirm();
    }

    function removeSubscriber(topic: Topic, subscriber: Subscriber) {
      RemoveSubscriber(topic.id!, subscriber)
        .then(() => {
          updateTopics(
            topicsRef.current.map((value) => {
              if (value.id === topic.id && value.subscribers) {
                value.subscribers = value.subscribers.filter(
                  (valueSubscriber) => valueSubscriber !== subscriber,
                );
              }
              return value;
            }),
          );

          showSnackbar({
            severity: "info",
            summary: "Removed Subscriber",
            detail: `Topic updated: ${topic.name}`,
            life: 3000,
          });
        })
        .catch((error) => {
          showSnackbar({
            severity: "error",
            summary: "Error",
            detail: `Error removing subscriber from topic ${topic.name}: ${error}`,
            life: 3000,
          });
        });
    }

    function publisherCountTemplate(topicSubscriber: TopicFlatten) {
      return (
        <div className="flex align-items-center gap-2">
          <span>{topicSubscriber.publisher_count}</span>

          {((topicSubscriber !== undefined &&
            topicSubscriber.publisher_count) ||
            0) > 0 && (
            <AccessButton
              basic
              rounded
              raised
              size="small"
              aria-label={`Clear Publisher Count ${topicSubscriber?.publisher_count} from Topic ${topicSubscriber?.name}`}
              tooltip="Clear Publisher Count"
              onClick={() =>
                clearCount({
                  id: topicSubscriber.id,
                  name: topicSubscriber.name,
                } as Topic)
              }
              config={config}
              permission="PLUGIN_ADMIN"
            >
              <FontAwesomeIcon icon="trash-can" />
            </AccessButton>
          )}
        </div>
      );
    }

    function deleteTopic(topic: Topic) {
      const accept = () => {
        if (!topic.id) {
          return;
        }

        DeleteTopic(topic.id)
          .then(() => {
            updateTopics(
              topicsRef.current.filter((value) => value.id !== topic.id),
            );

            showSnackbar({
              severity: "info",
              summary: "Confirmation",
              detail: `Deleted topic ${topic.name}`,
              life: 3000,
            });
          })
          .catch((error) => {
            showSnackbar({
              severity: "error",
              summary: "Error",
              detail: `Error deleting topic ${topic.name}: ${error}`,
              life: 3000,
            });
          });
      };
      const reject = () => {};
      const confirm = () => {
        confirmDialog({
          message:
            'Are you sure you want to delete Topic "' + topic.name + '"?',
          header: `Confirm Delete ${topic.name}`,
          icon: "pi pi-exclamation-triangle",
          defaultFocus: "accept",
          accept,
          reject,
        });
      };

      confirm();
    }

    function addSubscriber(topic: Topic) {
      setTopicName(topic.name || "");
      setSubscriberList([
        {
          namespace: "",
          garden: "",
          system: "",
          version: "",
          instance: "",
          command: "",
        } as Subscriber,
      ]);

      topicId.current = topic.id;
      isEdit.current = true;
      openTopicDialog();
    }

    function gardenTemplate(topicSubscriber: TopicFlatten) {
      return topicSubscriber.subscribers?.garden || "*";
    }

    function namespaceTemplate(topicSubscriber: TopicFlatten) {
      return topicSubscriber.subscribers?.namespace || "*";
    }

    function systemTemplate(topicSubscriber: TopicFlatten) {
      return topicSubscriber.subscribers?.system || "*";
    }

    function versionTemplate(topicSubscriber: TopicFlatten) {
      return topicSubscriber.subscribers?.version || "*";
    }

    function instanceTemplate(topicSubscriber: TopicFlatten) {
      return topicSubscriber.subscribers?.instance || "*";
    }

    function commandTemplate(topicSubscriber: TopicFlatten) {
      return topicSubscriber.subscribers?.command || "*";
    }

    function consumerCountTemplate(topicSubscriber: TopicFlatten) {
      return (
        <div className="flex align-items-center gap-2">
          <span>{topicSubscriber.subscribers?.consumer_count}</span>

          {topicSubscriber.subscribers != undefined &&
            topicSubscriber.subscribers.consumer_count != undefined &&
            (topicSubscriber.subscribers.consumer_count || 0) > 0 && (
              <AccessButton
                basic
                rounded
                raised
                size="small"
                className="ml-2"
                aria-label={`Clear Count of ${topicSubscriber.subscribers.consumer_count} for Topic ${topicSubscriber?.name} Subscriber ${topicSubscriber.subscribers.garden ?? "*"} ${topicSubscriber.subscribers.namespace ?? "*"} ${topicSubscriber.subscribers.system ?? "*"} ${topicSubscriber.subscribers.version ?? "*"} ${topicSubscriber.subscribers.instance ?? "*"} ${topicSubscriber.subscribers.command ?? "*"}`}
                tooltip="Clear count"
                onClick={() =>
                  clearCount(
                    { id: topicSubscriber.id } as Topic,
                    topicSubscriber.subscribers as Subscriber,
                  )
                }
                config={config}
                permission="PLUGIN_ADMIN"
              >
                <FontAwesomeIcon icon="trash-can" />
              </AccessButton>
            )}
        </div>
      );
    }

    function subscriberTypeTemplate(topicSubscriber: TopicFlatten) {
      return (
        <div className="flex align-items-center gap-2">
          <span>{topicSubscriber.subscribers?.subscriber_type}</span>

          {topicSubscriber.subscribers !== undefined &&
            topicSubscriber.subscribers.subscriber_type == "DYNAMIC" && (
              <AccessButton
                basic
                rounded
                raised
                onClick={() =>
                  removeSubscriber(
                    {
                      id: topicSubscriber.id,
                      name: topicSubscriber.name,
                    } as Topic,
                    topicSubscriber.subscribers!,
                  )
                }
                size="small"
                className="ml-2"
                aria-label={`Remove from Topic ${topicSubscriber?.name}, Subscriber ${topicSubscriber.subscribers.garden ?? "*"} ${topicSubscriber.subscribers.namespace ?? "*"} ${topicSubscriber.subscribers.system ?? "*"} ${topicSubscriber.subscribers.version ?? "*"} ${topicSubscriber.subscribers.instance ?? "*"} ${topicSubscriber.subscribers.command ?? "*"}`}
                tooltip="Remove Subscriber"
                config={config}
                permission="PLUGIN_ADMIN"
              >
                <FontAwesomeIcon icon="xmark-square" />
              </AccessButton>
            )}
        </div>
      );
    }

    function topicButtonTemplate(topic: TopicFlatten) {
      const has_only_dynamic_subscribers = topicsRef.current
        .find((value: Topic) => value.id === topic.id)
        ?.subscribers?.every(
          (subscriber) => subscriber.subscriber_type == "DYNAMIC",
        );

      return (
        <Grid container>
          <Grid size="grow">
            <Typography sx={{ wordBreak: "break-word" }}>
              {topic.name}
            </Typography>
          </Grid>
          <Grid>
            <AccessButton
              basic
              rounded
              raised
              onClick={() =>
                addRequestItem({
                  topic: { id: topic.id } as Topic,
                  type: "VIEW_TOPIC",
                })
              }
              tooltip="View Topic"
              className="mr-2"
              aria-label={`ViewTopic ${topic?.name}`}
              config={config}
              permission="PLUGIN_ADMIN"
            >
              <FontAwesomeIcon icon="eye" />
            </AccessButton>
            <AccessButton
              basic
              rounded
              raised
              onClick={() => addSubscriber({ id: topic.id } as Topic)}
              aria-label={`Add Subscriber to Topic ${topic?.name}`}
              tooltip="Add Subscriber"
              className="mr-2"
              config={config}
              permission="PLUGIN_ADMIN"
            >
              <FontAwesomeIcon icon="square-plus" />
            </AccessButton>
            {has_only_dynamic_subscribers && (
              <AccessButton
                basic
                rounded
                raised
                onClick={() => deleteTopic({ id: topic.id } as Topic)}
                aria-label={`Delete Topic ${topic?.name}`}
                tooltip="Delete Topic"
                config={config}
                permission="PLUGIN_ADMIN"
              >
                <FontAwesomeIcon icon="trash" />
              </AccessButton>
            )}
          </Grid>
        </Grid>
      );
    }

    const handleChange = (event: any) => {
      setHideGenerated(event.checked);
      generatedRef.current = event.checked;
      loadTopics();
    };

    const header = (
      <div className="flex flex-wrap align-items-center justify-content-between gap-2">
        <span className="text-xl text-900 font-bold">Topics</span>
        <div className="flex-1 text-center">
          <Checkbox
            onChange={handleChange}
            checked={hideGenerated}
            className="mr-2"
            pt={{
              icon: {
                role: "img",
                "aria-label": "Image of toggle state for Hide Generated Topics",
              },
              input: { "aria-label": "Toggle state for Hide Generated Topics" },
            }}
          />
          Hide Generated
        </div>
      </div>
    );

    const tableColumns = [
      {
        id: "topic",
        label: "Topic",
        field: "name",
        isString: true,
        template: topicButtonTemplate,
      },
      {
        id: "publisher_count",
        label: "Publisher Count",
        field: "publisher_count",
        sortable: true,
        filterable: true,
        isNumeric: true,
        template: publisherCountTemplate,
      },
      {
        id: "subscribers.garden",
        label: "Garden",
        field: "subscribers.garden",
        sortable: true,
        filterable: true,
        isString: true,
        template: gardenTemplate,
      },
      {
        id: "subscribers.namespace",
        label: "Namespace",
        field: "subscribers.namespace",
        sortable: true,
        filterable: true,
        isString: true,
        template: namespaceTemplate,
      },
      {
        id: "subscribers.system",
        label: "System",
        field: "subscribers.system",
        sortable: true,
        filterable: true,
        isString: true,
        template: systemTemplate,
      },
      {
        id: "subscribers.version",
        label: "Version",
        field: "subscribers.version",
        sortable: true,
        filterable: true,
        isString: true,
        template: versionTemplate,
      },
      {
        id: "subscribers.instance",
        label: "Instance",
        field: "subscribers.instance",
        sortable: true,
        filterable: true,
        isString: true,
        template: instanceTemplate,
      },
      {
        id: "subscribers.command",
        label: "Command",
        field: "subscribers.command",
        sortable: true,
        filterable: true,
        isString: true,
        template: commandTemplate,
      },
      {
        id: "subscribers.consumer_count",
        label: "Consumer Count",
        field: "subscribers.consumer_count",
        sortable: true,
        filterable: true,
        isNumeric: true,
        template: consumerCountTemplate,
      },
      {
        id: "subscribers.subscriber_type",
        label: "Subscriber Type",
        field: "subscribers.subscriber_type",
        sortable: true,
        filterable: true,
        isString: true,
        template: subscriberTypeTemplate,
      },
    ] as ColumnField[];

    return (
      <>
        <EnhancedTable
          data={topics}
          columns={tableColumns}
          header={header}
          flattenBy="subscribers"
          groupBy="name"
          defaultOrderBy="name"
          defaultOrder="desc"
          isLoading={loading}
        />
      </>
    );
  }

  function handleDialogClose() {
    //Dismiss dialog
    setDialogVisible(false);
  }

  function handleDialogSubmit() {
    if (topicName) {
      const topicObj = {
        name: topicName,
        subscribers: subscriberList,
      } as Topic;
      if (topicId && topicId.current && isEdit.current) {
        //Editing existing topic
        const subscriberObj = subscriberList[0];
        if (!topicName) {
          return;
        }
        AddSubscriber(topicId.current, subscriberObj)
          .then(() => {
            loadTopics();
            setDialogVisible(false);
            showSnackbar({
              severity: "info",
              summary: "Added Subscriber(s)",
              detail: `Topic updated: ${topicObj.name}`,
              life: 3000,
            });
          })
          .catch((error) => {
            showSnackbar({
              severity: "error",
              summary: "Error",
              detail: `Error updating topic ${topicObj.name}: ${error}`,
              life: 3000,
            });
          });
      } else {
        CreateTopic(topicObj)
          .then((createdTopic: Topic) => {
            updateTopics([...topicsRef.current, createdTopic]);
            topicId.current = undefined;
            setDialogVisible(false);
            showSnackbar({
              severity: "info",
              summary: "Topic Created",
              detail: `New topic created: ${topicObj.name}`,
              life: 3000,
            });
          })
          .catch((error) => {
            showSnackbar({
              severity: "error",
              summary: "Error",
              detail: `Error creating topic: ${error}`,
              life: 3000,
            });
          });
      }
    } else {
      const reqs = [];
      if (!topicName) {
        reqs.push("Name");
      }
      msgs.current?.show({
        severity: "error",
        detail: `Missing required field(s): ${reqs.join(", ")}`,
        sticky: true,
      });
    }
  }

  return (
    <div>
      <Dialog
        data-testid="topic-dialog"
        appendTo={"self"}
        header={isEdit.current ? "Add Subscriber" : "Create Topic"}
        footer={
          <>
            <AccessButton onClick={handleDialogClose} label="Close" />
            <AccessButton
              data-testid={`submit-btn-dialog`}
              severity="danger"
              onClick={handleDialogSubmit}
              label="Submit"
            />
          </>
        }
        visible={dialogVisible}
        onHide={() => {
          handleDialogClose();
        }}
      >
        <Messages ref={msgs} />
        <div className="flex flex-column gap-2">
          <label htmlFor="topicName" className="font-bold">
            Name
          </label>
          <InputText
            required
            id="topicName"
            type="text"
            className="mb-2"
            value={topicName}
            onChange={(e: ChangeEvent<HTMLInputElement>) =>
              setTopicName(e.target.value)
            }
            disabled={isEdit.current}
            pt={{
              root: {
                "aria-label": undefined,
                required: undefined,
              },
            }}
          />
        </div>
        <Divider />
        <SubscriberItem
          subscriberList={subscriberList}
          setSubscriberList={setSubscriberList}
          isEdit={isEdit.current}
        />
      </Dialog>
      <TopicHeader />
      <TopicTable />
    </div>
  );
}

export default TopicIndex;
