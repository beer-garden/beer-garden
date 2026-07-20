import "react-js-cron/dist/styles.css";

import {
  Box,
  Button,
  ButtonGroup,
  FormLabel,
  Grid,
  TextField,
  Typography,
} from "@mui/material";
import { Calendar } from "primereact/calendar";
import { Checkbox } from "primereact/checkbox";
import { Dropdown } from "primereact/dropdown";
import { InputNumber } from "primereact/inputnumber";
import { InputText } from "primereact/inputtext";
import { MultiSelect } from "primereact/multiselect";
import { ChangeEvent, useEffect, useState } from "react";
import { Cron } from "react-js-cron";

import {
  CronTrigger,
  DateTrigger,
  FileTrigger,
  IntervalTrigger,
  Job,
} from "../models/brewtils-types";
import { CompareObjects } from "../services/util_service";

interface SchedulerFormProps {
  scheduledJob: Job | undefined;
  setScheduledJob: (job: Job | undefined) => void;
  setIsJobValid: (isValid: boolean) => void;
}

interface LayoutProps {
  labelWidth: string;
  valueWidth: string;
}

function FileForm({
  fileTrigger,
  setFileTrigger,
  layoutProps,
}: {
  fileTrigger: FileTrigger | null;
  setFileTrigger: (trigger: FileTrigger) => void;
  layoutProps: LayoutProps;
}) {
  const CREATE = "Create";
  const MODIFY = "Modify";
  const MOVE = "Move";
  const DELETE = "Delete";
  const typeOptions = [CREATE, MODIFY, MOVE, DELETE];

  const defaultTypes = [];

  if (fileTrigger?.create) {
    defaultTypes.push(CREATE);
  }
  if (fileTrigger?.modify) {
    defaultTypes.push(MODIFY);
  }
  if (fileTrigger?.move) {
    defaultTypes.push(MOVE);
  }
  if (fileTrigger?.delete) {
    defaultTypes.push(DELETE);
  }

  const [selectedTypes, setSelectedTypes] =
    useState<Array<string>>(defaultTypes);

  useEffect(() => {
    let updateNeeded = false;
    let updates = {};

    if (!fileTrigger) {
      updateNeeded = true;
      updates = {
        create: selectedTypes.includes(CREATE),
        modify: selectedTypes.includes(MODIFY),
        move: selectedTypes.includes(MOVE),
        delete: selectedTypes.includes(DELETE),
      };
    } else {
      if (fileTrigger?.create !== selectedTypes.includes(CREATE)) {
        updateNeeded = true;
        updates = { ...updates, ...{ create: selectedTypes.includes(CREATE) } };
      }
      if (fileTrigger?.modify !== selectedTypes.includes(MODIFY)) {
        updateNeeded = true;
        updates = { ...updates, ...{ modify: selectedTypes.includes(MODIFY) } };
      }
      if (fileTrigger?.move !== selectedTypes.includes(MOVE)) {
        updateNeeded = true;
        updates = { ...updates, ...{ move: selectedTypes.includes(MOVE) } };
      }
      if (fileTrigger?.delete !== selectedTypes.includes(DELETE)) {
        updateNeeded = true;
        updates = { ...updates, ...{ delete: selectedTypes.includes(DELETE) } };
      }
    }
    if (updateNeeded) {
      setFileTrigger({
        ...fileTrigger,
        ...updates,
      });
    }
  }, [selectedTypes, fileTrigger, setFileTrigger]);

  if (fileTrigger === null) {
    setFileTrigger({});
  }

  return (
    <div>
      <div className="flex ml-2 mb-2">
        <div style={{ width: layoutProps.labelWidth }}>
          <label htmlFor="path">Path</label>
        </div>
        <div style={{ width: layoutProps.valueWidth }}>
          <InputText
            id="path"
            value={fileTrigger?.path ?? ""}
            onChange={(e) => {
              setFileTrigger({ ...fileTrigger, ...{ path: e.target.value } });
            }}
            invalid={
              fileTrigger?.path === undefined ||
              fileTrigger?.path === null ||
              fileTrigger?.path === ""
            }
            pt={{
              root: {
                autoComplete: "off",
              },
            }}
          />
        </div>
      </div>
      <div className="flex ml-2 mb-2">
        <div style={{ width: layoutProps.labelWidth }}>
          <label htmlFor="pattern">Pattern</label>
        </div>
        <div style={{ width: layoutProps.valueWidth }}>
          <InputText
            id="pattern"
            value={fileTrigger?.pattern}
            onChange={(e) => {
              setFileTrigger({
                ...fileTrigger,
                ...{ pattern: e.target.value },
              });
            }}
            pt={{
              root: {
                autoComplete: "off",
              },
            }}
          />
        </div>
      </div>
      <div className="flex ml-2 mb-2">
        <div style={{ width: layoutProps.labelWidth }}>
          <label htmlFor="recursive">Recursive</label>
        </div>
        <div style={{ width: layoutProps.valueWidth }}>
          <Checkbox
            id="recursive"
            onChange={(e) => {
              setFileTrigger({
                ...fileTrigger,
                ...{ recursive: e.checked },
              });
            }}
            checked={fileTrigger?.recursive === true}
            pt={{
              input: {
                "aria-label": "Recursive Checkbox",
              },
              icon: {
                role: "img",
                "aria-label": "Selection for Recursive Checkbox",
              },
            }}
          ></Checkbox>
        </div>
      </div>
      <div className="flex ml-2 mb-2">
        <div style={{ width: layoutProps.labelWidth }}>
          <label htmlFor="eventTypes">Event Types</label>
        </div>
        <div style={{ width: layoutProps.valueWidth }}>
          <MultiSelect
            id="eventTypes"
            value={selectedTypes}
            onChange={(e) => setSelectedTypes(e.value)}
            options={typeOptions}
            placeholder="Select Event Type"
          />
        </div>
      </div>
    </div>
  );
}

