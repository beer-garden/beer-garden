import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
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

interface TopicSubscriber {
  topic?: Topic;
  subscriber?: Subscriber;
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
  const [topicSubscribers, setTopicSubscribers] = useState<
    Array<TopicSubscriber>
  >([]);
  const [rawTopics, setRawTopics] = useState<Topic[]>([]);
  const [loading, setLoading] = useState(false);
  const [first, setFirst] = useState<number>(0);
  const [rows, setRows] = useState<number>(10);
  const [filters] = useState({
    "topic.name": {
      value: null,
      matchMode: FilterMatchMode.CONTAINS,
    },
    "topic.publisher_count": { value: null, matchMode: FilterMatchMode.EQUALS },
    "subscriber.namespace": {
      value: null,
      matchMode: FilterMatchMode.CONTAINS,
    },
    "subscriber.garden": { value: null, matchMode: FilterMatchMode.CONTAINS },
    "subscriber.system": { value: null, matchMode: FilterMatchMode.CONTAINS },
    "subscriber.version": { value: null, matchMode: FilterMatchMode.CONTAINS },
    "subscriber.instance": { value: null, matchMode: FilterMatchMode.CONTAINS },
    "subscriber.command": { value: null, matchMode: FilterMatchMode.CONTAINS },
    "subscriber.consumer_count": {
      value: null,
      matchMode: FilterMatchMode.EQUALS,
    },
    "subscriber.subscriber_type": {
      value: null,
      matchMode: FilterMatchMode.CONTAINS,
    },
  });
  const [sortField, setSortField] = useState<string | undefined>(undefined);
  const [sortOrder, setSortOrder] = useState<SortOrder>(undefined);
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
      .then((topics: Array<Topic>) => {
        const topicSubscribers: TopicSubscriber[] = topics.flatMap(
          (topic: Topic) => {
            const subscribers = topic.subscribers || [];
            return subscribers.map((subscriber: Subscriber) => {
              return { topic: topic, subscriber: subscriber };
            });
          },
        );
        setTopicSubscribers(topicSubscribers);
        setRawTopics(topics);
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
  }, [topicSubscribers]);

  useEffect(() => {
    loadTopics();
  }, []);

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
      <div className="flex items-end ml-2 page-header">
        <h1 className="flex-1">Topic Management</h1>

