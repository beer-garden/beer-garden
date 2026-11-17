type parameter_types =
  | "String"
  | "Integer"
  | "Float"
  | "Boolean"
  | "Any"
  | "Dictionary"
  | "Date"
  | "DateTime"
  | "Bytes"
  | "Base64"
  | "null";
type output_types = "STRING" | "JSON" | "XML" | "HTML" | "JS" | "CSS";

export interface AliasUserMap {
  target_garden?: string;
  username?: string;
}

export interface Choices {
  type?: string;
  display?: string;
  value?:
    | Array<{ text: string; value: string } | string>
    | { [key: string]: Array<{ text: string; value: string } | string> }
    | ChoicesValue
    | string;
  strict?: boolean;
  details?: Details;
}

export interface ChoicesValue {
  system?: string;
  system_version?: string;
  instance_name?: string;
  namespace?: string;
  command?: string;
}

export interface Details {
  name?: string;
  args?: Array<Array<string>>;
  address?: string;
  key_reference?: string;
}

export interface Command {
  name?: string;
  display_name?: string;
  description?: string;
  parameters?: Parameter[];
  command_type?: string;
  output_type?: output_types;
  schema?: object;
  form?: object;
  template?: string;
  icon_name?: string;
  hidden?: boolean;
  metadata?: object;
  tags?: string[];
  topics?: string[];
  allow_any_kwargs?: boolean;
}

export interface Connection {
  api?: string;
  status?: string;
  status_info?: any;
  config?: any;
}

export interface CronTrigger {
  year?: string;
  month?: string;
  day?: string;
  week?: string;
  dayOfWeek?: string;
  hour?: string;
  minute?: string;
  second?: string;
  startDate?: any;
  endDate?: any;
  timezone?: string;
  jitter?: number | null;
}

export interface DateTrigger {
  run_date?: any;
  timezone?: string;
}

export interface Event {
  name?: string;
  namespace?: string;
  garden?: string;
  metadata?: object;
  timestamp?: any;
  payloadType?: string;
  payload?: any;
  error?: boolean;
  errorMessage?: string;
}

export interface FileChunk {
  id?: string;
  fileId?: string;
  offset?: number;
  data?: string;
  owner?: any;
}

export interface File {
  id?: string;
  ownerId?: string;
  ownerType?: string;
  owner?: any;
  job?: any;
  request?: any;
  updatedAt?: any;
  fileName?: string;
  fileSize?: number;
  chunks?: object;
  chunkSize?: number;
  md5Sum?: string;
}

export interface FileStatus {
  fileId?: string;
  updatedAt?: string;
  fileName?: string;
  fileSize?: number;
  chunkSize?: number;
  chunks?: object;
  ownerId?: string;
  ownerType?: string;
  md5Sum?: string;
  chunkId?: string;
  offset?: number;
  data?: string;
  valid?: boolean;
  missingChunks?: any[];
  expectedNumberOfChunks?: number;
  expectedMaxSize?: number;
  numberOfChunks?: number;
  sizeOk?: boolean;
  chunksOk?: boolean;
  operationComplete?: boolean;
  message?: string;
}

export interface FileTrigger {
  pattern?: string;
  path?: string;
  recursive?: boolean;
  create?: boolean;
  modify?: boolean;
  move?: boolean;
  delete?: boolean;
}

export interface Garden {
  id?: string;
  name?: string;
  status?: string;
  status_info?: any;
  connection_type?: string;
  receiving_connections?: any;
  publishing_connections?: any;
  namespaces?: any[];
  systems?: any;
  has_parent?: boolean;
  parent?: string;
  children?: any;
  metadata?: object;
  default_user?: string;
  shared_users?: boolean;
  version?: string;
}

export interface Instance {
  id?: string;
  name?: string;
  description?: string;
  status?: string;
  status_info?: status_info;
  queueType?: string;
  queueInfo?: object;
  icon_name?: string;
  metadata?: InstanceMetadata;
}

export interface InstanceMetadata {
  runner_id?: string;
}

export interface IntervalTrigger {
  weeks?: number;
  days?: number;
  hours?: number;
  minutes?: number;
  seconds?: number;
  startDate?: any;
  endDate?: any;
  timezone?: string;
  jitter?: number;
  rescheduleOnFinish?: boolean;
}

export interface JobExportInput {
  ids?: any[];
}

export interface JobExportList {
  jobs?: any[];
}

export interface JobExport {
  id?: string;
  name?: string;
  triggerType?: string;
  trigger?: any;
  requestTemplate?: any;
  misfireGraceTime?: number;
  coalesce?: boolean;
  nextRunTime?: any;
  successCount?: number;
  errorCount?: number;
  canceledCount?: number;
  skipCount?: number;
  status?: string;
  max_instances?: number;
  timeout?: number;
}

