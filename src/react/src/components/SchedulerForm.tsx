import { Calendar } from "primereact/calendar";
import { Checkbox } from "primereact/checkbox";
import { Dropdown } from "primereact/dropdown";
import { InputNumber } from "primereact/inputnumber";
import { InputText } from "primereact/inputtext";
import { MultiSelect } from "primereact/multiselect";
import { SelectButton } from "primereact/selectbutton";
import { useEffect, useState } from "react";
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
  scheduledJob: Job | null;
  setScheduledJob: (job: Job) => void;
  runState: string;
  setRunState: (value: string) => void;
  runOptions: Array<string>;
}

function FileForm({
  fileTrigger,
  setFileTrigger,
}: {
  fileTrigger: FileTrigger | null;
  setFileTrigger: (trigger: FileTrigger) => void;
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
      <div className="p-field">
        <label className="ml-2">Path</label>
        <InputText
          value={fileTrigger?.path}
          onChange={(e) => {
            setFileTrigger({ ...fileTrigger, ...{ path: e.target.value } });
          }}
        />
      </div>
      <div className="p-field">
        <label className="ml-2">Pattern</label>
        <InputText
          value={fileTrigger?.pattern}
          onChange={(e) => {
            setFileTrigger({ ...fileTrigger, ...{ pattern: e.target.value } });
          }}
        />
      </div>
      <div className="p-field">
        <label className="ml-2">Recursive</label>
        <Checkbox
          onChange={(e) => {
            setFileTrigger({
              ...fileTrigger,
              ...{ recursive: e.target.value },
            });
          }}
          checked={fileTrigger?.recursive === true}
        ></Checkbox>
      </div>
      <div className="p-field">
        <label className="ml-2">Event Type</label>
        <MultiSelect
          value={selectedTypes}
          onChange={(e) => setSelectedTypes(e.value)}
          options={typeOptions}
          placeholder="Select Event Type"
        />
      </div>
    </div>
  );
}

function DateForm({
  dateTrigger,
  setDateTrigger,
}: {
  dateTrigger: DateTrigger | null;
  setDateTrigger: (trigger: DateTrigger) => void;
}) {
  const [runDate, setRunDate] = useState(
    typeof dateTrigger?.runDate === "string"
      ? new Date(dateTrigger.runDate)
      : dateTrigger?.runDate,
  );

  useEffect(() => {
    if (!dateTrigger || dateTrigger.runDate !== runDate) {
      setDateTrigger({ ...dateTrigger, ...{ runDate: runDate } });
    }
  }, [runDate, dateTrigger, setDateTrigger]);

  return (
    <div>
      <div className="p-field">
        <label className="ml-2">Run Date</label>
        <Calendar
          value={runDate}
          showTime
          hourFormat="24"
          onChange={(e: any) => setRunDate(e.value)}
        />
      </div>
      <div className="p-field">
        <label className="ml-2">Timezone</label>
        <InputText
          value={dateTrigger?.timezone}
          onChange={(e) => {
            setDateTrigger({ ...dateTrigger, ...{ timezone: e.target.value } });
          }}
        />
      </div>
    </div>
  );
}

function IntervalForm({
  intervalTrigger,
  setIntervalTrigger,
}: {
  intervalTrigger: IntervalTrigger | null;
  setIntervalTrigger: (trigger: IntervalTrigger) => void;
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
      <div className="p-field">
        <label>Interval Number</label>
        <InputNumber
          value={intervalNumber}
          onChange={(e) => setIntervalNumber(e.value)}
          min={1}
        />
      </div>
      <div className="p-field">
        <label>Interval Type</label>
        <Dropdown
          options={typeOptions || []}
          value={intervalType}
          onChange={(e) => setIntervalType(e.value)}
        />
      </div>
      <div className="p-field">
        <label className="ml-2">Start Date</label>
        <Calendar
          value={startDate}
          showTime
          hourFormat="24"
          onChange={(e: any) => setStartDate(e.value)}
        />
      </div>
      <div className="p-field">
        <label className="ml-2">End Date</label>
        <Calendar
          value={endDate}
          showTime
          hourFormat="24"
          onChange={(e: any) => setEndDate(e.value)}
        />
      </div>
      <div className="p-field">
        <label className="ml-2">Timezone</label>
        <InputText
          value={intervalTrigger?.timezone}
          onChange={(e) => {
            setIntervalTrigger({
              ...intervalTrigger,
              ...{ timezone: e.target.value },
            });
          }}
        />
      </div>
    </div>
  );
}

function CronForm({
  cronTrigger,
  setCronTrigger,
}: {
  cronTrigger: CronTrigger | null;
  setCronTrigger: (trigger: CronTrigger) => void;
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
      <div className="p-field">
        <Cron
          value={cronValue}
          setValue={setCronValue}
          clockFormat="24-hour-clock"
        />
      </div>

      <div className="p-field">
        <label className="ml-2">CRON Jitter</label>
        <InputNumber
          value={cronTrigger?.jitter}
          onValueChange={(e) => {
            setCronTrigger({ ...cronTrigger, ...{ jitter: e.target.value } });
          }}
          min={0}
        />
      </div>
      <div className="p-field">
        <label className="ml-2">Start Date</label>
        <Calendar
          value={startDate}
          showTime
          hourFormat="24"
          onChange={(e: any) => setStartDate(e.value)}
        />
      </div>
      <div className="p-field">
        <label className="ml-2">End Date</label>
        <Calendar
          value={endDate}
          showTime
          hourFormat="24"
          onChange={(e: any) => setEndDate(e.value)}
        />
      </div>
      <div className="p-field">
        <label className="ml-2">Timezone</label>
        <InputText
          value={cronTrigger?.timezone}
          onChange={(e) => {
            setCronTrigger({ ...cronTrigger, ...{ timezone: e.target.value } });
          }}
        />
      </div>
    </div>
  );
}

