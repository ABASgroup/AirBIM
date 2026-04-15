import { useState, useEffect } from "react";
import { Modal, Select, FilledButton } from "@ui";
import { createInviteLink, revokeInviteLinks } from "@/api/invites";
import { useWorkspace } from "@/context/WorkspaceContext";

const ROLE_OPTIONS = [
  { value: "member", label: "Редактор" },
  { value: "viewer", label: "Наблюдатель" },
];

export const InviteManagerModal = ({ isOpen, onClose, showBackdrop }) => {
  const { currentWorkspace } = useWorkspace();
  const [link, setLink] = useState(null);
  const [role, setRole] = useState("member");
  const [loading, setLoading] = useState(false);
  const workspaceId = currentWorkspace?.id;

  useEffect(() => {
    if (!isOpen || !workspaceId) return;
    const saved = sessionStorage.getItem(`inviteLink_${workspaceId}`);
    if (saved) {
      setLink(JSON.parse(saved));
    } else {
      handleCreateLink(role);
    }
  }, [isOpen, workspaceId, role]);
  const handleCreateLink = async (targetRole) => {
    if (!workspaceId) return;
    setLoading(true);
    try {
      const res = await createInviteLink(workspaceId, targetRole);
      setLink(res.data);
      sessionStorage.setItem(`inviteLink_${workspaceId}`, JSON.stringify(res.data));
    } catch (err) {
      console.error("Не удалось создать ссылку", err);
      setLink(null);
    } finally {
      setLoading(false);
    }
  };
  const handleRoleChange = (newRole) => {
    setRole(newRole);
    handleCreateLink(newRole);
  };
  const handleCopy = () => {
    if (!link?.token) return;
    const url = `${window.location.origin}/invites/${link.token}`;
    navigator.clipboard.writeText(url);
  };
  const handleRevoke = async () => {
    if (!workspaceId) return;
    setLoading(true);
    try {
      await revokeInviteLinks(workspaceId);
      setLink(null);
      sessionStorage.removeItem(`inviteLink_${workspaceId}`);
    } catch (err) {
      console.error("Не уадалось отозвать ссылку", err);
    } finally {
      setLoading(false);
    }
  };
  if (!isOpen) return null;
  const fullUrl = link ? `${window.location.origin}/invites/${link.token}` : "";

  return (
    <Modal title="Приглашение участников" isOpen={isOpen} onClose={onClose} showBackdrop={showBackdrop}>
      <div className="flex flex-col gap-5">
        <div className="flex flex-col gap-2">
          <label>Роль для новых участников</label>
          <Select value={role} onChange={handleRoleChange} options={ROLE_OPTIONS} disabled={loading} />
        </div>

        <div className="flex flex-col gap-2">
          <label>Пригласительная ссылка</label>
          <div className="flex gap-2">
            <input
              type="text"
              readOnly
              value={fullUrl || "Ссылка отозвана"}
              className="flex-1 bg-background-color border-none rounded-[5px] p-3 text-sm text-text-color outline-none"
            />
            <FilledButton
              onClick={handleCopy}
              disabled={!link || loading}
            >
              <i className="fa-solid fa-copy text-text-color"></i>
              Копировать
            </FilledButton>
          </div>
        </div>
        <FilledButton
          color="warning"
          onClick={handleRevoke}
          disabled={loading || !link}
        >
          Отозвать все ссылки
        </FilledButton>
      </div>
    </Modal>
  );
};