        <div>
          <AccessButton
            raised
            onClick={handleSync}
            label="Sync Topics"
            data-testid="rescan-btn"
            config={config}
            permission="PLUGIN_ADMIN"
            className="mr-2"
          />
          <AccessButton
            raised
            onClick={openTopicDialog}
            label="Create Topic"
            data-testid="create-btn"
            config={config}
            permission="PLUGIN_ADMIN"
            className="mr-2"
          />
        </div>
      </div>
    );
  }

  function TopicTable() {
    function clearCount(topic: Topic, subscriber?: Subscriber) {
      const accept = () => {
        ResetCount(topic.id, subscriber)
          .then((updatedTopic: Topic) => {
            if (subscriber) {
              setTopicSubscribers((currTopicSubscribers: TopicSubscriber[]) => {
                const subscribers = updatedTopic.subscribers || [];
                const updatedSubscriber: Subscriber = subscribers.find(
                  (s) =>
                    s.command == subscriber.command &&
                    s.instance == subscriber.instance &&
                    s.version == subscriber.version &&
                    s.system == subscriber.system &&
                    s.garden == subscriber.garden &&
                    s.namespace == subscriber.namespace,
                );
                const newTopicSubscribers = currTopicSubscribers.map(
                  (topicSubscriber: TopicSubscriber) => {
                    return topicSubscriber.topic?.id === topic.id
                      ? {
                          ...topicSubscriber,
                          topic: updatedTopic,
                          subscriber: updatedSubscriber,
                        }
                      : topicSubscriber;
                  },
                );
                return newTopicSubscribers;
              });
            } else {
              setTopicSubscribers((currTopicSubscribers: TopicSubscriber[]) => {
                const newTopicSubscribers = currTopicSubscribers.map(
                  (topicSubscriber: TopicSubscriber) => {
                    return topicSubscriber.topic?.id === topic.id
                      ? { ...topicSubscriber, topic: updatedTopic }
                      : topicSubscriber;
                  },
                );
                return newTopicSubscribers;
              });
            }
            showSnackbar({
              severity: "info",
              summary: "Confirmation",
              detail: `Cleared ${subscriber ? "consumer" : "publisher"} count for ${topic.name}`,
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
          message: `Are you sure you want to reset the ${subscriber ? "consumer" : "publisher"} count?`,
          header: `Confirm Clear ${subscriber ? "Consumer" : "Publisher"} Count ${topic.name}`,
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
          setTopicSubscribers((currentTopicSubscribers: TopicSubscriber[]) => {
            const newTopicSubs = currentTopicSubscribers.filter(
              (ts: TopicSubscriber) => {
                return (
                  ts.topic?.id !== topic.id ||
                  (ts.topic?.id == topic.id && ts.subscriber !== subscriber)
                );
              },
            );
            return newTopicSubs;
          });
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

    function publisherCountTemplate(topicSubscriber: TopicSubscriber) {
      return (
        <div className="flex align-items-center gap-2">
          <span>{topicSubscriber.topic?.publisher_count}</span>

          {((topicSubscriber.topic !== undefined &&
            topicSubscriber.topic.publisher_count) ||
            0) > 0 && (
            <AccessButton
              basic
              rounded
              raised
              size="small"
              aria-label={`Clear Publisher Count ${topicSubscriber.topic?.publisher_count} from Topic ${topicSubscriber.topic?.name}`}
              tooltip="Clear Publisher Count"
              onClick={() => clearCount(topicSubscriber.topic as Topic)}
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
            setTopicSubscribers((currentTopicSubscribers) => {
              return currentTopicSubscribers.filter(
                (ts: TopicSubscriber) => ts.topic?.id !== topic.id,
              );
            });
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

    function gardenTemplate(topicSubscriber: TopicSubscriber) {
      return topicSubscriber.subscriber?.garden || "*";
    }

    function namespaceTemplate(topicSubscriber: TopicSubscriber) {
      return topicSubscriber.subscriber?.namespace || "*";
    }

    function systemTemplate(topicSubscriber: TopicSubscriber) {
      return topicSubscriber.subscriber?.system || "*";
    }

    function versionTemplate(topicSubscriber: TopicSubscriber) {
      return topicSubscriber.subscriber?.version || "*";
    }

    function instanceTemplate(topicSubscriber: TopicSubscriber) {
      return topicSubscriber.subscriber?.instance || "*";
    }

    function commandTemplate(topicSubscriber: TopicSubscriber) {
      return topicSubscriber.subscriber?.command || "*";
    }

    function consumerCountTemplate(topicSubscriber: TopicSubscriber) {
      return (
        <div className="flex align-items-center gap-2">
          <span>{topicSubscriber.subscriber?.consumer_count}</span>

          {topicSubscriber.subscriber != undefined &&
            topicSubscriber.subscriber.consumer_count != undefined &&
            (topicSubscriber.subscriber.consumer_count || 0) > 0 && (
              <AccessButton
                basic
                rounded
                raised
                size="small"
                className="ml-2"
                aria-label={`Clear Count of ${topicSubscriber.subscriber.consumer_count} for Topic ${topicSubscriber?.topic?.name} Subscriber ${topicSubscriber.subscriber.garden ?? "*"} ${topicSubscriber.subscriber.namespace ?? "*"} ${topicSubscriber.subscriber.system ?? "*"} ${topicSubscriber.subscriber.version ?? "*"} ${topicSubscriber.subscriber.instance ?? "*"} ${topicSubscriber.subscriber.command ?? "*"}`}
                tooltip="Clear count"
                onClick={() =>
                  clearCount(
                    topicSubscriber.topic as Topic,
                    topicSubscriber.subscriber as Subscriber,
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

    function subscriberTypeTemplate(topicSubscriber: TopicSubscriber) {
      return (
        <div className="flex align-items-center gap-2">
          <span>{topicSubscriber.subscriber?.subscriber_type}</span>

          {topicSubscriber.subscriber !== undefined &&
            topicSubscriber.subscriber.subscriber_type == "DYNAMIC" && (
              <AccessButton
                basic
                rounded
                raised
                onClick={() =>
                  removeSubscriber(
                    topicSubscriber.topic!,
                    topicSubscriber.subscriber!,
                  )
                }
                size="small"
                className="ml-2"
                aria-label={`Remove from Topic ${topicSubscriber?.topic?.name}, Subscriber ${topicSubscriber.subscriber.garden ?? "*"} ${topicSubscriber.subscriber.namespace ?? "*"} ${topicSubscriber.subscriber.system ?? "*"} ${topicSubscriber.subscriber.version ?? "*"} ${topicSubscriber.subscriber.instance ?? "*"} ${topicSubscriber.subscriber.command ?? "*"}`}
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

    function topicButtonTemplate(topicSubscriber: TopicSubscriber) {
      const has_only_dynamic_subscribers =
        topicSubscriber.topic?.subscribers?.every(
          (subscriber) => subscriber.subscriber_type == "DYNAMIC",
        );

      return (
        <div className="flex">
          <AccessButton
            basic
            rounded
            raised
            onClick={() =>
              addRequestItem({
                topic: topicSubscriber.topic,
                type: "VIEW_TOPIC",
              })
            }
            tooltip="View Topic"
            className="mr-2"
            aria-label={`ViewTopic ${topicSubscriber.topic?.name}`}
            config={config}
            permission="PLUGIN_ADMIN"
          >
            <FontAwesomeIcon icon="eye" />
          </AccessButton>
          <AccessButton
            basic
            rounded
            raised
            onClick={() => addSubscriber(topicSubscriber.topic!)}
            aria-label={`Add Subscriber to Topic ${topicSubscriber.topic?.name}`}
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
              onClick={() => deleteTopic(topicSubscriber.topic!)}
              aria-label={`Delete Topic ${topicSubscriber.topic?.name}`}
              tooltip="Delete Topic"
              config={config}
              permission="PLUGIN_ADMIN"
            >
              <FontAwesomeIcon icon="trash" />
            </AccessButton>
          )}
        </div>
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

    // Custom filter template
    const filterElement = (props: any) => {
      return (
        <InputText
          value={props.value}
          onChange={(e) => props.filterApplyCallback(e.target.value)}
          pt={{
            root: {
              autoComplete: "off",
              "aria-label": `Input Filter for ${props?.field}`,
              type: "text",
            },
          }}
        />
      );
    };

    const tableColumns = [
      {
        id: "topic",
        label: "Topic",
        field: "name",
        isString: true,
      },
      {
        id: "publisher_count",
        label: "Publisher Count",
        field: "publisher_count",
        sortable: true,
        filterable: true,
        isNumeric: true,
      },
      {
        id: "subscribers.garden",
        label: "Garden",
        field: "subscribers.garden",
        sortable: true,
        filterable: true,
        isString: true,
      },
      {
        id: "subscribers.namespace",
        label: "Namespace",
        field: "subscribers.namespace",
        sortable: true,
        filterable: true,
        isString: true,
      },
      {
        id: "subscribers.system",
        label: "System",
        field: "subscribers.system",
        sortable: true,
        filterable: true,
        isString: true,
      },
      {
        id: "subscribers.version",
        label: "Version",
        field: "subscribers.version",
        sortable: true,
        filterable: true,
        isString: true,
      },
      {
        id: "subscribers.instance",
        label: "Instance",
        field: "subscribers.instance",
        sortable: true,
        filterable: true,
        isString: true,
      },
      {
        id: "subscribers.command",
        label: "Command",
        field: "subscribers.command",
        sortable: true,
        filterable: true,
        isString: true,
      },
      {
        id: "subscribers.consumer_count",
        label: "Consumer Count",
        field: "subscribers.consumer_count",
        sortable: true,
        filterable: true,
        isNumeric: true,
      },
      {
        id: "subscribers.subscriber_type",
        label: "Subscriber Type",
        field: "subscribers.subscriber_type",
        sortable: true,
        filterable: true,
        isString: true,
      },
    ] as ColumnField[];

    return (
      <>
        <EnhancedTable
          data={rawTopics}
          columns={tableColumns}
          header={header}
          flattenBy="subscribers"
          groupBy="name"
          // remoteFilter={tableLoadData}
          // dataLength={filteredRecords}
          // totalDataLength={totalRecords}
          // reloadTable={reloadRequestsTrigger}
          defaultOrderBy="name"
          defaultOrder="desc"
          // isLoading={loading}
        />
        <DataTable
          data-testid="topic-datatable"
          value={topicSubscribers}
          loading={loading}
          header={header}
          paginator
          rows={rows}
          first={first}
          filterDisplay="row"
          filters={filters}
          rowGroupMode="rowspan"
          groupRowsBy="topic.name"
          sortField={sortField}
          sortOrder={sortOrder}
          rowsPerPageOptions={[10, 25, 50]}
          paginatorTemplate={PaginatorTemplate}
          onPage={(e: any) => {
            setFirst(e.first);
            setRows(e.rows);
          }}
          onSort={(e: any) => {
            setSortField(e.sortField);
            setSortOrder(e.sortOrder);
            setFirst(0);
          }}
        >
          <Column
            field="topic.name"
            sortable
            filter
            header="Topic"
            style={{ maxWidth: "400px", overflowWrap: "break-word" }}
            showFilterMenu={false}
            filterElement={filterElement}
          />
          <Column field="topic.name" header="" body={topicButtonTemplate} />
          <Column
            field="topic.publisher_count"
            sortable
            filter
            header="Publisher Count"
            body={publisherCountTemplate}
            showFilterMenu={false}
            filterElement={filterElement}
          />
          <Column
            field="subscriber.garden"
            sortable
            filter
            header="Garden"
            body={gardenTemplate}
            showFilterMenu={false}
            filterElement={filterElement}
          />
          <Column
            field="subscriber.namespace"
            sortable
            filter
            header="Namespace"
            body={namespaceTemplate}
            showFilterMenu={false}
            filterElement={filterElement}
          />
          <Column
            field="subscriber.system"
            sortable
            filter
            header="System"
            body={systemTemplate}
            showFilterMenu={false}
            filterElement={filterElement}
          />
          <Column
            field="subscriber.version"
            sortable
            filter
            header="Version"
            body={versionTemplate}
            showFilterMenu={false}
            filterElement={filterElement}
          />
          <Column
            field="subscriber.instance"
            sortable
            filter
            header="Instance"
            body={instanceTemplate}
            showFilterMenu={false}
            filterElement={filterElement}
          />
          <Column
            field="subscriber.command"
            sortable
            filter
            header="Command"
            body={commandTemplate}
            style={{ maxWidth: "300px", overflowWrap: "break-word" }}
            showFilterMenu={false}
            filterElement={filterElement}
          />
          <Column
            field="subscriber.consumer_count"
            sortable
            filter
            header="Consumer Count"
            body={consumerCountTemplate}
            showFilterMenu={false}
            filterElement={filterElement}
          />
          <Column
            field="subscriber.subscriber_type"
            sortable
            filter
            header="Subscriber Type"
            body={subscriberTypeTemplate}
            showFilterMenu={false}
            filterElement={filterElement}
          />
        </DataTable>
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
            const subscribers = createdTopic.subscribers;
            const newTopicSubscribers = subscribers?.map(
              (subscriber: Subscriber) => {
                return {
                  topic: createdTopic,
                  subscriber: subscriber,
                } as TopicSubscriber;
              },
            );
            setTopicSubscribers([
              ...topicSubscribers,
              ...(newTopicSubscribers || []),
            ]);
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