function SchedulerForm({
  scheduledJob,
  setScheduledJob,
  runState,
  setRunState,
  runOptions,
}: SchedulerFormProps) {
  const jobOptions = ["CRON", "Interval", "Date", "File"];
  let defaultJobOption = "CRON";

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
      : {},
  );
  const [intervalTrigger, setIntervalTrigger] = useState(
    scheduledJob?.trigger_type === "interval"
      ? (scheduledJob?.trigger as IntervalTrigger)
      : {},
  );
  const [dateTrigger, setDateTrigger] = useState(
    scheduledJob?.trigger_type === "date"
      ? (scheduledJob?.trigger as DateTrigger)
      : {},
  );
  const [fileTrigger, setFileTrigger] = useState(
    scheduledJob?.trigger_type === "file"
      ? (scheduledJob?.trigger as FileTrigger)
      : {},
  );

  useEffect(() => {
    if (jobState === "Date") {
      if (!CompareObjects(scheduledJob?.trigger, dateTrigger)) {
        setScheduledJob({ ...scheduledJob, ...{ trigger: dateTrigger } });
      }
    } else if (jobState === "Interval") {
      if (!CompareObjects(scheduledJob?.trigger, intervalTrigger)) {
        setScheduledJob({ ...scheduledJob, ...{ trigger: intervalTrigger } });
      }
    } else if (jobState === "File") {
      if (!CompareObjects(scheduledJob?.trigger, fileTrigger)) {
        setScheduledJob({ ...scheduledJob, ...{ trigger: fileTrigger } });
      }
    } else if (jobState === "CRON") {
      if (!CompareObjects(scheduledJob?.trigger, cronTrigger)) {
        setScheduledJob({ ...scheduledJob, ...{ trigger: cronTrigger } });
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

  return (
    <div>
      <div className="card flex justify-content-center">
        <SelectButton
          value={runState}
          onChange={(e) => e.value && setRunState(e.value)}
          options={runOptions}
        />
      </div>
      {runState === runOptions[1] && (
        <div className="card flex flex-column align-items-center gap-3 ">
          <div className="p-field">
            <label className="ml-2">Job Name</label>
            <InputText
              value={scheduledJob?.name}
              onChange={(e) => {
                setScheduledJob({
                  ...scheduledJob,
                  ...{ name: e.target.value },
                });
              }}
            />
          </div>

          <div className="p-field">
            <label className="ml-2">Coalesce</label>
            <Checkbox
              onChange={(e) => {
                setScheduledJob({ ...scheduledJob, ...{ coalesce: e.value } });
              }}
              checked={scheduledJob?.coalesce === true}
            ></Checkbox>
          </div>
          <div className="p-field">
            <label className="ml-2">Misfire Grace Time</label>
            <InputNumber
              value={scheduledJob?.misfire_grace_time}
              onValueChange={(e) => {
                setScheduledJob({
                  ...scheduledJob,
                  ...{ misfire_grace_time: e.value },
                });
              }}
              showButtons
              min={0}
            />
          </div>
          <div className="p-field">
            <label className="ml-2">Max Instances</label>
            <InputNumber
              value={scheduledJob?.max_instances}
              onValueChange={(e) => {
                setScheduledJob({
                  ...scheduledJob,
                  ...{ max_instances: e.value },
                });
              }}
              showButtons
              min={1}
            />
          </div>
          <div className="p-field">
            <label className="ml-2">Timeout</label>
            <InputNumber
              value={scheduledJob?.timeout}
              onValueChange={(e) => {
                setScheduledJob({ ...scheduledJob, ...{ timeout: e.value } });
              }}
              showButtons
              min={0}
            />
          </div>
          <div className="p-field">
            <SelectButton
              value={jobState}
              onChange={(e) => e.value && setJobState(e.value)}
              options={jobOptions}
            />
          </div>
          {jobState === "CRON" && (
            <CronForm
              cronTrigger={cronTrigger}
              setCronTrigger={setCronTrigger}
            />
          )}
          {jobState === "Interval" && (
            <IntervalForm
              intervalTrigger={intervalTrigger}
              setIntervalTrigger={setIntervalTrigger}
            />
          )}
          {jobState === "Date" && (
            <DateForm
              dateTrigger={dateTrigger}
              setDateTrigger={setDateTrigger}
            />
          )}
          {jobState === "File" && (
            <FileForm
              fileTrigger={fileTrigger}
              setFileTrigger={setFileTrigger}
            />
          )}
        </div>
      )}
    </div>
  );
}
export default SchedulerForm;