export interface Job {
  id?: string;
  name?: string;
  trigger_type?: string;
  trigger?: CronTrigger | DateTrigger | IntervalTrigger | FileTrigger;
  request_template?: RequestTemplate;
  misfire_grace_time?: number | null;
  coalesce?: boolean;
  next_run_time?: any;
  success_count?: number;
  error_count?: number;
  canceled_count?: number;
  skip_count?: number;
  status?: string;
  max_instances?: number | null;
  timeout?: number | null;
}

export interface LoggingConfig {
  level?: string;
  formatters?: object;
  handlers?: object;
}

export interface Operation {
  modelType?: string;
  model?: any;
  args?: any[];
  kwargs?: object;
  targetGardenName?: string;
  sourceGardenName?: string;
  sourceApi?: string;
  operationType?: string;
}

export interface Parameter {
  key?: string;
  type?: parameter_types;
  multi?: boolean;
  display_name?: string;
  optional?: boolean;
  default?: any;
  description?: string;
  choices?: Choices;
  parameters?: Parameter[];
  nullable?: boolean;
  maximum?: number;
  minimum?: number;
  regex?: string;
  form_input_type?: string;
  type_info?: object;
}

export interface Patch {
  operation?: string;
  path?: string;
  value?: any;
}

export interface Queue {
  name?: string;
  system?: string;
  version?: string;
  instance?: string;
  systemId?: string;
  display?: string;
  size?: number;
}

export interface Replication {
  id?: string;
  replicationId?: string;
  expiresAt?: any;
}

export interface RequestFile {
  storageType?: string;
  filename?: string;
  id?: string;
}

export interface Request {
  system?: string;
  system_version?: string;
  instance_name?: string;
  namespace?: string;
  command?: string;
  command_display_name?: string;
  command_type?: string;
  parameters?: Record<string, any>;
  comment?: string;
  metadata?: RequestMetadata;
  output_type?: output_types;
  id?: string;
  is_event?: boolean;
  parent?: any;
  children?: Request[];
  output?: string;
  hidden?: boolean;
  status?: string;
  error_class?: string;
  created_at?: any;
  updated_at?: any;
  status_updated_at?: any;
  has_parent?: boolean;
  requester?: string;
  source_garden?: string;
  target_garden?: string;
  parent_id?: string;
}

export interface RequestMetadata {
  [key: string]: number | string;
}

export interface RequestTemplate {
  system?: string;
  system_version?: string;
  instance_name?: string;
  namespace?: string;
  command?: string;
  command_display_name?: string;
  command_type?: string;
  parameters?: object;
  comment?: string;
  metadata?: object;
  output_type?: string;
}

export interface Resolvable {
  id?: string;
  type?: string;
  storage?: string;
  details?: object;
}

export interface Role {
  permission?: string;
  description?: string;
  id?: string;
  name?: string;
  scope_gardens?: any[];
  scope_namespaces?: any[];
  scope_systems?: any[];
  scope_instances?: any[];
  scope_versions?: any[];
  scope_commands?: any[];
  protected?: boolean;
  file_generated?: boolean;
}

export interface Runner {
  id?: string;
  name?: string;
  path?: string;
  instance_id?: string;
  stopped?: boolean;
  dead?: boolean;
  restart?: boolean;
}

export interface StatusHistory {
  heartbeat?: any;
  status?: string;
}

export interface status_info {
  heartbeat?: any;
  history?: StatusHistory[];
}

export interface Subscriber {
  garden?: string;
  namespace?: string;
  system?: string;
  version?: string;
  instance?: string;
  command?: string;
  subscriber_type?: string;
  consumer_count?: number;
}

export interface SystemDomainIdentifier {
  name?: string;
  version?: string;
  namespace?: string;
}

export interface System {
  id?: string;
  name?: string;
  description?: string;
  version?: string;
  max_instances?: number;
  icon_name?: string;
  instances?: Instance[];
  commands?: Command[];
  display_name?: string;
  metadata?: object;
  namespace?: string;
  local?: boolean;
  template?: string;
  groups?: string[];
  prefix_topic?: string;
  requires?: string[];
  requires_timeout?: number;
  garden_name?: string;
}

export interface Topic {
  id?: string;
  name?: string;
  subscribers?: any[];
  publisher_count?: number;
}

export interface UpstreamRole {
  permission?: string;
  description?: string;
  id?: string;
  name?: string;
  scope_gardens?: any[];
  scope_namespaces?: any[];
  scope_systems?: any[];
  scope_instances?: any[];
  scope_versions?: any[];
  scope_commands?: any[];
  protected?: boolean;
  file_generated?: boolean;
}

export interface UserMetadata {
  last_authentication?: any;
  has_token?: boolean;
}

export interface User {
  id?: string;
  username?: string;
  password?: string;
  roles?: Role[];
  local_roles?: Role[];
  upstream_roles?: Role[];
  user_alias_mapping?: AliasUserMap[];
  is_remote?: boolean;
  metadata?: UserMetadata;
  protected?: boolean;
  file_generated?: boolean;
}

export interface UserToken {
  id?: string;
  uuid?: string;
  issuedAt?: any;
  expiresAt?: any;
  username?: string;
}
