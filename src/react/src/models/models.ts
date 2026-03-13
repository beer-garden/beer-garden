import { Instance, System } from "../models/brewtils-types";

export interface Config {
  application_name: string;
  auth_enabled: string;
  trusted_header_auth_enabled: string;
  icon_default: string;
  debug_mode: string;
  execute_javascript: string;
  auto_refresh: string;
  search_delay: string;
  garden_name: string;
  metrics_url: string;
  url_prefix: string;
  action_ttl: number;
  info_ttl: number;
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
  namespace: string | null;
  systemName: string | null;
  version: string | null;
  instance: string | null;
  command: string | null;
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
  permission: string;
  check: PermissionCheck;
  isLoading?: React.ReactElement;
  renderAuthFailed?: React.ReactElement;
}
