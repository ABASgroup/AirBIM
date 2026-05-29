import { useWorkspace } from "@/context/WorkspaceContext";
import { LoadingSpinner } from "@ui";

export const Can = ({ permission, permissions, fallback = null, children}) => {
  const { hasPermission, loadingPermissions } = useWorkspace();

  if (loadingPermissions) {
    return <LoadingSpinner variant="inline"/>;
  }
  let isAllowed = false;
  const permissionToCheck = permission ? [permission] : permissions;
  if (permissionToCheck && permissionToCheck.length > 0) {
    isAllowed = hasPermission(permissionToCheck);
  }
  return isAllowed ? children : fallback;
};