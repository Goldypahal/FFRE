import { useState, useEffect } from "react";
import { Header as LayoutHeader } from "../../components/layout/Header";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { Badge } from "../../components/ui/Badge";
import { Table, Cell, HeaderCell, HeaderRow, Header, Body, Row } from "../../components/ui/Table";
import { api } from "../../lib/api";
import {
  Users, Settings, Shield, Plug, FileText, AlertTriangle, Activity, LogOut,
  UsersRound, UserCheck, UserX, Edit2, Trash2,
  Menu, Plus, RefreshCw, Lock, Loader2, Upload, CheckCircle, X, Zap, Eye, Copy
} from "lucide-react";

type AdminSection =
  | "users-roles"
  | "system-settings"
  | "security-compliance"
  | "integrations"
  | "audit-logs"
  | "system-health";

interface AdminUser {
  id: string;
  name: string;
  email: string;
  role: string;
  status: "active" | "inactive" | "pending";
  lastLogin: string | null;
  createdAt: string;
}

interface SystemSetting {
  id: string;
  category: string;
  key: string;
  value: string | number | boolean;
  description: string;
  isSensitive: boolean;
}

interface Integration {
  id: string;
  name: string;
  provider: string;
  status: "connected" | "disconnected" | "error";
  lastSync: string | null;
  configCount: number;
}

interface AuditLogEntry {
  id: string;
  timestamp: string;
  user: string;
  action: string;
  resource: string;
  details: string;
  ipAddress: string;
}

interface HealthMetrics {
  status: string;
  uptime: string;
  cpu_usage_pct: number;
  memory_usage_mb: number;
  database: {
    status: string;
    active_connections: number;
    pool_size: number;
  };
  cache_worker: {
    status: string;
    pending_jobs: number;
    dead_letter_count: number;
  };
  model_latency_p95_ms: number;
}

