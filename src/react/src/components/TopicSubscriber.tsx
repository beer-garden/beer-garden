import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Alert, Box, Checkbox, DialogActions, DialogContent, Grid, TextField, Typography } from "@mui/material";
import Dialog from "@mui/material/Dialog";
import DialogTitle from "@mui/material/DialogTitle";
import Divider from '@mui/material/Divider';
import { Messages } from "primereact/messages";
import {
  ChangeEvent,
  JSX,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import AccessButton from "../components/AccessButton";
import ConfirmDialog from "../components/ConfirmDialog";
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

function TopicSubscriber({topicId, topicName, showDialog, closeDialog}:{topicId?: string; topicName?: string; showDialog: boolean; closeDialog: () => void; }){

    const [alertItem, setAlertItem] = useState<string|undefined>(undefined);

     function handleDialogSubmit() {
    if (topicName) {
      setAlertItem(undefined);

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
      setAlertItem(`Missing required field(s): ${reqs.join(", ")}`);
    }
  }

    return (
        <Dialog
        data-testid="topic-dialog"
        open={showDialog}
        onClose={() => {
          closeDialog();
        }}
      >
        <DialogTitle>
          {isEdit.current ? "Add Subscriber" : "Create Topic"}
        </DialogTitle>
        <DialogContent>
        {alertItem && (
          <Alert severity="error">
            {alertItem}
          </Alert>
        )}
        <div className="flex flex-column gap-2">
          <label htmlFor="topicName" className="font-bold">
            Name
          </label>
          <TextField
                        
                        variant="outlined"
                        placeholder="Topic Name"
          value={topicName}
            onChange={(e: ChangeEvent<HTMLInputElement>) =>
              setTopicName(e.target.value)
            }
            disabled={isEdit.current}
            required
                      />
        </div>
        <Divider />
        <SubscriberItem
          subscriberList={subscriberList}
          setSubscriberList={setSubscriberList}
          isEdit={isEdit.current}
        />
        </DialogContent>
        <DialogActions>
            <>
            <AccessButton onClick={closeDialog} label="Close" >Close</AccessButton>
            <AccessButton
              data-testid={`submit-btn-dialog`}
              color="error"
              onClick={handleDialogSubmit}
              label="Submit"
            >Submit</AccessButton>
          </>
        </DialogActions>
      </Dialog>
    );
}

export default TopicSubscriber