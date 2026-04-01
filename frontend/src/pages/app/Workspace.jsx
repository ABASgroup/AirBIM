import { useNavigate, useParams } from 'react-router-dom';
import { useWorkspace } from "@/context/WorkspaceContext"
import { UnfilledButton } from "@ui/UnfilledButton";

function Workspace() {
    const { workspaceId } = useParams();
    const { workspaces } = useWorkspace();
    const workspace = workspaces.find(w => w.id === workspaceId);

    return (
        <>
            <h1>Управление — </h1>
        </>
    )
}

export default Workspace;