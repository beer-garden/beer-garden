import { PropsWithChildren, useEffect, useState } from "react";

import { HasAccessProps } from "../models/models";
import { checkPermission } from "../services/permission_service";

const HasAccess = ({
  permission,
  check,
  isLoading,
  renderAuthFailed,
  children,
}: PropsWithChildren<HasAccessProps>) => {
  const [hasAccess, setHasAccess] = useState(false);
  const [checking, setChecking] = useState(false);

  useEffect(() => {
    setChecking(true);

    setHasAccess(checkPermission(permission, check));

    setChecking(false);
  }, [permission, check]);

  if (!hasAccess && checking) {
    return isLoading;
  }

  if (hasAccess) {
    return (
      // children is of type ReactNode which already includes ReactFragment
      { children }
    );
  }

  if (renderAuthFailed) {
    return renderAuthFailed;
  }

  return null;
};

export default HasAccess;
