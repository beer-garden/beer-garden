import { PropsWithChildren, useEffect, useState } from "react";

import { HasAccessProps, PermissionCheck } from "../models/models";
import { checkPermission } from "../services/permission_service";

const HasAccess = ({
  config,
  permission,
  isGlobal,
  hasGardenName,
  hasNamespace,
  hasSystemName,
  hasSystemVersion,
  hasCommandName,
  hasInstanceName,
  isLoading,
  renderAuthFailed,
  children,
}: PropsWithChildren<HasAccessProps>) => {
  const [hasAccess, setHasAccess] = useState(false);
  const [checking, setChecking] = useState(false);

  if (config === undefined || permission === undefined) {
    return children;
  }

  useEffect(() => {
    setChecking(true);

    const check = {
      global: isGlobal,
      gardenName: hasGardenName,
      namespace: hasNamespace,
      systemName: hasSystemName,
      systemVersion: hasSystemVersion,
      commandName: hasCommandName,
      instanceName: hasInstanceName,
    } as PermissionCheck;

    setHasAccess(checkPermission(config, permission, check));

    setChecking(false);
  }, [
    permission,
    isGlobal,
    hasGardenName,
    hasNamespace,
    hasSystemName,
    hasSystemVersion,
    hasCommandName,
    hasInstanceName,
  ]);

  if (!hasAccess && checking) {
    return isLoading;
  }

  if (hasAccess) {
    return children;
  }

  if (renderAuthFailed) {
    return renderAuthFailed;
  }

  return null;
};

export default HasAccess;