function DateForm({
  dateTrigger,
  setDateTrigger,
  layoutProps,
}: {
  dateTrigger: DateTrigger | null;
  setDateTrigger: (trigger: DateTrigger) => void;
  layoutProps: LayoutProps;
}) {
  const [runDate, setRunDate] = useState(
    dateTrigger?.run_date
      ? new Date(dateTrigger.run_date)
      : dateTrigger?.run_date,
  );

  const updateRunDate = (updatedRunDate: any) => {
    if (updatedRunDate) {
      setRunDate(updatedRunDate);
      if (
        !dateTrigger ||
        dateTrigger.run_date !== new Date(updatedRunDate).getTime()
      ) {
        setDateTrigger({
          ...dateTrigger,
          ...{ run_date: new Date(updatedRunDate).getTime() },
        });
      }
    }
  };

  return (
    <div>
      <div className="flex ml-2 mb-2">
        <div style={{ width: layoutProps.labelWidth }}>
          <label htmlFor="runDate">Run Date</label>
        </div>
        <div style={{ width: layoutProps.valueWidth }}>
          <Calendar
            id="runDate"
            value={runDate}
            showTime
            hourFormat="24"
            onChange={(e: any) => updateRunDate(e.value)}
            invalid={
              runDate === undefined || runDate === null || runDate === ""
            }
            pt={{
              input: {
                root: ({ context }: { context: any }) => {
                  if (!context.disabled) {
                    return {
                      "aria-label": `Run Date`,
                      "aria-controls": undefined,
                      "aria-description":
                        "Select Date and Time, aria-controls removed when popup is not in DOM",
                    };
                  }
                  return {
                    "aria-label": `Run Date`,
                    "aria-description": "Select Date and Time",
                  };
                },
              },
            }}
          />
        </div>
      </div>
      <div className="flex ml-2 mb-2">
        <div style={{ width: layoutProps.labelWidth }}>
          <label htmlFor="timezone">Timezone</label>
        </div>
        <div style={{ width: layoutProps.valueWidth }}>
          <InputText
            id="timezone"
            value={dateTrigger?.timezone}
            onChange={(e) => {
              setDateTrigger({
                ...dateTrigger,
                ...{ timezone: e.target.value },
              });
            }}
            pt={{
              root: {
                autoComplete: "off",
              },
            }}
          />
        </div>
      </div>
    </div>
  );
}

