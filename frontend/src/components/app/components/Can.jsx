import { useWorkspace } from "@/context/WorkspaceContext";

export const Can = ({ permission, permissions, fallback = null, children}) => {
  const { hasPermission, loadingPermissions } = useWorkspace();

  if (loadingPermissions) {
    return null;
  }
  let isAllowed = false;
  const permissionToCheck = permission ? [permission] : permissions;
  if (permissionToCheck && permissionToCheck.length > 0) {
    isAllowed = hasPermission(permissionToCheck);
  }
  return isAllowed ? children : fallback;
};