export const ALL = "bg-all";
export const COMMAND_CREATE = "bg-command-create";
export const COMMAND_READ = "bg-command-read";
export const COMMAND_UPDATE = "bg-command-update";
export const COMMAND_DELETE = "bg-command-delete";
export const EVENT_CREATE = "bg-event-create";
export const EVENT_READ = "bg-event-read";
export const EVENT_UPDATE = "bg-event-update";
export const EVENT_DELETE = "bg-event-delete";
export const INSTANCE_CREATE = "bg-instance-create";
export const INSTANCE_READ = "bg-instance-read";
export const INSTANCE_UPDATE = "bg-instance-update";
export const INSTANCE_DELETE = "bg-instance-delete";
export const QUEUE_CREATE = "bg-queue-create";
export const QUEUE_READ = "bg-queue-read";
export const QUEUE_UPDATE = "bg-queue-update";
export const QUEUE_DELETE = "bg-queue-delete";
export const JOB_CREATE = "bg-job-create";
export const JOB_READ = "bg-job-read";
export const JOB_UPDATE = "bg-job-update";
export const JOB_DELETE = "bg-job-delete";
export const REQUEST_CREATE = "bg-request-create";
export const REQUEST_READ = "bg-request-read";
export const REQUEST_UPDATE = "bg-request-update";
export const REQUEST_DELETE = "bg-request-delete";
export const ROLE_CREATE = "bg-role-create";
export const ROLE_READ = "bg-role-read";
export const ROLE_UPDATE = "bg-role-update";
export const ROLE_DELETE = "bg-role-delete";
export const SYSTEM_CREATE = "bg-system-create";
export const SYSTEM_READ = "bg-system-read";
export const SYSTEM_UPDATE = "bg-system-update";
export const SYSTEM_DELETE = "bg-system-delete";
export const USER_CREATE = "bg-user-create";
export const USER_READ = "bg-user-read";
export const USER_UPDATE = "bg-user-update";
export const USER_DELETE = "bg-user-delete";

export const CATEGORIES = {
  user: {
    create: USER_CREATE,
    read: USER_READ,
    update: USER_UPDATE,
    delete: USER_DELETE,
  },
  command: {
    create: COMMAND_CREATE,
    read: COMMAND_READ,
    update: COMMAND_UPDATE,
    delete: COMMAND_DELETE,
  },
  event: {
    create: EVENT_CREATE,
    read: EVENT_READ,
    update: EVENT_UPDATE,
    delete: EVENT_DELETE,
  },
  instance: {
    create: INSTANCE_CREATE,
    read: INSTANCE_READ,
    update: INSTANCE_UPDATE,
    delete: INSTANCE_DELETE,
  },
  queue: {
    create: QUEUE_CREATE,
    read: QUEUE_READ,
    update: QUEUE_UPDATE,
    delete: QUEUE_DELETE,
  },
  job: {
    create: JOB_CREATE,
    read: JOB_READ,
    update: JOB_UPDATE,
    delete: JOB_DELETE,
  },
  request: {
    create: REQUEST_CREATE,
    read: REQUEST_READ,
    update: REQUEST_UPDATE,
    delete: REQUEST_DELETE,
  },
  role: {
    create: ROLE_CREATE,
    read: ROLE_READ,
    update: ROLE_UPDATE,
    delete: ROLE_DELETE,
  },
  system: {
    create: SYSTEM_CREATE,
    read: SYSTEM_READ,
    update: SYSTEM_UPDATE,
    delete: SYSTEM_DELETE,
  },
};

export const LIST_ALL = [].concat.apply(
  [],
  Object.values(CATEGORIES).map(r => Object.values(r)),
);
