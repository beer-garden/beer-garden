import { PropsWithChildren, useCallback, useEffect, useState } from "react";

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
  if (config === undefined || permission === undefined) {
    return children;
  }

  const [hasAccess, setHasAccess] = useState(
    config?.auth_enabled === undefined || config?.auth_enabled === false,
  );
  const [checking, setChecking] = useState(config?.auth_enabled === true);

  const validatePermissions = useCallback(() => {
    const check = {
      global: isGlobal,
      gardenName: hasGardenName,
      namespace: hasNamespace,
      systemName: hasSystemName,
      systemVersion: hasSystemVersion,
      commandName: hasCommandName,
      instanceName: hasInstanceName,
    } as PermissionCheck;

    return checkPermission(config, permission, check);
  }, [
    config,
    permission,
    isGlobal,
    hasGardenName,
    hasNamespace,
    hasSystemName,
    hasSystemVersion,
    hasCommandName,
    hasInstanceName,
  ]);

  useEffect(() => {
    if (hasAccess && checking) {
      setChecking(false);
    } else if (checking) {
      setHasAccess(validatePermissions());
      setChecking(false);
    }
  }, [
    checking,
    permission,
    isGlobal,
    hasGardenName,
    hasNamespace,
    hasSystemName,
    hasSystemVersion,
    hasCommandName,
    hasInstanceName,
  ]);

  return (
    <>
      {!hasAccess && checking && isLoading}
      {hasAccess && children}
      {!hasAccess && !checking && renderAuthFailed}
    </>
  );
};

export default HasAccess;
