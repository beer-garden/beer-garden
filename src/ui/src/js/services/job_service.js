jobService.$inject = ["$http", "NamespaceService"];

/**
 * jobService - Service for getting jobs from the API.
 * @param  {Object} $http             Angular's $http object.
 * @param  {Object} NamespaceService  Beer-Garden's namespace service.
 * @return {Object}                   Object for interacting with the job API.
 */
export default function jobService($http, NamespaceService) {
  let JobService = {};

  JobService.getJobs = function () {
    return $http.get("api/v1/jobs");
  };

  JobService.getJob = function (id) {
    return $http.get("api/v1/jobs/" + id);
  };

  JobService.exportJobs = function () {
    return $http.post("api/v1/export/jobs/");
  };

  JobService.importJobs = function (payload) {
    return $http.post("api/v1/import/jobs/", payload);
  };

  JobService.createJob = function (job) {
    if (job["id"] == null) {
      return $http.post("api/v1/jobs", job);
    }

    return JobService.updateJob(job);
  };

  JobService.deleteJob = function (id) {
    return $http.delete("api/v1/jobs/" + id);
  };

  JobService.patchJob = function (id, payload) {
    return $http.patch("api/v1/jobs/" + id, payload);
  };

  JobService.runAdHocJob = function (id, resetInterval) {
    // `resetInterval` ignored until API understands what to
    // do with it.
    return $http.post(`api/v1/jobs/${id}/execute`)
  };

  JobService.updateJob = function (job) {
    return JobService.patchJob(job["id"], {
      operations: [
        {
          operation: "update",
          path: "/job",
          value: job,
        },
      ],
    });
  };

  JobService.resumeJob = function (jobId) {
    return JobService.patchJob(jobId, {
      operations: [
        {
          operation: "update",
          path: "/status",
          value: "RUNNING",
        },
      ],
    });
  };

  JobService.pauseJob = function (jobId) {
    return JobService.patchJob(jobId, {
      operations: [
        {
          operation: "update",
          path: "/status",
          value: "PAUSED",
        },
      ],
    });
  };

  const getTrigger = function (triggerType, formModel) {
    if (triggerType === "date") {
      return {
        run_date: formModel["run_date"],
        timezone: formModel["date_timezone"],
      };
    } else if (triggerType === "interval") {
      let weeks = 0;
      let minutes = 0;
      let hours = 0;
      let seconds = 0;
      let days = 0;
      if (formModel["interval"] === "weeks") {
        weeks = formModel["interval_num"];
      } else if (formModel["interval"] === "minutes") {
        minutes = formModel["interval_num"];
      } else if (formModel["interval"] === "hours") {
        hours = formModel["interval_num"];
      } else if (formModel["interval"] === "seconds") {
        seconds = formModel["interval_num"];
      } else if (formModel["interval"] === "days") {
        days = formModel["interval_num"];
      }
      return {
        weeks: weeks,
        minutes: minutes,
        hours: hours,
        seconds: seconds,
        days: days,
        jitter: formModel["interval_jitter"],
        start_date: formModel["interval_start_date"],
        end_date: formModel["interval_end_date"],
        timezone: formModel["interval_timezone"],
        reschedule_on_finish: formModel["interval_reschedule_on_finish"],
      };
    } else if (triggerType === "file") {
      return {
        pattern: formModel["file_pattern"],
        path: formModel["file_path"],
        recursive: formModel["file_recursive"],
        callbacks: formModel["file_callbacks"],
      };
    } else {
      return {
        minute: formModel["minute"],
        hour: formModel["hour"],
        day: formModel["day"],
        month: formModel["month"],
        day_of_week: formModel["day_of_week"],
        year: formModel["year"],
        week: formModel["week"],
        second: formModel["second"],
        jitter: formModel["cron_jitter"],
        start_date: formModel["cron_start_date"],
        end_date: formModel["cron_end_date"],
        timezone: formModel["cron_timezone"],
      };
    }
  };

  JobService.serverModelToForm = function (job) {
    let formModel = {};

    formModel["name"] = job["name"];
    formModel["misfire_grace_time"] = job["misfire_grace_time"];
    formModel["trigger_type"] = job["trigger_type"];
    formModel["coalesce"] = job["coalesce"];
    formModel["max_instances"] = job["max_instances"];
    formModel["timeout"] = job["timeout"];
    formModel["id"] = job["id"] || null;

    if (job["trigger_type"] === "date") {
      formModel["run_date"] = job["trigger"]["run_date"];
      formModel["date_timezone"] = job["trigger"]["timezone"];
    } else if (job["trigger_type"] === "interval") {
      formModel["weeks"] = job["trigger"]["weeks"] || 0;
      formModel["minutes"] = job["trigger"]["minutes"] || 0;
      formModel["hours"] = job["trigger"]["hours"] || 0;
      formModel["seconds"] = job["trigger"]["seconds"] || 0;
      formModel["days"] = job["trigger"]["days"] || 0;

      if (job["trigger"]["weeks"] != 0) {
        formModel["interval"] = "weeks";
        formModel["interval_num"] = job["trigger"]["weeks"];
      } else if (job["trigger"]["minutes"] != 0) {
        formModel["interval"] = "minutes";
        formModel["interval_num"] = job["trigger"]["minutes"];
      } else if (job["trigger"]["hours"] != 0) {
        formModel["interval"] = "hours";
        formModel["interval_num"] = job["trigger"]["hours"];
      } else if (job["trigger"]["seconds"] != 0) {
        formModel["interval"] = "seconds";
        formModel["interval_num"] = job["trigger"]["seconds"];
      } else if (job["trigger"]["days"] != 0) {
        formModel["interval"] = "days";
        formModel["interval_num"] = job["trigger"]["days"];
      }

      formModel["interval_jitter"] = job["trigger"]["jitter"];
      formModel["interval_start_date"] = job["trigger"]["start_date"];
      formModel["interval_end_date"] = job["trigger"]["end_date"];
      formModel["interval_timezone"] = job["trigger"]["timezone"];
      formModel["interval_reschedule_on_finish"] =
        job["trigger"]["reschedule_on_finish"];
    } else if (job["trigger_type"] === "file") {
      formModel["file_pattern"] = job["trigger"]["pattern"];
      formModel["file_path"] = job["trigger"]["path"];
      formModel["file_recursive"] = job["trigger"]["recursive"];
      formModel["file_callbacks"] = job["trigger"]["callbacks"];
    } else {
      formModel["minute"] = job["trigger"]["minute"];
      formModel["hour"] = job["trigger"]["hour"];
      formModel["day"] = job["trigger"]["day"];
      formModel["month"] = job["trigger"]["month"];
      formModel["day_of_week"] = job["trigger"]["day_of_week"];
      formModel["year"] = job["trigger"]["year"];
      formModel["week"] = job["trigger"]["week"];
      formModel["second"] = job["trigger"]["second"];
      formModel["cron_jitter"] = job["trigger"]["jitter"];
      formModel["cron_start_date"] = job["trigger"]["start_date"];
      formModel["cron_end_date"] = job["trigger"]["end_date"];
      formModel["cron_timezone"] = job["trigger"]["timezone"];
    }

    return formModel;
  };

  JobService.formToServerModel = function (formModel, requestTemplate) {
    let serviceModel = {};
    serviceModel["name"] = formModel["name"];
    serviceModel["misfire_grace_time"] = formModel["misfire_grace_time"];
    serviceModel["trigger_type"] = formModel["trigger_type"];
    serviceModel["trigger"] = getTrigger(formModel["trigger_type"], formModel);
    serviceModel["request_template"] = requestTemplate;
    serviceModel["coalesce"] = formModel["coalesce"];
    serviceModel["max_instances"] = formModel["max_instances"];
    serviceModel["timeout"] = formModel["timeout"];
    serviceModel["id"] = formModel["id"] || null;
    return serviceModel;
  };

  JobService.TRIGGER_TYPES = ["cron", "date", "interval", "file"];
  JobService.CRON_KEYS = [
    "minute",
    "hour",
    "day",
    "month",
    "day_of_week",
    "year",
    "week",
    "second",
    "cron_jitter",
    "cron_start_date",
    "cron_end_date",
    "cron_timezone",
  ];
  JobService.INTERVAL_KEYS = [
    "interval_num",
    "interval",
    "interval_start_date",
    "interval_end_date",
    "interval_timezone",
    "interval_jitter",
    "interval_reschedule_on_finish",
  ];
  JobService.DATE_KEYS = ["run_date", "date_timezone"];
  JobService.FILE_KEYS = [
    "file_pattern",
    "file_path",
    "file_recursive",
    "file_callbacks",
  ];

  JobService.getRequiredKeys = function (triggerType) {
    if (triggerType === "cron") {
      let requiredKeys = [];
      for (let key of JobService.CRON_KEYS) {
        if (
          ![
            "cron_start_date",
            "cron_end_date",
            "cron_timezone",
            "cron_jitter",
          ].includes(key)
        ) {
          requiredKeys.push(key);
        }
      }
      return requiredKeys;
    } else if (triggerType === "date") {
      return JobService.DATE_KEYS;
    } else if (triggerType === "file") {
      return [];
    } else {
      let requiredKeys = [];
      for (let key of JobService.INTERVAL_KEYS) {
        if (
          ![
            "interval_start_date",
            "interval_end_date",
            "interval_timezone",
            "interval_jitter",
            "interval_reschedule_on_finish",
          ].includes(key)
        ) {
          requiredKeys.push(key);
        }
      }
      return requiredKeys;
    }
  };

  JobService.SCHEMA = {
    type: "object",
    required: ["trigger_type", "name"],
    properties: {
      trigger_type: {
        title: "Trigger Type",
        description: "The type of trigger to create.",
        type: "string",
        enum: JobService.TRIGGER_TYPES,
      },
      name: {
        title: "Job Name",
        description: "A non-unique name for this job.",
        type: "string",
        minLength: 1,
      },
      misfire_grace_time: {
        title: "Misfire Grace Time",
        description: "Grace time for missed jobs.",
        type: "integer",
        minimum: 0,
        default: 5,
      },
      coalesce: {
        title: "Coalesce",
        type: "boolean",
        default: true,
      },
      max_instances: {
        title: "Max Instances",
        description: "Maximum number of concurrent job executions.",
        type: "integer",
        minimum: 1,
        default: 3,
      },
      timeout: {
        title: "Timeout",
        description: "Job timeout (in seconds).",
        type: "integer",
      },
      run_date: {
        title: "Run Date",
        description: "Exact time to run this job.",
        type: ["integer", "null"],
        format: "datetime",
      },
      date_timezone: {
        title: "Timezone",
        description: "The timezone associated with this job.",
        type: "string",
        default: "UTC",
      },
      year: {
        title: "Year",
        description: "Cron year value",
        type: "string",
        default: "*",
      },
      month: {
        title: "Month",
        description: "Cron month value",
        type: "string",
        default: "1",
      },
      week: {
        title: "Week",
        description: "Cron week value",
        type: "string",
        default: "*",
      },
      day_of_week: {
        title: "Day Of Week",
        description: "Day of Week",
        type: "string",
        default: "*",
      },
      hour: {
        title: "Hour",
        description: "Cron hour value",
        type: "string",
        default: "0",
      },
      minute: {
        title: "Minute",
        description: "Cron minute value",
        type: "string",
        default: "0",
      },
      second: {
        title: "Second",
        description: "Cron second value",
        type: "string",
        default: "0",
      },
      day: {
        title: "Day",
        description: "Cron day value",
        type: "string",
        default: "1",
      },
      cron_end_date: {
        title: "End Date",
        description: "Date when the cron should end.",
        type: ["integer", "null"],
        format: "datetime",
      },
      cron_timezone: {
        title: "Timezone",
        description: "Timezone to apply to start/end date.",
        type: "string",
        default: "UTC",
      },
      cron_start_date: {
        title: "Start Date",
        description: "Date when the cron should start.",
        type: ["integer", "null"],
        format: "datetime",
      },
      cron_jitter: {
        title: "Cron Jitter",
        description:
          "Advance or delay job execute by this many seconds at most.",
        type: "integer",
        minimum: 0,
      },
      interval_end_date: {
        title: "End Date",
        description: "Date when the job should end.",
        type: ["integer", "null"],
        format: "datetime",
      },
      interval_timezone: {
        title: "Timezone",
        description: "Timezone to apply to start/end date.",
        type: "string",
        default: "UTC",
      },
      interval_start_date: {
        title: "Start Date",
        description: "Date when the job should start.",
        type: ["integer", "null"],
        format: "datetime",
      },
      interval: {
        title: "Interval",
        description: "Repeat this job every X of this interval",
        type: "string",
        enum: ["seconds", "minutes", "hours", "days", "weeks"],
        default: "hours",
      },
      interval_num: {
        title: "Interval Number",
        description: "Repeat this job every X of the interval",
        type: "integer",
        default: 1,
        minimum: 0,
      },
      interval_jitter: {
        title: "Interval Jitter",
        description:
          "Advance or delay job execute by this many seconds at most.",
        type: "integer",
        minimum: 0,
      },
      interval_reschedule_on_finish: {
        title: "Reschedule on Finish",
        description: "Reset the interval timer when the job finishes.",
        type: "boolean",
      },
      file_pattern: {
        title: "Pattern",
        description:
          "File name patterns to match, supports non-extended shell-style glob pattern matching",
        type: "array",
        items: {
          type: "string",
        },
      },
      file_path: {
        title: "Path",
        description: "Directory to watch.",
        type: "string",
      },
      file_recursive: {
        title: "Recursive",
        description: "Look more than one level deep in the directory.",
        type: "boolean",
      },
      file_callbacks: {
        title: "Callbacks",
        description: "What file events should trigger the plugins?",
        type: "object",
        properties: {
          on_created: { type: "boolean" },
          on_modified: { type: "boolean" },
          on_moved: { type: "boolean" },
          on_deleted: { type: "boolean" },
        },
      },
    },
  };

  JobService.FORM = [
    {
      type: "fieldset",
      items: ["name", "trigger_type"],
    },
    {
      type: "fieldset",
      items: [
        {
          type: "tabs",
          tabs: [
            {
              title: "Job Optional Fields",
              items: [
                "coalesce",
                "misfire_grace_time",
                "max_instances",
                "timeout",
              ],
            },
            {
              title: "Cron Trigger",
              items: [
                {
                  type: "section",
                  htmlClass: "row",
                  items: [
                    { key: "minute", htmlClass: "col-md-2" },
                    { key: "hour", htmlClass: "col-md-2" },
                    { key: "day", htmlClass: "col-md-2" },
                    { key: "month", htmlClass: "col-md-2" },
                    { key: "day_of_week", htmlClass: "col-md-2" },
                  ],
                },
                {
                  type: "section",
                  htmlClass: "row",
                  items: [
                    { key: "year", htmlClass: "col-md-3" },
                    { key: "week", htmlClass: "col-md-3" },
                    { key: "second", htmlClass: "col-md-3" },
                    { key: "cron_jitter", htmlClass: "col-md-3" },
                  ],
                },
                {
                  type: "section",
                  htmlClass: "row",
                  items: [
                    { key: "cron_start_date", htmlClass: "col-md-4" },
                    { key: "cron_end_date", htmlClass: "col-md-4" },
                    { key: "cron_timezone", htmlClass: "col-md-4" },
                  ],
                },
              ],
            },
            {
              title: "Interval Trigger",
              items: [
                {
                  type: "section",
                  htmlClass: "row",
                  items: [
                    { key: "interval_num", htmlClass: "col-md-2" },
                    { key: "interval", htmlClass: "col-md-2" },
                    { key: "interval_jitter", htmlClass: "col-md-2" },
                    {
                      key: "interval_reschedule_on_finish",
                      htmlClass: "col-md-2",
                    },
                  ],
                },
                {
                  type: "section",
                  htmlClass: "row",
                  items: [
                    { key: "interval_start_date", htmlClass: "col-md-4" },
                    { key: "interval_end_date", htmlClass: "col-md-4" },
                    { key: "interval_timezone", htmlClass: "col-md-4" },
                  ],
                },
              ],
            },
            {
              title: "Date Trigger",
              items: [
                {
                  type: "section",
                  htmlClass: "row",
                  items: [
                    { key: "run_date", htmlClass: "col-md-6" },
                    { key: "date_timezone", htmlClass: "col-md-2" },
                  ],
                },
              ],
            },
            {
              title: "File Trigger",
              items: [
                {
                  type: "section",
                  htmlClass: "row",
                  items: [
                    { key: "file_pattern", htmlClass: "col-md-4" },
                    { key: "file_path", htmlClass: "col-md-2" },
                    { key: "file_recursive", htmlClass: "col-md-2" },
                    { key: "file_callbacks", htmlClass: "col-md-2" },
                  ],
                },
              ],
            },
          ],
        },
      ],
    },
    {
      type: "section",
      htmlClass: "row",
      items: [
        {
          type: "button",
          style: "btn-warning w-100 ",
          title: "Reset",
          onClick: "reset(ngform, model, system, command.data)",
          htmlClass: "col-md-2",
        },
        {
          type: "submit",
          style: "btn-primary w-100",
          title: "Create Job",
          htmlClass: "col-md-10",
        },
      ],
    },
  ];

  return JobService;
}
