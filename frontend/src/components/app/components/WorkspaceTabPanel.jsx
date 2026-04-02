// Панель настроек воркспейса
import { useState } from "react";
import { TabPanel } from "@ui";
import { MemberList } from "@app/components/MemberList";

export const WorkspaceTabPanel = ({ workspace }) => {
	const [activeTab, setActiveTab] = useState("general");
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
				<MemberList workspaceId={workspace?.id} />
			)}
		</TabPanel>
	);
};