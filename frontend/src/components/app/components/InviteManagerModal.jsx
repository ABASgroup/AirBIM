import { useState, useEffect } from "react";
import { Modal, Select, FilledButton, ConfirmModal } from "@ui";
import { createInviteLink, revokeInviteLinks } from "@/api/invites";
import { useWorkspace } from "@/context/WorkspaceContext";
import { ROLES } from "@/constants";

const ROLE_OPTIONS = ROLES.filter(r => r.value === "member" || r.value === "viewer");

export const InviteManagerModal = ({ isOpen, onClose, showBackdrop }) => {
  const { currentWorkspace } = useWorkspace();
  const [link, setLink] = useState(null);
  const [role, setRole] = useState("member");
  const [loading, setLoading] = useState(false);
  const workspaceId = currentWorkspace?.id;
  const [confirmRevokeLinks, setConfirmRevokeLinks] = useState(null);

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
      setConfirmRevokeLinks(false);
    }
  };
  if (!isOpen) return null;
  const fullUrl = link ? `${window.location.origin}/invites/${link.token}` : "";

  if (confirmRevokeLinks) {
    return (
      <ConfirmModal
        isOpen={true}
        title="Отзыв пригласительных ссылок"
        message="Вы уверены, что хотите отозвать все пригласительные ссылки?"
        onConfirm={handleRevoke}
        onCancel={() => setConfirmRevokeLinks(false)}
      />
    );
  }

  return (
    <Modal title="Приглашение участников" isOpen={isOpen} onClose={onClose} showBackdrop={showBackdrop}>
      <div className="flex flex-col gap-5">
        <div className="flex flex-col">
          <label>Роль для новых участников</label>
          <Select value={role} onChange={handleRoleChange} options={ROLE_OPTIONS} disabled={loading} />
        </div>

        <div className="flex flex-col">
          <label>Пригласительная ссылка</label>
          <div className="flex gap-2">
            <input
              type="text"
              readOnly
              value={fullUrl || "Ссылки отозваны"}
              className="flex-1 bg-background-color border-none rounded-[5px] p-3 text-sm text-text-color outline-none"
            />
            <FilledButton onClick={handleCopy}>
              <i className="fa-solid fa-copy text-text-color"></i>
              Копировать
            </FilledButton>
            <button onClick={() => setConfirmRevokeLinks(true)} className="cursor-pointer active:scale-95 hover:brightness-70">
              <i className="fa-solid fa-ban text-primary-color"></i>
            </button>
          </div>
        </div>
      </div>
    </Modal>
  );
};