function IntervalForm({
  intervalTrigger,
  setIntervalTrigger,
  layoutProps,
}: {
  intervalTrigger: IntervalTrigger | null;
  setIntervalTrigger: (trigger: IntervalTrigger) => void;
  layoutProps: LayoutProps;
}) {
  const typeOptions = ["seconds", "minutes", "hours", "days", "weeks"];

  let defaultIntervalType = "seconds";
  let defaultIntervalNumber = 0;

  if (intervalTrigger?.seconds && intervalTrigger.seconds > 0) {
    defaultIntervalType = "seconds";
    defaultIntervalNumber = intervalTrigger.seconds;
  } else if (intervalTrigger?.minutes && intervalTrigger.minutes > 0) {
    defaultIntervalType = "minutes";
    defaultIntervalNumber = intervalTrigger.minutes;
  } else if (intervalTrigger?.hours && intervalTrigger.hours > 0) {
    defaultIntervalType = "hours";
    defaultIntervalNumber = intervalTrigger.hours;
  } else if (intervalTrigger?.days && intervalTrigger.days > 0) {
    defaultIntervalType = "days";
    defaultIntervalNumber = intervalTrigger.days;
  } else if (intervalTrigger?.weeks && intervalTrigger.weeks > 0) {
    defaultIntervalType = "weeks";
    defaultIntervalNumber = intervalTrigger.weeks;
  }

  const [intervalType, setIntervalType] = useState(defaultIntervalType || null);
  const [intervalNumber, setIntervalNumber] = useState(
    defaultIntervalNumber || null,
  );

  const [startDate, setStartDate] = useState(
    typeof intervalTrigger?.startDate === "string"
      ? new Date(intervalTrigger.startDate)
      : intervalTrigger?.startDate,
  );
  const [endDate, setEndDate] = useState(
    typeof intervalTrigger?.endDate === "string"
      ? new Date(intervalTrigger.endDate)
      : intervalTrigger?.endDate,
  );

  useEffect(() => {
    let updateNeeded = false;
    let updates = {};

    if (!intervalTrigger) {
      updateNeeded = true;
      updates = {
        seconds:
          intervalNumber && intervalType === "seconds" ? intervalNumber : 0,
        minutes:
          intervalNumber && intervalType === "minutes" ? intervalNumber : 0,
        hours: intervalNumber && intervalType === "hours" ? intervalNumber : 0,
        days: intervalNumber && intervalType === "days" ? intervalNumber : 0,
        weeks: intervalNumber && intervalType === "weeks" ? intervalNumber : 0,
        endDate: endDate,
        startDate: startDate,
      };
    } else {
      if (intervalTrigger?.endDate !== endDate) {
        updateNeeded = true;
        updates = { ...updates, ...{ endDate: endDate } };
      }

      if (intervalTrigger?.startDate !== startDate) {
        updateNeeded = true;
        updates = { ...updates, ...{ startDate: startDate } };
      }

      const intervalUpdates = {
        seconds:
          intervalNumber && intervalType === "seconds" ? intervalNumber : 0,
        minutes:
          intervalNumber && intervalType === "minutes" ? intervalNumber : 0,
        hours: intervalNumber && intervalType === "hours" ? intervalNumber : 0,
        days: intervalNumber && intervalType === "days" ? intervalNumber : 0,
        weeks: intervalNumber && intervalType === "weeks" ? intervalNumber : 0,
      };

      if (
        intervalTrigger?.seconds !== intervalUpdates.seconds ||
        intervalTrigger?.minutes !== intervalUpdates.minutes ||
        intervalTrigger?.hours !== intervalUpdates.hours ||
        intervalTrigger?.days !== intervalUpdates.days ||
        intervalTrigger?.weeks !== intervalUpdates.weeks
      ) {
        updateNeeded = true;
        updates = { ...updates, ...intervalUpdates };
      }
    }

    if (updateNeeded) {
      setIntervalTrigger({ ...intervalTrigger, ...updates });
    }
  }, [
    intervalType,
    intervalNumber,
    startDate,
    endDate,
    intervalTrigger,
    setIntervalTrigger,
  ]);

  return (
    <div>
      <div className="flex ml-2 mb-2">
        <div style={{ width: layoutProps.labelWidth }}>
          <label htmlFor="intervalNumber">Interval Number</label>
        </div>
        <div style={{ width: layoutProps.valueWidth }}>
          <InputNumber
            id="intervalNumber"
            value={intervalNumber}
            onChange={(e) => setIntervalNumber(e.value)}
            min={1}
            incrementButtonIcon="pi pi-chevron-up"
            decrementButtonIcon="pi pi-chevron-down"
            pt={{
              input: {
                root: {
                  "aria-label": `Interval Number`,
                  autoComplete: "off",
                },
              },
              incrementButton: {
                tabIndex: 0,
                "aria-label": `Increase Interval Number by 1`,
                "aria-hidden": "false",
              },
              decrementButton: {
                tabIndex: 0,
                "aria-label": `Decrease Interval Number by 1`,
                "aria-hidden": "false",
              },
              incrementIcon: {
                role: "img",
                "aria-label": "Increase Interval Number",
              },
              decrementIcon: {
                role: "img",
                "aria-label": "Decrease Interval Number",
              },
            }}
          />
        </div>
      </div>
      <div className="flex ml-2 mb-2">
        <div style={{ width: layoutProps.labelWidth }}>
          <label htmlFor="intervalType">Interval Type</label>
        </div>
        <div style={{ width: layoutProps.valueWidth }}>
          <datalist id={`selectIntervalTypeDropdown`} aria-hidden="true">
            {typeOptions.map((intervalType: string) => (
              <option key={intervalType} value={intervalType} />
            ))}
          </datalist>
          <Dropdown
            id="intervalType"
            options={typeOptions || []}
            value={intervalType}
            onChange={(e) => setIntervalType(e.value)}
            pt={{
              dropdownIcon: {
                role: "img",
                "aria-label": `Interval Type Select Icon`,
              },
              input: {
                autoComplete: "off",
              },
              select: {
                autoComplete: "off",
                "aria-controls": `selectIntervalTypeDropdown`,
                "aria-label": ` Select Interval Type for Dropdown Select`,
              },
            }}
          />
        </div>
      </div>
      <div className="flex ml-2 mb-2">
        <div style={{ width: layoutProps.labelWidth }}>
          <label htmlFor="startDate">Start Date</label>
        </div>
        <div style={{ width: layoutProps.valueWidth }}>
          <Calendar
            id="startDate"
            value={startDate}
            showTime
            hourFormat="24"
            onChange={(e: any) => setStartDate(e.value)}
            tooltip={`Scheduler Start Date`}
            pt={{
              input: {
                root: ({ context }: { context: any }) => {
                  if (!context.disabled) {
                    return {
                      "aria-label": `Scheduler Start Date`,
                      "aria-controls": undefined,
                      "aria-description":
                        "Select Date and Time, aria-controls removed when popup is not in DOM",
                    };
                  }
                  return {
                    "aria-label": `Scheduler Start Date`,
                    "aria-description": "Select Date and Time",
                  };
                },
              },
            }}
          />
        </div>
      </div>
      <div className="flex ml-2 mb-2">
        <div style={{ width: layoutProps.labelWidth }}>
          <label htmlFor="endDate">End Date</label>
        </div>
        <div style={{ width: layoutProps.valueWidth }}>
          <Calendar
            id="endDate"
            value={endDate}
            showTime
            hourFormat="24"
            onChange={(e: any) => setEndDate(e.value)}
            tooltip={`Scheduler End Date`}
            pt={{
              input: {
                root: ({ context }: { context: any }) => {
                  if (!context.disabled) {
                    return {
                      "aria-label": `Scheduler End Date`,
                      "aria-controls": undefined,
                      "aria-description":
                        "Select Date and Time, aria-controls removed when popup is not in DOM",
                    };
                  }
                  return {
                    "aria-label": `Scheduler End Date`,
                    "aria-description": "Select Date and Time",
                  };
                },
              },
            }}
          />
        </div>
      </div>
      <div className="flex ml-2 mb-2">
        <div style={{ width: layoutProps.labelWidth }}>
          <label htmlFor="timezone">Timezone</label>
        </div>
        <div style={{ width: layoutProps.valueWidth }}>
          <InputText
            id="timezone"
            value={intervalTrigger?.timezone}
            onChange={(e) => {
              setIntervalTrigger({
                ...intervalTrigger,
                ...{ timezone: e.target.value },
              });
            }}
            pt={{
              root: {
                autoComplete: "off",
              },
            }}
          />
        </div>
      </div>
    </div>
  );
}

