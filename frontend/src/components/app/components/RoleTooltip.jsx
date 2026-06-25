import { Tooltip } from "@ui";
import { ROLES } from "@/constants";

export const RoleTooltip = ({ role, children, className = "", disabled = false }) => {
  const roleData = ROLES.find(r => r.value === role);

  if (!roleData) return children;

  const content = (
    <div>
      <h3 className="font-bold mt-1">{roleData.label}</h3>
      <p className="text-sm mt-1">{roleData.description}</p>
      <p className="text-sm mt-1 mb-1">Права:</p>
      <ul className="text-sm m-0 pl-4">
        {roleData.permissions.map((perm, idx) => (
          <li key={idx}>{perm}</li>
        ))}
      </ul>
    </div>
  );

  return (
    <Tooltip content={content} className={className} disabled={disabled}>
      {children}
    </Tooltip>
  );
};