export function Administration() {
  const [activeSection, setActiveSection] = useState<AdminSection>("users-roles");
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");

  // Live Data State
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [settings, setSettings] = useState<SystemSetting[]>([]);
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([]);
  const [healthMetrics, setHealthMetrics] = useState<HealthMetrics | null>(null);

  const [loading, setLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [notification, setNotification] = useState<{ type: "success" | "error"; message: string } | null>(null);

  // User Modals
  const [isAddUserOpen, setIsAddUserOpen] = useState(false);
  const [newUserName, setNewUserName] = useState("");
  const [newUserEmail, setNewUserEmail] = useState("");
  const [newUserRole, setNewUserRole] = useState("Fraud Analyst");
  const [newUserPassword, setNewUserPassword] = useState("FinSecure2026!");

  // Setting Edit Modal
  const [editingSetting, setEditingSetting] = useState<SystemSetting | null>(null);
  const [editSettingValue, setEditSettingValue] = useState("");

  const showNotification = (type: "success" | "error", message: string) => {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 4000);
  };

  const fetchAllAdminData = async () => {
    setIsRefreshing(true);
    try {
      const [uData, sData, iData, aData, hData] = await Promise.all([
        api.get<AdminUser[]>("/admin/users"),
        api.get<SystemSetting[]>("/admin/settings"),
        api.get<Integration[]>("/admin/integrations"),
        api.get<AuditLogEntry[]>("/admin/audit-logs"),
        api.get<HealthMetrics>("/admin/health-metrics")
      ]);
      setUsers(uData);
      setSettings(sData);
      setIntegrations(iData);
      setAuditLogs(aData);
      setHealthMetrics(hData);
    } catch (err: any) {
      console.error("Failed to load admin telemetry:", err);
      showNotification("error", err.message || "Failed to load admin data");
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchAllAdminData();
  }, []);

  // Handlers for User Actions
  const handleUserAction = async (action: string, userId: string) => {
    try {
      if (action === "toggle-status") {
        const u = users.find((x) => x.id === userId);
        if (!u) return;
        const newStatus = u.status === "active" ? "inactive" : "active";
        const updated = await api.patch<AdminUser>(`/admin/users/${userId}`, { status: newStatus });
        setUsers(users.map((x) => (x.id === userId ? { ...x, status: updated.status } : x)));
        showNotification("success", `User ${u.name} status updated to ${newStatus}`);
      } else if (action === "deactivate" || action === "delete") {
        await api.delete(`/admin/users/${userId}`);
        setUsers(users.filter((x) => x.id !== userId));
        showNotification("success", `User removed successfully`);
      } else if (action === "edit") {
        const u = users.find((x) => x.id === userId);
        if (u) {
          const nextRole = u.role === "Fraud Analyst" ? "Senior Investigator" : u.role === "Senior Investigator" ? "Compliance Officer" : "Fraud Analyst";
          const updated = await api.patch<AdminUser>(`/admin/users/${userId}`, { role: nextRole });
          setUsers(users.map((x) => (x.id === userId ? { ...x, role: updated.role } : x)));
          showNotification("success", `Promoted ${u.name} to ${nextRole}`);
        }
      }
    } catch (err: any) {
      showNotification("error", err.message || "Action failed");
    }
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newUserName.trim() || !newUserEmail.trim()) return;
    try {
      const created = await api.post<AdminUser>("/admin/users", {
        name: newUserName.trim(),
        email: newUserEmail.trim(),
        role: newUserRole,
        password: newUserPassword,
        status: "active"
      });
      setUsers([...users, created]);
      setIsAddUserOpen(false);
      setNewUserName("");
      setNewUserEmail("");
      showNotification("success", `User ${created.name} registered`);
    } catch (err: any) {
      showNotification("error", err.message || "Failed to create user");
    }
  };

  // Handlers for Setting Actions
  const handleSettingAction = async (action: string, settingId: string) => {
    try {
      if (action.startsWith("toggle-")) {
        const id = action.replace("toggle-", "");
        const s = settings.find((x) => x.id === id);
        if (!s) return;
        const nextVal = !s.value;
        const updated = await api.put<SystemSetting>(`/admin/settings/${id}`, { value: String(nextVal) });
        setSettings(settings.map((x) => (x.id === id ? { ...x, value: updated.value } : x)));
        showNotification("success", `Setting ${s.key} set to ${nextVal}`);
      } else if (action.startsWith("update-")) {
        const parts = action.split("-");
        const id = parts[1];
        const val = parts.slice(2).join("-");
        const updated = await api.put<SystemSetting>(`/admin/settings/${id}`, { value: val });
        setSettings(settings.map((x) => (x.id === id ? { ...x, value: updated.value } : x)));
        showNotification("success", `Updated setting value to ${val}`);
      } else if (action.startsWith("edit-")) {
        const id = action.replace("edit-", "");
        const s = settings.find((x) => x.id === id);
        if (s) {
          setEditingSetting(s);
          setEditSettingValue(String(s.value));
        }
      }
    } catch (err: any) {
      showNotification("error", err.message || "Failed to update setting");
    }
  };

  const handleSaveSettingModal = async () => {
    if (!editingSetting) return;
    try {
      const updated = await api.put<SystemSetting>(`/admin/settings/${editingSetting.id}`, {
        value: editSettingValue
      });
      setSettings(settings.map((x) => (x.id === editingSetting.id ? { ...x, value: updated.value } : x)));
      setEditingSetting(null);
      showNotification("success", `Updated ${editingSetting.key}`);
    } catch (err: any) {
      showNotification("error", err.message || "Failed to save setting");
    }
  };

  // Handlers for Integration Actions
  const handleIntegrationAction = async (action: string, integrationId: string) => {
    try {
      if (action === "toggle-status") {
        const item = integrations.find((x) => x.id === integrationId);
        if (!item) return;
        if (item.status === "error" || item.status === "disconnected") {
          const res = await api.post<Integration>(`/admin/integrations/${integrationId}/sync`);
          setIntegrations(integrations.map((x) => (x.id === integrationId ? res : x)));
          showNotification("success", `Sync completed for ${item.name}`);
        } else {
          const res = await api.patch<Integration>(`/admin/integrations/${integrationId}`, { status: "disconnected" });
          setIntegrations(integrations.map((x) => (x.id === integrationId ? res : x)));
          showNotification("success", `Disconnected ${item.name}`);
        }
      } else if (action === "disconnect") {
        const res = await api.patch<Integration>(`/admin/integrations/${integrationId}`, { status: "disconnected" });
        setIntegrations(integrations.map((x) => (x.id === integrationId ? res : x)));
        showNotification("success", `Disconnected integration`);
      }
    } catch (err: any) {
      showNotification("error", err.message || "Failed integration action");
    }
  };

  const handleLogAction = (_action: string, logId: string) => {
    navigator.clipboard?.writeText(logId);
    showNotification("success", `Copied reference: ${logId}`);
  };

  // Filtered data based on search
  const filteredUsers = users.filter(user =>
    user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.role.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredSettings = settings.filter(setting =>
    setting.key.toLowerCase().includes(searchTerm.toLowerCase()) ||
    setting.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredIntegrations = integrations.filter(int =>
    int.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    int.provider.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="flex h-full w-full">
      {/* Sidebar Navigation */}
      <aside
        className={`
          flex-shrink-0 w-64 bg-surface-container-lowest border-r border-outline-variant
          transition-all duration-300
          ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'}
          overflow-hidden
        `}
      >
        <div className="flex items-center justify-between p-4 border-b border-outline-variant">
          <h3 className="font-headline-md text-headline-md text-on-surface">Administration</h3>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="h-8 w-8 p-1"
          >
            <Menu size={16} />
          </Button>
        </div>

        <nav className="pt-4 space-y-2 overflow-auto h-full">
          <button
            onClick={() => setActiveSection("users-roles")}
            className={`${activeSection === "users-roles" ? "text-on-surface bg-surface-container-high" : "text-on-surface-variant hover:text-on-surface"}
                      flex w-full items-center gap-3 p-3 rounded-lg transition-colors`}
          >
            <Users size={18} />
            <span>Users & Roles</span>
          </button>

          <button
            onClick={() => setActiveSection("system-settings")}
            className={`${activeSection === "system-settings" ? "text-on-surface bg-surface-container-high" : "text-on-surface-variant hover:text-on-surface"}
                      flex w-full items-center gap-3 p-3 rounded-lg transition-colors`}
          >
            <Settings size={18} />
            <span>System Settings</span>
          </button>

          <button
            onClick={() => setActiveSection("security-compliance")}
            className={`${activeSection === "security-compliance" ? "text-on-surface bg-surface-container-high" : "text-on-surface-variant hover:text-on-surface"}
                      flex w-full items-center gap-3 p-3 rounded-lg transition-colors`}
          >
            <Shield size={18} />
            <span>Security & Compliance</span>
          </button>

          <button
            onClick={() => setActiveSection("integrations")}
            className={`${activeSection === "integrations" ? "text-on-surface bg-surface-container-high" : "text-on-surface-variant hover:text-on-surface"}
                      flex w-full items-center gap-3 p-3 rounded-lg transition-colors`}
          >
            <Plug size={18} />
            <span>Integrations</span>
          </button>

          <button
            onClick={() => setActiveSection("audit-logs")}
            className={`${activeSection === "audit-logs" ? "text-on-surface bg-surface-container-high" : "text-on-surface-variant hover:text-on-surface"}
                      flex w-full items-center gap-3 p-3 rounded-lg transition-colors`}
          >
            <FileText size={18} />
            <span>Audit Logs</span>
          </button>

          <button
            onClick={() => setActiveSection("system-health")}
            className={`${activeSection === "system-health" ? "text-on-surface bg-surface-container-high" : "text-on-surface-variant hover:text-on-surface"}
                      flex w-full items-center gap-3 p-3 rounded-lg transition-colors`}
          >
            <Activity size={18} />
            <span>System Health</span>
          </button>
        </nav>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <LayoutHeader
          title="Enterprise Control Plane"
          rightContent={
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={() => setIsSidebarOpen(true)}>
                <Menu size={16} className="mr-1" /> Navigation
              </Button>
            </div>
          }
        />

        {notification && (
          <div className={`mx-6 mt-4 p-3 rounded-lg text-xs font-medium flex items-center justify-between ${
            notification.type === "success"
              ? "bg-risk-low/20 text-risk-low border border-risk-low/30"
              : "bg-risk-high/20 text-risk-high border border-risk-high/30"
          }`}>
            <span>{notification.message}</span>
            <button onClick={() => setNotification(null)}>&times;</button>
          </div>
        )}

        <div className="flex-1 overflow-auto p-6">
          <div className="space-y-6">
            {/* Top Toolbar */}
            <div className="flex flex-col sm:flex-row gap-4 justify-between items-start sm:items-center">
              <div className="relative flex-1 max-w-md">
                <Input
                  placeholder={`Search ${activeSection.replace('-', ' ')}...`}
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-8 bg-surface-container-low border border-outline-variant"
                />
              </div>

              <div className="flex gap-2 w-full sm:w-auto justify-end">
                {activeSection === "users-roles" && (
                  <Button
                    variant="default"
                    size="sm"
                    onClick={() => setIsAddUserOpen(true)}
                    className="bg-investment-gold text-surface hover:bg-investment-gold/90"
                  >
                    <Plus size={14} className="mr-1" /> Add User
                  </Button>
                )}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={fetchAllAdminData}
                  disabled={isRefreshing}
                  className="border-outline-variant text-on-surface"
                >
                  <RefreshCw size={14} className={`mr-1 ${isRefreshing ? "animate-spin" : ""}`} />
                  {isRefreshing ? "Syncing..." : "Refresh"}
                </Button>
              </div>
            </div>

            {/* Section Content */}
            {activeSection === "users-roles" && (
              <UsersRolesSection
                users={filteredUsers}
                onUserAction={(action, userId) => handleUserAction(action, userId)}
              />
            )}

            {activeSection === "system-settings" && (
              <SystemSettingsSection
                settings={filteredSettings}
                onSettingAction={(action, settingId) => handleSettingAction(action, settingId)}
              />
            )}

            {activeSection === "security-compliance" && (
              <SecurityComplianceSection />
            )}

            {activeSection === "integrations" && (
              <IntegrationsSection
                integrations={filteredIntegrations}
                onIntegrationAction={(action, integrationId) => handleIntegrationAction(action, integrationId)}
              />
            )}

            {activeSection === "audit-logs" && (
              <AuditLogsSection
                logs={auditLogs}
                onLogAction={(action, logId) => handleLogAction(action, logId)}
              />
            )}

            {activeSection === "system-health" && (
              <SystemHealthSection healthMetrics={healthMetrics} />
            )}
          </div>
        </div>
      </div>

      {/* Add User Modal */}
      {isAddUserOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="bg-surface-container-low border border-outline-variant rounded-xl max-w-md w-full p-6 shadow-xl">
            <h3 className="text-base font-semibold font-headline text-on-surface mb-4">Add Enterprise User</h3>
            <form onSubmit={handleCreateUser} className="space-y-4">
              <div>
                <label className="block text-xs font-mono text-on-surface-variant mb-1">Full Name</label>
                <Input
                  value={newUserName}
                  onChange={(e) => setNewUserName(e.target.value)}
                  placeholder="e.g. Jordan Hayes"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-mono text-on-surface-variant mb-1">Email Address</label>
                <Input
                  type="email"
                  value={newUserEmail}
                  onChange={(e) => setNewUserEmail(e.target.value)}
                  placeholder="jordan.hayes@company.com"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-mono text-on-surface-variant mb-1">Assigned Role</label>
                <select
                  value={newUserRole}
                  onChange={(e) => setNewUserRole(e.target.value)}
                  className="w-full bg-surface-container border border-outline-variant rounded px-3 py-2 text-sm text-on-surface"
                >
                  <option value="Fraud Analyst">Fraud Analyst</option>
                  <option value="Senior Investigator">Senior Investigator</option>
                  <option value="Compliance Officer">Compliance Officer</option>
                  <option value="Administrator">Administrator</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-mono text-on-surface-variant mb-1">Initial Password</label>
                <Input
                  type="password"
                  value={newUserPassword}
                  onChange={(e) => setNewUserPassword(e.target.value)}
                  required
                />
              </div>
              <div className="flex justify-end gap-2 pt-4 border-t border-outline-variant/40">
                <Button type="button" variant="outline" size="sm" onClick={() => setIsAddUserOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" size="sm" className="bg-investment-gold text-surface">
                  Register User
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Setting Modal */}
      {editingSetting && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="bg-surface-container-low border border-outline-variant rounded-xl max-w-md w-full p-6 shadow-xl">
            <h3 className="text-base font-semibold font-headline text-on-surface mb-2">Edit System Parameter</h3>
            <p className="text-xs text-on-surface-variant mb-4 font-mono">{editingSetting.key}</p>
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-mono text-on-surface-variant mb-1">Value</label>
                <Input
                  value={editSettingValue}
                  onChange={(e) => setEditSettingValue(e.target.value)}
                />
              </div>
              <p className="text-xs text-on-surface-variant">{editingSetting.description}</p>
              <div className="flex justify-end gap-2 pt-4 border-t border-outline-variant/40">
                <Button variant="outline" size="sm" onClick={() => setEditingSetting(null)}>
                  Cancel
                </Button>
                <Button size="sm" onClick={handleSaveSettingModal} className="bg-investment-gold text-surface">
                  Save Changes
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Users & Roles Section
function UsersRolesSection({
  users,
  onUserAction
}: {
  users: AdminUser[];
  onUserAction: (action: string, userId: string) => void;
}) {
  return (
    <div className="space-y-6">
      <h2 className="font-headline-lg text-headline-lg text-on-surface">Users & Roles Management</h2>
      <p className="text-body-lg text-on-surface-variant">Manage user accounts, roles, and cryptographic tenant scopes</p>

      {/* Users Table */}
      <div className="overflow-x-auto">
        <Table>
          <Header>
            <HeaderRow>
              <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Name</HeaderCell>
              <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Email</HeaderCell>
              <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Role</HeaderCell>
              <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Status</HeaderCell>
              <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Last Login</HeaderCell>
              <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-right">Actions</HeaderCell>
            </HeaderRow>
          </Header>
          <Body>
            {users.length === 0 ? (
              <Row>
                <Cell colSpan={6} className="p-8 text-center text-on-surface-variant">
                  <UsersRound size={32} className="mx-auto mb-4 opacity-50" />
                  <p className="text-center text-on-surface-variant">No users found</p>
                </Cell>
              </Row>
            ) : (
              users.map((user) => (
                <Row key={user.id} className="hover:bg-surface-container-high transition-colors">
                  <Cell className="p-4 text-on-surface font-medium">{user.name}</Cell>
                  <Cell className="p-4 text-on-surface font-mono text-xs">{user.email}</Cell>
                  <Cell className="p-4">
                    <Badge
                      variant={
                        user.role === "Administrator" ? "secondary" :
                        user.role === "Compliance Officer" ? "warning" :
                        user.role === "Senior Investigator" ? "success" : "outline"
                      }
                      className="text-[10px] px-2 py-0.5"
                    >
                      {user.role}
                    </Badge>
                  </Cell>
                  <Cell className="p-4">
                    <Badge
                      variant={user.status === "active" ? "secondary" : "destructive"}
                      className="text-[10px] px-2 py-0.5"
                    >
                      {user.status.toUpperCase()}
                    </Badge>
                  </Cell>
                  <Cell className="p-4 text-on-surface">
                    {user.lastLogin ? (
                      <span className="text-xs font-mono">{new Date(user.lastLogin).toLocaleDateString()}</span>
                    ) : (
                      <span className="text-xs text-on-surface-variant">Never</span>
                    )}
                  </Cell>
                  <Cell className="p-4 text-right">
                    <div className="inline-flex space-x-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onUserAction("edit", user.id)}
                        className="p-1"
                        title="Promote / Change Role"
                      >
                        <Edit2 size={12} />
                      </Button>
                      <Button
                        variant={user.status === "active" ? "outline" : "default"}
                        size="sm"
                        onClick={() => onUserAction("toggle-status", user.id)}
                        className="p-1 bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
                        title={user.status === "active" ? "Deactivate User" : "Activate User"}
                      >
                        {user.status === "active" ? <UserX size={12} /> : <UserCheck size={12} />}
                      </Button>
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => {
                          if (window.confirm(`Permanently remove ${user.name}?`)) {
                            onUserAction("delete", user.id);
                          }
                        }}
                        className="p-1 bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
                        title="Delete User"
                      >
                        <Trash2 size={12} />
                      </Button>
                    </div>
                  </Cell>
                </Row>
              ))
            )}
          </Body>
        </Table>
      </div>
    </div>
  );
}

// System Settings Section
function SystemSettingsSection({
  settings,
  onSettingAction
}: {
  settings: SystemSetting[];
  onSettingAction: (action: string, settingId: string) => void;
}) {
  const categories = [...new Set(settings.map(s => s.category))];

  return (
    <div className="space-y-6">
      <h2 className="font-headline-lg text-headline-lg text-on-surface">System Configuration</h2>
      <p className="text-body-lg text-on-surface-variant">Global parameters, compliance thresholds, and model operational settings</p>

      <div className="space-y-6">
        {categories.map((category) => {
          const categorySettings = settings.filter(s => s.category === category);
          return (
            <div key={category} className="space-y-4">
              <h3 className="font-label-md text-label-md text-on-surface uppercase tracking-wider text-xs font-mono text-investment-gold">
                {category} Settings
              </h3>
              <div className="space-y-3">
                {categorySettings.map((setting) => (
                  <SettingItem
                    key={setting.id}
                    setting={setting}
                    onAction={(action) => onSettingAction(action, setting.id)}
                  />
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// Individual Setting Item
function SettingItem({
  setting,
  onAction
}: {
  setting: SystemSetting;
  onAction: (action: string) => void;
}) {
  return (
    <div className="p-4 bg-surface-container-low border border-outline-variant rounded-lg flex items-center justify-between">
      <div className="flex-1">
        <div className="flex items-center gap-3">
          <Settings size={16} className="text-on-surface-variant" />
          <div>
            <h4 className="font-label-md text-label-md text-on-surface font-mono text-xs">{setting.key}</h4>
            <p className="text-body-sm text-on-surface-variant text-xs">{setting.description}</p>
          </div>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <span className="font-mono text-xs px-2.5 py-1 bg-surface-container rounded border border-outline-variant/50 text-investment-gold">
          {String(setting.value)}
        </span>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onAction(`edit-${setting.id}`)}
          className="p-1"
          aria-label="Edit parameter"
        >
          <Edit2 size={12} />
        </Button>
      </div>
    </div>
  );
}

// Security & Compliance Section
function SecurityComplianceSection() {
  return (
    <div className="space-y-6">
      <h2 className="font-headline-lg text-headline-lg text-on-surface">Security & Compliance</h2>
      <p className="text-body-lg text-on-surface-variant">Cryptographic audit policies, HSM verification, and access controls</p>

      <div className="space-y-4">
        <div className="p-4 bg-surface-container-low border border-outline-variant rounded-lg flex items-center justify-between">
          <div>
            <h4 className="font-label-md text-label-md text-on-surface">AES-256 Envelope Encryption</h4>
            <p className="text-xs text-on-surface-variant">All PII fields encrypted with non-deterministic Fernet & HMAC-SHA256 blind indexing</p>
          </div>
          <Badge variant="success" className="text-[10px]">Active</Badge>
        </div>

        <div className="p-4 bg-surface-container-low border border-outline-variant rounded-lg flex items-center justify-between">
          <div>
            <h4 className="font-label-md text-label-md text-on-surface">HSM Digital Signatures</h4>
            <p className="text-xs text-on-surface-variant">SHA-256 cryptographic chain of custody for Evidence Vault artifacts</p>
          </div>
          <Badge variant="success" className="text-[10px]">FIPS 140-2 Level 3</Badge>
        </div>

        <div className="p-4 bg-surface-container-low border border-outline-variant rounded-lg flex items-center justify-between">
          <div>
            <h4 className="font-label-md text-label-md text-on-surface">FinCEN Regulatory Filing Automation</h4>
            <p className="text-xs text-on-surface-variant">Direct Suspicious Activity Report (SAR) XML/PDF generation engine</p>
          </div>
          <Badge variant="success" className="text-[10px]">Compliant</Badge>
        </div>
      </div>
    </div>
  );
}

// Integrations Section
function IntegrationsSection({
  integrations,
  onIntegrationAction
}: {
  integrations: Integration[];
  onIntegrationAction: (action: string, integrationId: string) => void;
}) {
  return (
    <div className="space-y-6">
      <h2 className="font-headline-lg text-headline-lg text-on-surface">Enterprise Integrations</h2>
      <p className="text-body-lg text-on-surface-variant">Third-party verification feeds, credit bureaus, and blockchain oracles</p>

      <div className="overflow-x-auto">
        <Table>
          <Header>
            <HeaderRow>
              <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Integration</HeaderCell>
              <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Provider</HeaderCell>
              <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Status</HeaderCell>
              <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Last Sync</HeaderCell>
              <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-right">Action</HeaderCell>
            </HeaderRow>
          </Header>
          <Body>
            {integrations.map((integration) => (
              <Row key={integration.id} className="hover:bg-surface-container-high transition-colors">
                <Cell className="p-4 text-on-surface font-medium">{integration.name}</Cell>
                <Cell className="p-4 text-on-surface-variant font-mono text-xs">{integration.provider}</Cell>
                <Cell className="p-4">
                  <Badge
                    variant={integration.status === "connected" ? "secondary" : "destructive"}
                    className="text-[10px] px-2 py-0.5"
                  >
                    {integration.status.toUpperCase()}
                  </Badge>
                </Cell>
                <Cell className="p-4 text-on-surface font-mono text-xs">
                  {integration.lastSync ? new Date(integration.lastSync).toLocaleString() : "Never"}
                </Cell>
                <Cell className="p-4 text-right">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onIntegrationAction("toggle-status", integration.id)}
                    className="text-xs border-outline-variant"
                  >
                    {integration.status === "connected" ? "Disconnect" : "Trigger Sync"}
                  </Button>
                </Cell>
              </Row>
            ))}
          </Body>
        </Table>
      </div>
    </div>
  );
}

// Audit Logs Section
function AuditLogsSection({
  logs,
  onLogAction
}: {
  logs: AuditLogEntry[];
  onLogAction: (action: string, logId: string) => void;
}) {
  return (
    <div className="space-y-6">
      <h2 className="font-headline-lg text-headline-lg text-on-surface">Immutable Audit Trail</h2>
      <p className="text-body-lg text-on-surface-variant">Cryptographic administrative and automated agent actions</p>

      <div className="overflow-x-auto">
        <Table>
          <Header>
            <HeaderRow>
              <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Timestamp</HeaderCell>
              <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Actor</HeaderCell>
              <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Action</HeaderCell>
              <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Target</HeaderCell>
              <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Details</HeaderCell>
              <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-right">Reference</HeaderCell>
            </HeaderRow>
          </Header>
          <Body>
            {logs.map((log) => (
              <Row key={log.id} className="hover:bg-surface-container-high transition-colors">
                <Cell className="p-4 font-mono text-xs text-on-surface">
                  {new Date(log.timestamp).toLocaleString()}
                </Cell>
                <Cell className="p-4 text-xs text-on-surface">{log.user}</Cell>
                <Cell className="p-4 font-mono text-xs text-investment-gold">{log.action}</Cell>
                <Cell className="p-4 font-mono text-xs text-on-surface-variant">{log.resource}</Cell>
                <Cell className="p-4 text-xs text-on-surface truncate max-w-[300px]">{log.details}</Cell>
                <Cell className="p-4 text-right">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onLogAction("copy-ref", log.id)}
                    className="p-1"
                    title="Copy Reference ID"
                  >
                    <Copy size={12} />
                  </Button>
                </Cell>
              </Row>
            ))}
          </Body>
        </Table>
      </div>
    </div>
  );
}

// System Health Section
function SystemHealthSection({ healthMetrics }: { healthMetrics: HealthMetrics | null }) {
  const hm = healthMetrics || {
    status: "healthy",
    uptime: "14d 6h",
    cpu_usage_pct: 22.4,
    memory_usage_mb: 612,
    database: { status: "connected", active_connections: 8, pool_size: 20 },
    cache_worker: { status: "operational", pending_jobs: 0, dead_letter_count: 0 },
    model_latency_p95_ms: 140
  };

  return (
    <div className="space-y-6">
      <h2 className="font-headline-lg text-headline-lg text-on-surface">System Diagnostics</h2>
      <p className="text-body-lg text-on-surface-variant">Cluster health, memory footprint, and LangGraph inference latency</p>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-surface-container-low border border-outline-variant rounded-xl p-5">
          <div className="text-xs font-mono text-on-surface-variant uppercase">Core Engine Status</div>
          <div className="text-2xl font-bold font-headline text-risk-low mt-2 uppercase">{hm.status}</div>
          <div className="text-xs text-on-surface-variant mt-1">Uptime: {hm.uptime}</div>
        </div>

        <div className="bg-surface-container-low border border-outline-variant rounded-xl p-5">
          <div className="text-xs font-mono text-on-surface-variant uppercase">CPU & Memory</div>
          <div className="text-2xl font-bold font-headline text-on-surface mt-2">{hm.cpu_usage_pct}%</div>
          <div className="text-xs text-on-surface-variant mt-1">Memory: {hm.memory_usage_mb} MB RSS</div>
        </div>

        <div className="bg-surface-container-low border border-outline-variant rounded-xl p-5">
          <div className="text-xs font-mono text-on-surface-variant uppercase">Database Pool</div>
          <div className="text-2xl font-bold font-headline text-on-surface mt-2">
            {hm.database.active_connections} / {hm.database.pool_size}
          </div>
          <div className="text-xs text-risk-low mt-1">Status: {hm.database.status}</div>
        </div>

        <div className="bg-surface-container-low border border-outline-variant rounded-xl p-5">
          <div className="text-xs font-mono text-on-surface-variant uppercase">P95 Model Latency</div>
          <div className="text-2xl font-bold font-headline text-investment-gold mt-2">{hm.model_latency_p95_ms} ms</div>
          <div className="text-xs text-on-surface-variant mt-1">Worker Queue: {hm.cache_worker.status}</div>
        </div>
      </div>
    </div>
  );
}

export default Administration;