function CronForm({
  cronTrigger,
  setCronTrigger,
  layoutProps,
}: {
  cronTrigger: CronTrigger | null;
  setCronTrigger: (trigger: CronTrigger) => void;
  layoutProps: LayoutProps;
}) {
  const defaultCronValue =
    (cronTrigger?.minute ? cronTrigger.minute : "*") +
    " " +
    (cronTrigger?.hour ? cronTrigger.hour : "*") +
    " " +
    (cronTrigger?.day ? cronTrigger.day : "*") +
    " " +
    (cronTrigger?.month ? cronTrigger.month : "*") +
    " " +
    (cronTrigger?.dayOfWeek ? cronTrigger.dayOfWeek : "*") +
    " ";

  const [cronValue, setCronValue] = useState(defaultCronValue);
  const [startDate, setStartDate] = useState(
    typeof cronTrigger?.startDate === "string"
      ? new Date(cronTrigger.startDate)
      : cronTrigger?.startDate,
  );
  const [endDate, setEndDate] = useState(
    typeof cronTrigger?.endDate === "string"
      ? new Date(cronTrigger.endDate)
      : cronTrigger?.endDate,
  );

  useEffect(() => {
    let updateNeeded = false;
    let updates = {};
    const cronValues = cronValue.trim().split(/\s+/);

    if (!cronTrigger) {
      updateNeeded = true;
      updates = {
        endDate: endDate,
        startDate: startDate,
        minute: cronValues[0],
        hour: cronValues[1],
        day: cronValues[2],
        month: cronValues[3],
        dayOfWeek: cronValues[4],
      };
    } else {
      if (cronTrigger?.endDate !== endDate) {
        updateNeeded = true;
        updates = { ...updates, ...{ endDate: endDate } };
      }

      if (cronTrigger?.startDate !== startDate) {
        updateNeeded = true;
        updates = { ...updates, ...{ startDate: startDate } };
      }

      if (cronTrigger?.minute !== cronValues[0]) {
        updateNeeded = true;
        updates = { ...updates, ...{ minute: cronValues[0] } };
      }

      if (cronTrigger?.hour !== cronValues[1]) {
        updateNeeded = true;
        updates = { ...updates, ...{ hour: cronValues[1] } };
      }

      if (cronTrigger?.day !== cronValues[2]) {
        updateNeeded = true;
        updates = { ...updates, ...{ day: cronValues[2] } };
      }

      if (cronTrigger?.month !== cronValues[3]) {
        updateNeeded = true;
        updates = { ...updates, ...{ month: cronValues[3] } };
      }

      if (cronTrigger?.dayOfWeek !== cronValues[4]) {
        updateNeeded = true;
        updates = { ...updates, ...{ dayOfWeek: cronValues[4] } };
      }
    }

    if (updateNeeded) {
      setCronTrigger({ ...cronTrigger, ...updates });
    }
  }, [cronValue, endDate, startDate, cronTrigger, setCronTrigger]);

  return (
    <div>
      <div className="flex ml-2 mb-2">
        <div style={{ width: layoutProps.labelWidth }}>
          <label htmlFor="cron">CRON</label>
        </div>
        <div id="cron" style={{ width: layoutProps.valueWidth }}>
          <Cron
            value={cronValue}
            setValue={setCronValue}
            clockFormat="24-hour-clock"
          />
        </div>
      </div>

      <div className="flex ml-2 mb-2">
        <div style={{ width: layoutProps.labelWidth }}>
          <label htmlFor="cronJitter">CRON Jitter</label>
        </div>
        <div style={{ width: layoutProps.valueWidth }}>
          <InputNumber
            id="cronJitter"
            value={cronTrigger?.jitter}
            onValueChange={(e) => {
              setCronTrigger({ ...cronTrigger, ...{ jitter: e.target.value } });
            }}
            min={0}
            incrementButtonIcon="pi pi-chevron-up"
            decrementButtonIcon="pi pi-chevron-down"
            pt={{
              input: {
                root: {
                  "aria-label": `CRON Jitter`,
                  autoComplete: "off",
                },
              },
              incrementButton: {
                tabIndex: 0,
                "aria-label": `Increase CRON Jitter by 1`,
                "aria-hidden": "false",
              },

              decrementButton: {
                tabIndex: 0,
                "aria-label": `Decrease CRON Jitter by 1`,
                "aria-hidden": "false",
              },
              incrementIcon: {
                role: "img",
                "aria-label": "Increase CRON Jitter",
              },
              decrementIcon: {
                role: "img",
                "aria-label": "Decrease CRON Jitter",
              },
            }}
          />
        </div>
      </div>
      <div className="flex ml-2 mb-2">
        <div style={{ width: layoutProps.labelWidth }}>
          <label htmlFor="startDate">Start Date</label>
        </div>
        <div style={{ width: layoutProps.valueWidth }}>
          <Calendar
            id="startDate"
            value={startDate}
            showTime
            hourFormat="24"
            onChange={(e: any) => setStartDate(e.value)}
            pt={{
              input: {
                root: ({ context }: { context: any }) => {
                  if (!context.disabled) {
                    return {
                      "aria-label": `CRON Start Date`,
                      "aria-controls": undefined,
                      "aria-description":
                        "Select Date and Time, aria-controls removed when popup is not in DOM",
                    };
                  }
                  return {
                    "aria-label": `CRON Start Date`,
                    "aria-description": "Select Date and Time",
                  };
                },
              },
            }}
          />
        </div>
      </div>
      <div className="flex ml-2 mb-2">
        <div style={{ width: layoutProps.labelWidth }}>
          <label htmlFor="endDate">End Date</label>
        </div>
        <div style={{ width: layoutProps.valueWidth }}>
          <Calendar
            id="endDate"
            value={endDate}
            showTime
            hourFormat="24"
            onChange={(e: any) => setEndDate(e.value)}
            pt={{
              input: {
                root: ({ context }: { context: any }) => {
                  if (!context.disabled) {
                    return {
                      "aria-label": `CRON End Date`,
                      "aria-controls": undefined,
                      "aria-description":
                        "Select Date and Time, aria-controls removed when popup is not in DOM",
                    };
                  }
                  return {
                    "aria-label": `CRON End Date`,
                    "aria-description": "Select Date and Time",
                  };
                },
              },
            }}
          />
        </div>
      </div>
      <div className="flex ml-2 mb-2">
        <div style={{ width: layoutProps.labelWidth }}>
          <label htmlFor="timezone">Timezone</label>
        </div>
        <div style={{ width: layoutProps.valueWidth }}>
          <InputText
            id="timezone"
            value={cronTrigger?.timezone}
            onChange={(e) => {
              setCronTrigger({
                ...cronTrigger,
                ...{ timezone: e.target.value },
              });
            }}
            pt={{
              root: {
                autoComplete: "off",
              },
            }}
          />
        </div>
      </div>
    </div>
  );
}

