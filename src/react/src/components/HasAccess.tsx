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
  const [hasAccess, setHasAccess] = useState(
    config?.auth_enabled === undefined || config?.auth_enabled === false,
  );
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    if (!hasAccess) {
      setChecking(true);
    }
    if (checking) {
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
