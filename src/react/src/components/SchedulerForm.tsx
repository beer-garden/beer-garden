import "react-js-cron/dist/styles.css";

import {
  Box,
  Button,
  ButtonGroup,
  Checkbox,
  FormControlLabel,
  FormLabel,
  MenuItem,
  OutlinedInput,
  Select,
  SelectChangeEvent,
  TextField,
  Typography,
} from "@mui/material";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import { DateTimePicker } from "@mui/x-date-pickers/DateTimePicker";
import { PickerValue } from "@mui/x-date-pickers/internals";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { Dayjs } from "dayjs";
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
import NumberField from "./EnhancedTable/components/NumberField";

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
    <Box>
      <Box sx={{ display: "flex", ml: 2, mb: 2, alignItems: "center" }}>
        <Box sx={{ width: layoutProps.labelWidth }}>
          <FormLabel
            htmlFor="path"
            sx={{
              minWidth: "100px",
              textAlign: "right",
              fontWeight: "bold",
            }}
          >
            Path
          </FormLabel>
        </Box>
        <Box sx={{ width: layoutProps.valueWidth }}>
          <TextField
            id="path"
            fullWidth
            size="small"
            value={fileTrigger?.path ?? ""}
            onChange={(e) => {
              setFileTrigger({ ...fileTrigger, ...{ path: e.target.value } });
            }}
            error={
              fileTrigger?.path === undefined ||
              fileTrigger?.path === null ||
              fileTrigger?.path === ""
            }
            autoComplete="off"
          />
        </Box>
      </Box>
      <Box sx={{ display: "flex", ml: 2, mb: 2, alignItems: "center" }}>
        <Box sx={{ width: layoutProps.labelWidth }}>
          <FormLabel
            htmlFor="pattern"
            sx={{
              minWidth: "100px",
              textAlign: "right",
              fontWeight: "bold",
            }}
          >
            Pattern
          </FormLabel>
        </Box>
        <Box sx={{ width: layoutProps.valueWidth }}>
          <TextField
            id="pattern"
            fullWidth
            size="small"
            value={fileTrigger?.pattern ?? ""}
            onChange={(e) => {
              setFileTrigger({
                ...fileTrigger,
                ...{ pattern: e.target.value },
              });
            }}
            autoComplete="off"
          />
        </Box>
      </Box>
      <Box sx={{ display: "flex", ml: 2, mb: 2, alignItems: "center" }}>
        <Box sx={{ width: layoutProps.labelWidth }}>
          <FormLabel
            htmlFor="recursive"
            sx={{
              minWidth: "100px",
              textAlign: "right",
              fontWeight: "bold",
            }}
          >
            Recursive
          </FormLabel>
        </Box>
        <Box sx={{ width: layoutProps.valueWidth }}>
          <FormControlLabel
            control={
              <Checkbox
                id="recursive"
                onChange={(e) => {
                  setFileTrigger({
                    ...fileTrigger,
                    ...{ recursive: e.target.checked },
                  });
                }}
                checked={fileTrigger?.recursive === true}
              />
            }
            label=""
          />
        </Box>
      </Box>
      <Box sx={{ display: "flex", ml: 2, mb: 2, alignItems: "center" }}>
        <Box sx={{ width: layoutProps.labelWidth }}>
          <FormLabel
            htmlFor="eventTypes"
            sx={{
              minWidth: "100px",
              textAlign: "right",
              fontWeight: "bold",
            }}
          >
            Event Types
          </FormLabel>
        </Box>
        <Box sx={{ width: layoutProps.valueWidth }}>
          <Select
            id="eventTypes"
            multiple
            value={selectedTypes}
            onChange={(event: SelectChangeEvent<typeof typeOptions | null>) => {
              const {
                target: { value },
              } = event;

              if (value === null) {
                setSelectedTypes([]);
              } else {
                setSelectedTypes(
                  typeof value === "string" ? value.split(",") : value,
                );
              }
            }}
            input={<OutlinedInput label="Select Event Type" />}
            renderValue={(selected) =>
              selected === null ? "" : selected.join(", ")
            }
            size="small"
            fullWidth
          >
            {typeOptions.map((option) => (
              <MenuItem key={option} value={option}>
                {option}
              </MenuItem>
            ))}
          </Select>
        </Box>
      </Box>
    </Box>
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
    <Box>
      <Box sx={{ display: "flex", ml: 2, mb: 2, alignItems: "center" }}>
        <Box sx={{ width: layoutProps.labelWidth }}>
          <FormLabel
            htmlFor="runDate"
            sx={{
              minWidth: "100px",
              textAlign: "right",
              fontWeight: "bold",
            }}
          >
            Run Date
          </FormLabel>
        </Box>
        <Box sx={{ width: layoutProps.valueWidth }}>
          <LocalizationProvider dateAdapter={AdapterDayjs}>
            <DateTimePicker
              value={runDate as Dayjs}
              onChange={(newValue: PickerValue) => {
                if (newValue && newValue.isValid()) {
                  updateRunDate(newValue);
                } else {
                  updateRunDate(undefined);
                }
              }}
              slotProps={{
                textField: {
                  id: "runDate",
                },
              }}
            />
          </LocalizationProvider>
        </Box>
      </Box>
      <Box sx={{ display: "flex", ml: 2, mb: 2, alignItems: "center" }}>
        <Box sx={{ width: layoutProps.labelWidth }}>
          <FormLabel
            htmlFor="timezone"
            sx={{
              minWidth: "100px",
              textAlign: "right",
              fontWeight: "bold",
            }}
          >
            Timezone
          </FormLabel>
        </Box>
        <Box sx={{ width: layoutProps.valueWidth }}>
          <TextField
            id="timezone"
            fullWidth
            size="small"
            value={dateTrigger?.timezone ?? ""}
            onChange={(e) => {
              setDateTrigger({
                ...dateTrigger,
                ...{ timezone: e.target.value },
              });
            }}
            autoComplete="off"
          />
        </Box>
      </Box>
    </Box>
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
    <Box>
      <Box sx={{ display: "flex", ml: 2, mb: 2, alignItems: "center" }}>
        <Box sx={{ width: layoutProps.labelWidth }}>
          <FormLabel
            htmlFor="intervalNumber"
            sx={{
              minWidth: "100px",
              textAlign: "right",
              fontWeight: "bold",
            }}
          >
            Interval Number
          </FormLabel>
        </Box>
        <Box sx={{ width: layoutProps.valueWidth }}>
          <NumberField
            id="intervalNumber"
            value={intervalNumber}
            onValueChange={(value: number | null) => setIntervalNumber(value)}
            min={1}
            size="small"
          />
        </Box>
      </Box>
      <Box sx={{ display: "flex", ml: 2, mb: 2, alignItems: "center" }}>
        <Box sx={{ width: layoutProps.labelWidth }}>
          <FormLabel
            htmlFor="intervalType"
            sx={{
              minWidth: "100px",
              textAlign: "right",
              fontWeight: "bold",
            }}
          >
            Interval Type
          </FormLabel>
        </Box>
        <Box sx={{ width: layoutProps.valueWidth }}>
          <Select
            id="intervalType"
            value={intervalType}
            onChange={(event: SelectChangeEvent<string | null>) => {
              setIntervalType(event.target.value);
            }}
            size="small"
            fullWidth
          >
            {typeOptions.map((option) => (
              <MenuItem key={option} value={option}>
                {option}
              </MenuItem>
            ))}
          </Select>
        </Box>
      </Box>
      <Box sx={{ display: "flex", ml: 2, mb: 2, alignItems: "center" }}>
        <Box sx={{ width: layoutProps.labelWidth }}>
          <FormLabel
            htmlFor="startDate"
            sx={{
              minWidth: "100px",
              textAlign: "right",
              fontWeight: "bold",
            }}
          >
            Start Date
          </FormLabel>
        </Box>
        <Box sx={{ width: layoutProps.valueWidth }}>
          <LocalizationProvider dateAdapter={AdapterDayjs}>
            <DateTimePicker
              value={startDate as Dayjs}
              onChange={(newValue: PickerValue) => {
                if (newValue && newValue.isValid()) {
                  setStartDate(newValue);
                } else {
                  setStartDate(undefined);
                }
              }}
              slotProps={{
                textField: {
                  id: "startDate",
                },
              }}
            />
          </LocalizationProvider>
        </Box>
      </Box>
      <Box sx={{ display: "flex", ml: 2, mb: 2, alignItems: "center" }}>
        <Box sx={{ width: layoutProps.labelWidth }}>
          <FormLabel
            htmlFor="endDate"
            sx={{
              minWidth: "100px",
              textAlign: "right",
              fontWeight: "bold",
            }}
          >
            End Date
          </FormLabel>
        </Box>
        <Box sx={{ width: layoutProps.valueWidth }}>
          <LocalizationProvider dateAdapter={AdapterDayjs}>
            <DateTimePicker
              value={endDate as Dayjs}
              onChange={(newValue: PickerValue) => {
                if (newValue && newValue.isValid()) {
                  setEndDate(newValue);
                } else {
                  setEndDate(undefined);
                }
              }}
              slotProps={{
                textField: {
                  id: "endDate",
                },
              }}
            />
          </LocalizationProvider>
        </Box>
      </Box>
      <Box sx={{ display: "flex", ml: 2, mb: 2, alignItems: "center" }}>
        <Box sx={{ width: layoutProps.labelWidth }}>
          <FormLabel
            htmlFor="timezone"
            sx={{
              minWidth: "100px",
              textAlign: "right",
              fontWeight: "bold",
            }}
          >
            Timezone
          </FormLabel>
        </Box>
        <Box sx={{ width: layoutProps.valueWidth }}>
          <TextField
            id="timezone"
            fullWidth
            size="small"
            value={intervalTrigger?.timezone ?? ""}
            onChange={(e) => {
              setIntervalTrigger({
                ...intervalTrigger,
                ...{ timezone: e.target.value },
              });
            }}
            autoComplete="off"
          />
        </Box>
      </Box>
    </Box>
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
    <Box>
      <Box sx={{ display: "flex", ml: 2, mb: 2, alignItems: "center" }}>
        <Box sx={{ width: layoutProps.labelWidth }}>
          <FormLabel
            htmlFor="cron"
            sx={{
              minWidth: "100px",
              textAlign: "right",
              fontWeight: "bold",
            }}
          >
            CRON
          </FormLabel>
        </Box>
        <Box id="cron" sx={{ width: layoutProps.valueWidth }}>
          <Cron
            value={cronValue}
            setValue={setCronValue}
            clockFormat="24-hour-clock"
          />
        </Box>
      </Box>

      <Box sx={{ display: "flex", ml: 2, mb: 2, alignItems: "center" }}>
        <Box sx={{ width: layoutProps.labelWidth }}>
          <FormLabel
            htmlFor="cronJitter"
            sx={{
              minWidth: "100px",
              textAlign: "right",
              fontWeight: "bold",
            }}
          >
            CRON Jitter
          </FormLabel>
        </Box>
        <Box sx={{ width: layoutProps.valueWidth }}>
          <NumberField
            id="cronJitter"
            value={cronTrigger?.jitter}
            onValueChange={(value: number | null) => {
              setCronTrigger({ ...cronTrigger, ...{ jitter: value } });
            }}
            min={0}
            size="small"
          />
        </Box>
      </Box>
      <Box sx={{ display: "flex", ml: 2, mb: 2, alignItems: "center" }}>
        <Box sx={{ width: layoutProps.labelWidth }}>
          <FormLabel
            htmlFor="startDate"
            sx={{
              minWidth: "100px",
              textAlign: "right",
              fontWeight: "bold",
            }}
          >
            Start Date
          </FormLabel>
        </Box>
        <Box sx={{ width: layoutProps.valueWidth }}>
          <LocalizationProvider dateAdapter={AdapterDayjs}>
            <DateTimePicker
              value={startDate as Dayjs}
              onChange={(newValue: PickerValue) => {
                if (newValue && newValue.isValid()) {
                  setStartDate(newValue);
                } else {
                  setStartDate(undefined);
                }
              }}
              slotProps={{
                textField: {
                  id: "startDate",
                },
              }}
            />
          </LocalizationProvider>
        </Box>
      </Box>
      <Box sx={{ display: "flex", ml: 2, mb: 2, alignItems: "center" }}>
        <Box sx={{ width: layoutProps.labelWidth }}>
          <FormLabel
            htmlFor="endDate"
            sx={{
              minWidth: "100px",
              textAlign: "right",
              fontWeight: "bold",
            }}
          >
            End Date
          </FormLabel>
        </Box>
        <Box sx={{ width: layoutProps.valueWidth }}>
          <LocalizationProvider dateAdapter={AdapterDayjs}>
            <DateTimePicker
              value={endDate as Dayjs}
              onChange={(newValue: PickerValue) => {
                if (newValue && newValue.isValid()) {
                  setEndDate(newValue);
                } else {
                  setEndDate(undefined);
                }
              }}
              slotProps={{
                textField: {
                  id: "endDate",
                },
              }}
            />
          </LocalizationProvider>
        </Box>
      </Box>
      <Box sx={{ display: "flex", ml: 2, mb: 2, alignItems: "center" }}>
        <Box sx={{ width: layoutProps.labelWidth }}>
          <FormLabel
            htmlFor="timezone"
            sx={{
              minWidth: "100px",
              textAlign: "right",
              fontWeight: "bold",
            }}
          >
            Timezone
          </FormLabel>
        </Box>
        <Box sx={{ width: layoutProps.valueWidth }}>
          <TextField
            id="timezone"
            fullWidth
            size="small"
            value={cronTrigger?.timezone ?? ""}
            onChange={(e) => {
              setCronTrigger({
                ...cronTrigger,
                ...{ timezone: e.target.value },
              });
            }}
            autoComplete="off"
          />
        </Box>
      </Box>
    </Box>
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
              key={option}
              onClick={() => setJobState(option)}
              aria-label={`Change Job Type ${option}`}
            >
              <Typography>{option}</Typography>
            </Button>
          ))}
        </ButtonGroup>
      </Box>

      <Box sx={{ display: "flex", justifyContent: "center" }}>
        <Box>
          <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
            <FormLabel
              htmlFor="jobName"
              sx={{
                minWidth: "100px",
                textAlign: "right",
                fontWeight: "bold",
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
              size="small"
            />
          </Box>

          <Box sx={{ display: "flex", ml: 2, mb: 2, alignItems: "center" }}>
            <Box sx={{ width: layoutProps.labelWidth }}>
              <FormLabel
                htmlFor="coalesce"
                sx={{
                  minWidth: "100px",
                  textAlign: "right",
                  fontWeight: "bold",
                }}
              >
                Coalesce
              </FormLabel>
            </Box>
            <Box sx={{ width: layoutProps.valueWidth }}>
              <FormControlLabel
                control={
                  <Checkbox
                    id="coalesce"
                    onChange={(e) => {
                      setScheduledJob({
                        ...scheduledJob,
                        ...{ coalesce: e.target.checked },
                      });
                    }}
                    checked={scheduledJob?.coalesce === true}
                  />
                }
                label=""
              />
            </Box>
          </Box>
        </Box>
        <Box>
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
        </Box>
      </Box>
    </Box>
  );
}

export default SchedulerForm;
