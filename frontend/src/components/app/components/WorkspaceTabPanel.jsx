// Панель настроек воркспейса
import { useState } from "react";
import { TabPanel, FilledButton } from "@ui";
import { MemberList, InviteManagerModal } from "@app/components";

export const WorkspaceTabPanel = ({ workspace }) => {
	const [activeTab, setActiveTab] = useState("general");
	const [isModalOpen, setIsModalOpen] = useState(false);
	const tabs = [
		{ id: "general", label: "Основное" },
		{ id: "members", label: "Участники" },
	];
	return (
		<TabPanel tabs={tabs} activeTab={activeTab} onChange={setActiveTab}>
			{activeTab === "general" && (
				<p>Воркспейс создан: {workspace.created_at.split("T")[0]}</p>
			)}
			{activeTab === "members" && (
				<>
					<FilledButton onClick={() => setIsModalOpen(true)}>
						<i className="fa-solid fa-plus text-text-color"></i>
						Создать пригласительную ссылку
					</FilledButton>
					<InviteManagerModal
						isOpen={isModalOpen}
						onClose={() => setIsModalOpen(false)}>
					</InviteManagerModal>
					<MemberList workspaceId={workspace?.id} />
				</>
			)}
		</TabPanel>
	);
};