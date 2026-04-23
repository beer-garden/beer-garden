import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { FilterMatchMode } from "primereact/api";
import { Button } from "primereact/button";
import { Checkbox } from "primereact/checkbox";
import { Column } from "primereact/column";
import { ConfirmDialog, confirmDialog } from "primereact/confirmdialog";
import { DataTable, SortOrder } from "primereact/datatable";
import { Dialog } from "primereact/dialog";
import { Divider } from "primereact/divider";
import { InputText } from "primereact/inputtext";
import { Messages } from "primereact/messages";
import { Toast } from "primereact/toast";
import { ChangeEvent, useCallback, useEffect, useRef, useState } from "react";

import SubscriberCard from "../components/SubscriberCard";
import { Subscriber, Topic } from "../models/brewtils-types";
import {
  AddSubscriber,
  CreateTopic,
  DeleteTopic,
  GetTopics,
  RemoveSubscriber,
  ResetCount,
  SyncTopics,
} from "../services/topic_service";

function TopicIndex() {
  const toast = useRef<Toast>(null);
  const [topics, setTopics] = useState<Array<Topic>>([]);
  const [loading, setLoading] = useState(false);
  const [first, setFirst] = useState<number>(0);
  const [rows, setRows] = useState<number>(10);
  const [filters, setFilters] = useState({
    name: {
      value: null,
      matchMode: FilterMatchMode.CONTAINS,
    },
    publisherCount: { value: null, matchMode: FilterMatchMode.EQUALS },
    subscribers: { value: null, matchMode: FilterMatchMode.CONTAINS },
  });
  const [sortField, setSortField] = useState<string | undefined>(undefined);
  const [sortOrder, setSortOrder] = useState<SortOrder>(undefined);
  const [showGenerated, setShowGenerated] = useState<boolean>(false);
  const generatedRef = useRef<boolean>(false);

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

    GetTopics({ include_generated: generatedRef.current })
      .then((topics: Array<Topic>) => {
        setTopics(topics);
        setLoading(false);
      })
      .catch((error) => {
        console.error("Error fetching topics:", error);
        setLoading(false);
      });
  }, [topics]);

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
          toast.current?.show({
            severity: "info",
            summary: "Confirmation",
            detail: "Sync Topics complete",
            life: 3000,
          });
        })
        .catch((error) => {
          console.error("Error deleting system:", error);
        });
    }

    return (
      <div className="flex items-end ml-2 page-header">
        <h1 className="flex-1">Topic Management</h1>
        <div>
          <Button
            onClick={handleSync}
            label="Sync Topics"
            data-testid="rescan-btn"
          />
          <Button
            onClick={openTopicDialog}
            label="Create Topic"
            data-testid="create-btn"
          />
        </div>
      </div>
    );
  }

  function TopicTable() {
    function clearCount(topic: Topic, subscriber?: Subscriber) {
      const accept = () => {
        ResetCount(topic.id, subscriber)
          .then(() => {
            if (toast && toast.current) {
              toast.current?.show({
                severity: "info",
                summary: "Confirmation",
                detail: `Cleared ${subscriber ? "consumer" : "publisher"} count for ${topic.name}`,
                life: 3000,
              });
            }
          })
          .catch((error) => {
            console.error("Error clearing count:", error);
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
          // Remove subscriber from topic
          const topicRemoveSubscriber = (
            topic: Topic,
            subscriber: Subscriber,
          ): Topic => {
            if (
              topic.subscribers &&
              topic.subscribers.some((s: Subscriber) => s === subscriber)
            ) {
              topic.subscribers = topic.subscribers.filter(
                (s: Subscriber) => s !== subscriber,
              );
              return topic;
            }
            return topic;
          };
          // Map the updated topic to list of topics
          const replaceTopic = (newTopic: Topic) => {
            setTopics((prevTopics) => {
              return prevTopics.map((topic) => {
                return topic.id == newTopic.id ? newTopic : topic;
              });
            });
          };
          const updatedTopic = topicRemoveSubscriber(topic, subscriber);
          replaceTopic(updatedTopic);
          toast.current?.show({
            severity: "info",
            summary: "Removed Subscriber",
            detail: `Topic updated: ${topic.name}`,
            life: 3000,
          });
        })
        .catch((error) => {
          console.error("Error removing subscriber:", error);
        });
    }

    function publisherCountTemplate(topic: Topic) {
      return (
        <div className="flex align-items-center gap-2">
          <span>{topic.publisher_count}</span>
          <Button
            size="small"
            tooltip="Clear count"
            onClick={() => clearCount(topic)}
          >
            <FontAwesomeIcon icon="0" />
          </Button>
        </div>
      );
    }

    function subscribersTemplate(topic: Topic) {
      return (
        <div style={{ overflowX: "auto" }}>
          {topic.subscribers && topic.subscribers?.length > 0 ? (
            <table
              className="table-auto w-full gap-2"
              style={{ borderCollapse: "collapse" }}
            >
              <thead className="border">
                <tr>
                  <th className="border border-1 px-2">Garden</th>
                  <th className="border border-1 px-2">Namespace</th>
                  <th className="border border-1 px-2">System</th>
                  <th className="border border-1 px-2">Version</th>
                  <th className="border border-1 px-2">Instance</th>
                  <th className="border border-1 px-2">Command</th>
                  <th
                    className="border border-1 px-2"
                    style={{ minWidth: "100px" }}
                  >
                    Consumer Count
                  </th>
                  <th
                    className="border border-1 px-2"
                    style={{ minWidth: "150px" }}
                  >
                    Type
                  </th>
                </tr>
              </thead>
              <tbody>
                {topic.subscribers?.map((subscriber) => (
                  <tr
                    key={`${subscriber.garden}.${subscriber.namespace}.${subscriber.system}.${subscriber.version}.${subscriber.instance}.${subscriber.command}`}
                  >
                    <td className="border border-1 px-2">
                      {subscriber.garden || "*"}
                    </td>
                    <td className="border border-1 px-2">
                      {subscriber.namespace || "*"}
                    </td>
                    <td className="border border-1 px-2">
                      {subscriber.system || "*"}
                    </td>
                    <td className="border border-1 px-2">
                      {subscriber.version || "*"}
                    </td>
                    <td className="border border-1 px-2">
                      {subscriber.instance || "*"}
                    </td>
                    <td className="border border-1 px-2">
                      {subscriber.command || "*"}
                    </td>
                    <td className="border border-1 px-2">
                      <div className="flex align-items-center gap-2">
                        <span>{subscriber.consumer_count}</span>
                        {subscriber.consumer_count > -1 && (
                          <Button
                            size="small"
                            className="ml-2"
                            tooltip="Clear count"
                            onClick={() => clearCount(topic, subscriber)}
                          >
                            <FontAwesomeIcon icon="0" />
                          </Button>
                        )}
                      </div>
                    </td>
                    <td className="border border-1 px-2">
                      <div className="flex align-items-center gap-2">
                        <span>{subscriber.subscriber_type}</span>
                        {subscriber.subscriber_type == "DYNAMIC" && (
                          <Button
                            onClick={() => removeSubscriber(topic, subscriber)}
                            size="small"
                            className="ml-2"
                            tooltip="Remove Subscriber"
                          >
                            <FontAwesomeIcon icon="xmark-square" />
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p>No subscribers</p>
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
            setTopics((currentTopics) => {
              return currentTopics.filter((t) => t.id !== topic.id);
            });
            if (toast && toast.current) {
              toast.current?.show({
                severity: "info",
                summary: "Confirmation",
                detail: `Deleted topic ${topic.name}`,
                life: 3000,
              });
            }
          })
          .catch((error) => {
            console.error("Error deleting topic:", error);
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

    function topicButtonTemplate(topic: Topic) {
      const has_only_dynamic_subscribers = topic.subscribers?.every(
        (subscriber) => subscriber.subscriber_type == "DYNAMIC",
      );

      return (
        <>
          {has_only_dynamic_subscribers && (
            <Button onClick={() => deleteTopic(topic)} tooltip="Delete Topic">
              <FontAwesomeIcon icon="trash" />
            </Button>
          )}
          <Button onClick={() => addSubscriber(topic)} tooltip="Add Subscriber">
            <FontAwesomeIcon icon="pencil" />
          </Button>
        </>
      );
    }

    const handleChange = (event: any) => {
      setShowGenerated(event.checked);
      generatedRef.current = event.checked;
      loadTopics();
    };

    const header = (
      <div className="flex flex-wrap align-items-center justify-content-between gap-2">
        <span className="text-xl text-900 font-bold">Topics</span>
        <div>
          <Checkbox
            onChange={handleChange}
            checked={showGenerated}
            className="mr-2"
          />
          Show Generated
        </div>
      </div>
    );

    function myFilterFunction(subscribers: Subscriber[], filter: any) {
      console.log(subscribers);
      console.log(filter);
    }

    return (
      // Add generated checkbox and set to true
      // http://localhost:8080/api/v1/topics?columns=%7B%22data%22:%22name%22,%22name%22:%22%22,%22searchable%22:true,%22orderable%22:true,%22search%22:%7B%22value%22:%22%22,%22regex%22:false%7D%7D&columns=%7B%22data%22:%22publisher_count%22,%22name%22:%22%22,%22searchable%22:true,%22orderable%22:true,%22search%22:%7B%22value%22:%22%22,%22regex%22:false%7D%7D&columns=%7B%22data%22:%22subscribers%22,%22name%22:%22%22,%22searchable%22:true,%22orderable%22:true,%22search%22:%7B%22value%22:%22%22,%22regex%22:false%7D%7D&columns=%7B%22data%22:null,%22name%22:%22%22,%22searchable%22:true,%22orderable%22:false,%22search%22:%7B%22value%22:%22%22,%22regex%22:false%7D%7D&columns=%7B%22data%22:%22id%22%7D&draw=5&length=100&order=%7B%22column%22:0,%22dir%22:%22asc%22%7D&search=%7B%22value%22:%22%22,%22regex%22:false%7D&start=0
      // http://localhost:8080/api/v1/topics?columns=%7B%22data%22:%22name%22,%22name%22:%22%22,%22searchable%22:true,%22orderable%22:true,%22search%22:%7B%22value%22:%22%22,%22regex%22:false%7D%7D&columns=%7B%22data%22:%22publisher_count%22,%22name%22:%22%22,%22searchable%22:true,%22orderable%22:true,%22search%22:%7B%22value%22:%22%22,%22regex%22:false%7D%7D&columns=%7B%22data%22:%22subscribers%22,%22name%22:%22%22,%22searchable%22:true,%22orderable%22:true,%22search%22:%7B%22value%22:%22%22,%22regex%22:false%7D%7D&columns=%7B%22data%22:null,%22name%22:%22%22,%22searchable%22:true,%22orderable%22:false,%22search%22:%7B%22value%22:%22%22,%22regex%22:false%7D%7D&columns=%7B%22data%22:%22id%22%7D&draw=4&include_generated=true&length=100&order=%7B%22column%22:0,%22dir%22:%22asc%22%7D&search=%7B%22value%22:%22%22,%22regex%22:false%7D&start=0

      <>
        <ConfirmDialog />
        <DataTable
          data-testid="topic-datatable"
          value={topics}
          loading={loading}
          header={header}
          paginator
          rows={rows}
          first={first}
          filterDisplay="row"
          filters={filters}
          onFilter={(e) => setFilters(e.filters as typeof filters)}
          sortField={sortField}
          sortOrder={sortOrder}
          rowsPerPageOptions={[10, 25, 50]}
          onPage={(e: any) => {
            setFirst(e.first);
            setRows(e.rows);
          }}
          onSort={(e: any) => {
            setSortField(e.sortField);
            setSortOrder(e.sortOrder);
            setFirst(0);
          }}
          dataKey="id"
        >
          <Column
            field="name"
            sortable
            filter
            header="Topic"
            style={{ width: "20%" }}
          />
          <Column
            field="publisher_count"
            sortable
            filter
            header="Publisher Count"
            body={publisherCountTemplate}
            showFilterMenu={false}
            style={{ width: "7%" }}
          />
          <Column
            field="subscribers"
            sortable
            filter
            header="Subscribers"
            body={subscribersTemplate}
            filterMatchMode="custom"
            filterFunction={myFilterFunction}
          />
          <Column
            header=""
            body={topicButtonTemplate}
            style={{ minWidth: "150px", width: "10%" }}
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
            toast.current?.show({
              severity: "info",
              summary: "Added Subscriber(s)",
              detail: `Topic updated: ${topicObj.name}`,
              life: 3000,
            });
          })
          .catch((error) => {
            console.error("Error editing the topic:", error);
          });
      } else {
        // Create new role
        CreateTopic(topicObj)
          .then((createdTopic: Topic) => {
            setTopics([...topics, createdTopic]);
            topicId.current = undefined;
            setDialogVisible(false);
            toast.current?.show({
              severity: "info",
              summary: "Topic Created",
              detail: `New topic created: ${topicObj.name}`,
              life: 3000,
            });
          })
          .catch((error) => {
            console.error("Error creating the topic:", error);
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
      <Toast ref={toast} />
      <Dialog
        data-testid="topic-dialog"
        appendTo={"self"}
        header={isEdit.current ? "Add Subscriber" : "Create Topic"}
        footer={
          <>
            <Button onClick={handleDialogClose}>Close</Button>
            <Button
              data-testid={`submit-btn-dialog`}
              severity="danger"
              onClick={handleDialogSubmit}
            >
              Submit
            </Button>
          </>
        }
        visible={dialogVisible}
        style={{ width: "50vw" }}
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
          />
        </div>
        <Divider />
        <SubscriberCard
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
