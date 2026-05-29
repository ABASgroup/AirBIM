// Верхняя панель с переключателем вкладок настроек
export const TabPanel = ({ tabs, activeTab, onChange, children }) => {
	return (
		<div className="bg-background-color">
			<div className="flex border-5 border-surface rounded-[10px] shadow-bottom">
				{tabs.map((tab) => (
					<button
						key={tab.id}
						onClick={() => onChange(tab.id)}
						className={`flex-1 px-4 py-2 ${activeTab === tab.id && "bg-surface rounded-[5px]"}`}
					>
						{tab.label}
					</button>
				))}
			</div>
			<div>{children}</div>
		</div>
	);
};