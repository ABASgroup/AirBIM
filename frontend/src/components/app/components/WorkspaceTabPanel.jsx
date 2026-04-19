// Панель настроек воркспейса
import { useState, useEffect } from "react";
import { TabPanel, FilledButton } from "@ui";
import { MemberList, InviteManagerModal } from "@app/components";
import { useWorkspace } from "@/context/WorkspaceContext";

export const WorkspaceTabPanel = ({ workspace }) => {
  const { hasPermission, loadingPermissions } = useWorkspace();
  const [activeTab, setActiveTab] = useState("general");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const canAccessMembers = !loadingPermissions && hasPermission([
    "members:view",
    "members:invite",
    "members:edit_role"
  ]);
  const tabs = [
    { id: "general", label: "Основное" },
    ...(canAccessMembers ? [{ id: "members", label: "Участники" }] : []),
  ];

  if (loadingPermissions) {
    return <div>Загрузка...</div>;
  }

  const isPersonalWorkspace = workspace?.type === "personal";

  return (
    <TabPanel tabs={tabs} activeTab={activeTab} onChange={setActiveTab}>
      {activeTab === "general" && (
        <p>Воркспейс создан: {workspace.created_at.split("T")[0]}</p>
      )}
      {canAccessMembers && activeTab === "members" && (
        <div className="pt-5">
          {!isPersonalWorkspace && (
            <>
              <FilledButton onClick={() => setIsModalOpen(true)}>
                <i className="fa-solid fa-plus text-text-color"></i>
                Создать пригласительную ссылку
              </FilledButton>
              <InviteManagerModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                showBackdrop>
              </InviteManagerModal>
            </>
          )}
          <MemberList workspaceId={workspace?.id} />
        </div>
      )}
    </TabPanel>
  )
}