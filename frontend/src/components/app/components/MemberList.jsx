// Компонент списка пользователей с ролями
import { useState, useEffect, useRef } from "react";
import { getWorkspaceMembers, removeWorkspaceMember, changeUserRole } from "@/api/workspace";
import { Select, ActionMenu } from "@ui";
import { RoleTooltip } from "@app/components";
import { ROLES } from "@/utils/roles";

export const MemberList = ({ workspaceId }) => {
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [hasPermission, setHasPermission] = useState(true);
  const [activeMenuId, setActiveMenuId] = useState(null);
  const actionBtnRefs = useRef({});
  const [removingId, setRemovingId] = useState(null);
  const [changingRoleId, setChangingRoleId] = useState(null);
  const [openSelectId, setOpenSelectId] = useState(null);
  const selectRoles = ROLES.filter(r => r.value !== "owner");
  useEffect(() => {
    if (workspaceId) {
      getWorkspaceMembers(workspaceId)
        .then(res => setMembers(res.data))
        .catch(err => {
          if (err.response?.status === 403) {
            setHasPermission(false);
          }
        })
        .finally(() => setLoading(false));
    }
  }, [workspaceId]);

  if (loading) {
    return <div>Загрузка участников...</div>;
  }

  const handleRemoveMember = async (userId) => {
    try {
      setRemovingId(userId);
      await removeWorkspaceMember(workspaceId, userId);
      setMembers(members.filter(m => m.user.id !== userId));
      setActiveMenuId(null);
    } catch (err) {
      console.error("Не удалось удалить пользователя:", err);
    } finally {
      setRemovingId(null);
    }
  };

  const handleRoleChange = async (userId, newRole) => {
    try {
      setChangingRoleId(userId);
      await changeUserRole(workspaceId, userId, newRole);
      setMembers(members.map(m =>
        m.user.id === userId ? { ...m, role: newRole } : m
      ));
    } catch (err) {
      console.error("Failed to change role:", err);
    } finally {
      setChangingRoleId(null);
    }
  };


  return (
    (hasPermission ? (
      <div className="flex flex-col mt-5 gap-3" >
        {
          members.map((member) => {
            const isOwner = member.role === "owner";
            return (
              <div key={member.user.email} className="flex items-center justify-between gap-2 h-14">
                <div className="w-full flex items-center bg-surface p-2 pl-4 rounded-[5px] gap-3">
                  <i className="fa-solid fa-user text-text-color text-xl"></i>
                  <div>
                    <p className="m-0">{member.user.username}</p>
                    <p className="m-0 text-sm text-mute-text-color">{member.user.email}</p>
                  </div>
                </div>
                <RoleTooltip role={member.role} disabled={openSelectId === member.user.id} className="w-70 h-full">
                  <Select
                    value={member.role}
                    options={isOwner ? ROLES : selectRoles}
                    disabled={isOwner}
                    onChange={(newRole) => handleRoleChange(member.user.id, newRole)}
                    onOpenChange={(isOpen) => setOpenSelectId(isOpen ? member.user.id : null)}
                    renderOption={(option, button) => (
                      <RoleTooltip key={option.value} role={option.value}>
                        {button}
                      </RoleTooltip>
                    )}
                    className="w-full h-full"
                    bgClassName="bg-surface"
                  />
                </RoleTooltip>
                <div className="h-full w-14 flex items-center justify-center">
                  <button
                    ref={(el) => actionBtnRefs.current[member.user.id] = el}
                    onClick={(e) => {
                      e.stopPropagation();
                      setActiveMenuId(activeMenuId === member.user.id ? null : member.user.id);
                    }}
                    disabled={isOwner}
                    className={`${isOwner ? "opacity-25" : "cursor-pointer"}`}
                  >
                    <i className="fa-solid fa-bars text-text-color text-xl w-14 pr-2 flex justify-center"></i>
                  </button>
                </div>
                {activeMenuId === member.user.id && (
                  <ActionMenu
                    isOpen={true}
                    onClose={() => setActiveMenuId(null)}
                    buttonRef={{ current: actionBtnRefs.current[member.user.id] }}
                  >
                    <button
                      onClick={() => handleRemoveMember(member.user.id)}
                      disabled={removingId === member.user.id}
                    >
                      <i className="fa-solid fa-trash"></i>
                      Удалить
                    </button>
                  </ActionMenu>
                )}

              </div>
            )
          })
        }
      </div >
    ) : (<p>У вас нет прав на просмотр данной вкладки</p>)
    )
  );
};