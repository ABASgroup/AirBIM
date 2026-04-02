// Компонент списка пользователей с ролями
import { useState, useEffect } from "react";
import { getWorkspaceMembers } from "@/api/workspace";
import { Select } from "@ui";

export const MemberList = ({ workspaceId }) => {
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [hasPermission, setHasPermission] = useState(true);
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
  const roles = [
    { value: "owner", label: "Владелец" },
    { value: "admin", label: "Администратор" },
    { value: "member", label: "Редактор" },
    { value: "viewer", label: "Наблюдатель" },
  ];
  const selectRoles = roles.filter(r => r.value !== "owner");
  if (loading) {
    return <div>Загрузка участников...</div>;
  }

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
                  <Select
                    value={member.role}
                    options={isOwner ? roles : selectRoles}
                    disabled={isOwner}
                    className="w-70 h-full"
                    bgClassName="bg-surface"
                  />
                  <div className="h-full w-14 flex items-center justify-center">
                    <i className="fa-solid fa-bars text-text-color text-xl w-14 pr-2 flex justify-center"></i>
                  </div>
                </div>
              )
            })
          }
        </div >
      ) : (<p>У вас нет прав на просмотр данной вкладки</p>)
    )

  );
};