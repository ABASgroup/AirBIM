// Страница управления воркспейсом
import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getWorkspace } from "@/api/workspace";
import { WorkspaceTabPanel } from "@app/components/WorkspaceTabPanel";
import { useWorkspace } from "@/context/WorkspaceContext";

function WorkspacePage() {
    const { workspaceId } = useParams();
    const [workspace, setWorkspace] = useState(null);
    const { switchWorkspace } = useWorkspace();
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        getWorkspace(workspaceId)
            .then(res => {
                setWorkspace(res.data);
                switchWorkspace(res.data.id);
                setLoading(false);
            })
            .catch(err => {
                if (err.response?.status === 403) {
                    navigate("/app/dashboard", { replace: true });
                }
                setLoading(false);
            });

    }, [workspaceId, switchWorkspace]);

    if (loading) return <div>Загрузка...</div>;

    return (
        <>
            <h1>Управление {workspace.name}</h1>
            <WorkspaceTabPanel workspace={workspace} />
        </>
    );
}
export default WorkspacePage;