function SchedulerForm({
  scheduledJob,
  setScheduledJob,
  setIsJobValid,
}: SchedulerFormProps) {
  const jobOptions = ["CRON", "Interval", "Date", "File"];
  let defaultJobOption = "CRON";
  const defaultTimeZone = "UTC";

  if (scheduledJob?.trigger_type === "interval") {
    defaultJobOption = "Interval";
  } else if (scheduledJob?.trigger_type === "date") {
    defaultJobOption = "Date";
  } else if (scheduledJob?.trigger_type === "file") {
    defaultJobOption = "File";
  }
  const [jobState, setJobState] = useState(defaultJobOption);

  const [cronTrigger, setCronTrigger] = useState(
    scheduledJob?.trigger_type === "cron"
      ? (scheduledJob?.trigger as CronTrigger)
      : { timezone: defaultTimeZone },
  );
  const [intervalTrigger, setIntervalTrigger] = useState(
    scheduledJob?.trigger_type === "interval"
      ? (scheduledJob?.trigger as IntervalTrigger)
      : { hours: 1, timezone: defaultTimeZone },
  );
  const [dateTrigger, setDateTrigger] = useState(
    scheduledJob?.trigger_type === "date"
      ? (scheduledJob?.trigger as DateTrigger)
      : { timezone: defaultTimeZone },
  );
  const [fileTrigger, setFileTrigger] = useState(
    scheduledJob?.trigger_type === "file"
      ? (scheduledJob?.trigger as FileTrigger)
      : { pattern: ".*" },
  );

  useEffect(() => {
    const validateForm = () => {
      let valid = true;
      if (
        scheduledJob?.name === undefined ||
        scheduledJob?.name === null ||
        scheduledJob?.name === ""
      ) {
        valid = false;
      }
      if (
        jobState === "Date" &&
        (dateTrigger?.run_date === undefined ||
          dateTrigger?.run_date === null ||
          dateTrigger?.run_date === "")
      ) {
        valid = false;
      }
      if (
        jobState === "File" &&
        (fileTrigger?.path === undefined ||
          fileTrigger?.path === null ||
          fileTrigger?.path === "")
      ) {
        valid = false;
      }
      setIsJobValid(valid);
    };
    validateForm();

    if (scheduledJob === undefined) {
      setScheduledJob({
        max_instances: 3,
        misfire_grace_time: 5,
        coalesce: true,
      });
      return;
    }
    if (jobState === "Date") {
      if (!CompareObjects(scheduledJob?.trigger, dateTrigger)) {
        setScheduledJob({
          ...scheduledJob,
          ...{ trigger_type: "date", trigger: dateTrigger },
        });
      }
    } else if (jobState === "Interval") {
      if (!CompareObjects(scheduledJob?.trigger, intervalTrigger)) {
        setScheduledJob({
          ...scheduledJob,
          ...{ trigger_type: "interval", trigger: intervalTrigger },
        });
      }
    } else if (jobState === "File") {
      if (!CompareObjects(scheduledJob?.trigger, fileTrigger)) {
        setScheduledJob({
          ...scheduledJob,
          ...{ trigger_type: "file", trigger: fileTrigger },
        });
      }
    } else if (jobState === "CRON") {
      if (!CompareObjects(scheduledJob?.trigger, cronTrigger)) {
        setScheduledJob({
          ...scheduledJob,
          ...{ trigger_type: "cron", trigger: cronTrigger },
        });
      }
    }
  }, [
    jobState,
    dateTrigger,
    intervalTrigger,
    fileTrigger,
    cronTrigger,
    scheduledJob,
    setScheduledJob,
  ]);

  const layoutProps = {
    valueWidth: "70%",
    labelWidth: "30%",
  } as LayoutProps;

  return (
    <Box>
      <Box sx={{ justifyContent: "center", mb: 4, display: "flex" }}>
        <ButtonGroup variant="contained" aria-label="">
          {jobOptions.map((option) => (
            <Button
              onClick={() => setJobState(option)}
              aria-label={`Change Job Type ${option}`}
            >
              <Typography>{option}</Typography>
            </Button>
          ))}
        </ButtonGroup>
      </Box>

      <div className="card flex justify-content-center ">
        <div>
          <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
            <FormLabel
              htmlFor="jobName"
              sx={{
                minWidth: "100px",
                textAlign: "right",
                color: "text.primary",
              }}
            >
              Job Name
            </FormLabel>
            <TextField
              id="jobName"
              value={scheduledJob?.name ?? ""}
              onChange={(e: ChangeEvent<HTMLInputElement>) => {
                setScheduledJob({
                  ...scheduledJob,
                  ...{ name: e.target.value },
                });
              }}
              sx={{ ml: 2, mb: 2 }}
              placeholder="Enter Job Name"
            />
          </Box>

          <div className="flex ml-2 mb-2">
            <div style={{ width: layoutProps.labelWidth }}>
              <label htmlFor="coalesce">Coalesce</label>
            </div>
            <div style={{ width: layoutProps.valueWidth }}>
              <Checkbox
                id="coalesce"
                onChange={(e) => {
                  setScheduledJob({
                    ...scheduledJob,
                    ...{ coalesce: e.checked },
                  });
                }}
                checked={scheduledJob?.coalesce === true}
                pt={{
                  input: {
                    "aria-label": `Coalesce Requests Checkbox`,
                  },
                  icon: {
                    role: "img",
                    "aria-label": "Selection for Coalesce Requests Checkbox",
                  },
                }}
              ></Checkbox>
            </div>
          </div>
          <div className="flex ml-2 mb-2">
            <Box sx={{ width: layoutProps.labelWidth }}>
              <label htmlFor="misfireGraceTime">Misfire Grace Time</label>
            </Box>
            <div style={{ width: layoutProps.valueWidth }}>
              <InputNumber
                id="misfireGraceTime"
                value={scheduledJob?.misfire_grace_time}
                onValueChange={(e) => {
                  setScheduledJob({
                    ...scheduledJob,
                    ...{ misfire_grace_time: e.value },
                  });
                }}
                showButtons
                min={0}
                incrementButtonIcon="pi pi-chevron-up"
                decrementButtonIcon="pi pi-chevron-down"
                pt={{
                  input: {
                    root: {
                      "aria-label": `Misfire Grace Time`,
                      autoComplete: "off",
                    },
                  },
                  incrementButton: {
                    tabIndex: 0,
                    "aria-label": `Increase Misfire Grace Time by 1`,
                    "aria-hidden": "false",
                  },

                  decrementButton: {
                    tabIndex: 0,
                    "aria-label": `Decrease Misfire Grace Time by 1`,
                    "aria-hidden": "false",
                  },
                  incrementIcon: {
                    role: "img",
                    "aria-label": "Increase Misfire Grace Time",
                  },
                  decrementIcon: {
                    role: "img",
                    "aria-label": "Decrease Misfire Grace Time",
                  },
                }}
              />
            </div>
          </div>
          <div className="flex ml-2 mb-2">
            <div style={{ width: layoutProps.labelWidth }}>
              <label htmlFor="maxInstances">Max Instances</label>
            </div>
            <div style={{ width: layoutProps.valueWidth }}>
              <InputNumber
                id="maxInstances"
                value={scheduledJob?.max_instances}
                onValueChange={(e) => {
                  setScheduledJob({
                    ...scheduledJob,
                    ...{ max_instances: e.value },
                  });
                }}
                showButtons
                min={1}
                incrementButtonIcon="pi pi-chevron-up"
                decrementButtonIcon="pi pi-chevron-down"
                pt={{
                  input: {
                    root: {
                      "aria-label": `Max Instances`,
                      autoComplete: "off",
                    },
                  },
                  incrementButton: {
                    tabIndex: 0,
                    "aria-label": `Increase Max Instances by 1`,
                    "aria-hidden": "false",
                  },
                  decrementButton: {
                    tabIndex: 0,
                    "aria-label": `Decrease Max Instances by 1`,
                    "aria-hidden": "false",
                  },
                }}
              />
            </div>
          </div>
          <div className="flex ml-2 mb-2">
            <div style={{ width: layoutProps.labelWidth }}>
              <label htmlFor="timeout">Timeout</label>
            </div>
            <div style={{ width: layoutProps.valueWidth }}>
              <InputNumber
                id="timeout"
                value={scheduledJob?.timeout}
                onValueChange={(e) => {
                  setScheduledJob({ ...scheduledJob, ...{ timeout: e.value } });
                }}
                showButtons
                min={0}
                incrementButtonIcon="pi pi-chevron-up"
                decrementButtonIcon="pi pi-chevron-down"
                pt={{
                  input: {
                    root: {
                      "aria-label": `Timeout`,
                      autoComplete: "off",
                      "aria-valuenow": scheduledJob?.timeout ?? undefined,
                    },
                  },
                  incrementButton: {
                    tabIndex: 0,
                    "aria-label": `Increase Timeout by 1`,
                    "aria-hidden": "false",
                  },
                  decrementButton: {
                    tabIndex: 0,
                    "aria-label": `Decrease Timeout by 1`,
                    "aria-hidden": "false",
                  },
                  incrementIcon: {
                    role: "img",
                    "aria-label": "Increase Timeout",
                  },
                  decrementIcon: {
                    role: "img",
                    "aria-label": "Decrease Timeout",
                  },
                }}
              />
            </div>
          </div>
        </div>
        <div>
          {jobState === "CRON" && (
            <CronForm
              cronTrigger={cronTrigger}
              setCronTrigger={setCronTrigger}
              layoutProps={layoutProps}
            />
          )}
          {jobState === "Interval" && (
            <IntervalForm
              intervalTrigger={intervalTrigger}
              setIntervalTrigger={setIntervalTrigger}
              layoutProps={layoutProps}
            />
          )}
          {jobState === "Date" && (
            <DateForm
              dateTrigger={dateTrigger}
              setDateTrigger={setDateTrigger}
              layoutProps={layoutProps}
            />
          )}
          {jobState === "File" && (
            <FileForm
              fileTrigger={fileTrigger}
              setFileTrigger={setFileTrigger}
              layoutProps={layoutProps}
            />
          )}
        </div>
      </div>
    </Box>
  );
}
export default SchedulerForm;
