import {
  PropsWithChildren,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

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
  const [checking, setChecking] = useState(config?.auth_enabled === true);
  const runValidation = useRef(config?.auth_enabled === true);

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
    if (!runValidation.current) {
      if (checking) {
        setChecking(false);
      }
      return;
    }

    if (checking) {
      setHasAccess(validatePermissions());
      setChecking(false);
      runValidation.current = false;
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
