import { JwtPayload } from "jwt-decode";

import {
  Command,
  Instance,
  Job,
  Parameter,
  Request,
  Runner,
  System,
  Topic,
} from "../models/brewtils-types";

export interface Config {
  application_name?: string;
  auth_enabled?: boolean;
  trusted_header_auth_enabled?: boolean;
  icon_default?: string;
  debug_mode?: boolean;
  execute_javascript?: boolean;
  auto_refresh?: boolean;
  search_delay?: string;
  garden_name?: string;
  metrics_url?: string;
  url_prefix?: string;
  action_ttl?: number;
  info_ttl?: number;
}

export interface Version {
  beer_garden_version: string;
  python_version: string;
  current_api_version: string;
  supported_api_versions: string[];
}

export interface Listener {
  listener: (message: any) => void;
  props: Record<string, any>;
}

export interface ScratchPadValue {
  padId: string;
  padType: string | null;
  values: any;
}

export interface RequestCommand {
  namespace?: string;
  systemName?: string;
  version?: string;
  instance?: string;
  command?: string;
}

export interface RequestItem {
  requestId?: string;
  request?: Request;
  requestCommandInput?: RequestCommand;

  showSchedule?: boolean;
  jobId?: string;
  job?: Job;

  topic?: Topic;

  itemId: string;
  type: string;
}

export interface InputParam extends Parameter {
  value?: any;
  isInvalid: boolean;
  options: Array<{ label: string; value: any }> | undefined;
  error: boolean;
  errorMsg?: string;
}

export interface InstanceDialogProps {
  instance: Instance;
  system: System;
  isVisible: boolean;
  onClose: any;
}

export interface PermissionCheck {
  global?: boolean;
  gardenName?: string;
  namespace?: string;
  systemName?: string;
  systemVersion?: string;
  commandName?: string;
  instanceName?: string;
}

export interface HasAccessProps {
  label?: string;
  tooltip?: string;
  config?: Config;
  permission?: "READ_ONLY" | "OPERATOR" | "PLUGIN_ADMIN" | "GARDEN_ADMIN";
  isGlobal?: boolean;
  hasGardenName?: string;
  hasNamespace?: string;
  hasSystemName?: string;
  hasSystemVersion?: string;
  hasCommandName?: string;
  hasInstanceName?: string;
  isLoading?: React.ReactElement;
  renderAuthFailed?: React.ReactElement;
}

export interface CommandFormProps {
  command: Command | null | undefined;
  disabled?: boolean;
  request?: Request | null | undefined;
  setRequest: (request: Request) => void;
  resetForm: boolean;
  setResetForm: (reset: boolean) => void;
  setIsFormValid: (isValid: boolean) => void;
}

export interface TourStepProps {
  content: string;
  prefix: string;
  uuid?: string;
  label: string;
  layer: "NAVIGATION" | "LAYOUT" | "COMPONENT";
  pos: number;
}

export interface RunnerGroup {
  path: string;
  runners: Runner[];
}

export interface CustomJwtPayload extends JwtPayload {
  username?: string;
  roles?: string[];
  preferences?: {
    theme?: string;
    dark_mode: boolean;
    power_user: boolean;
  };
}
