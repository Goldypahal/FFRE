import { useState } from "react";
import { Header as LayoutHeader } from "../../components/layout/Header";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../../components/ui/Select";
import { Checkbox } from "../../components/ui/Checkbox";
import { Badge } from "../../components/ui/Badge";
import { Table, TableBody, Cell, HeaderCell, HeaderRow, Header, Body, Row } from "../../components/ui/Table";
import {
  Users, Settings, Shield, Plug, FileText, AlertTriangle, Activity, Bell, LogOut,
  Mail, Share2, UsersRound, UserPlus, UserCheck, UserX, Edit2, Trash2, Clock,
  Menu, Plus, RefreshCw, Lock, Loader2, Upload, CheckCircle, X, Zap, Eye, Copy, Power, Database, Cpu, HardDrive
} from "lucide-react";

// Admin section types
type AdminSection =
  | "users-roles"
  | "system-settings"
  | "security-compliance"
  | "integrations"
  | "audit-logs"
  | "system-health";

// User type for management
interface AdminUser {
  id: string;
  name: string;
  email: string;
  role: string;
  status: "active" | "inactive" | "pending";
  lastLogin: string | null;
  createdAt: string;
}

// System settings type
interface SystemSetting {
  id: string;
  category: string;
  key: string;
  value: string | number | boolean;
  description: string;
  isSensitive: boolean;
}

// Integration type
interface Integration {
  id: string;
  name: string;
  provider: string;
  status: "connected" | "disconnected" | "error";
  lastSync: string | null;
  configCount: number;
}

// Audit log entry
interface AuditLogEntry {
  id: string;
  timestamp: string;
  user: string;
  action: string;
  resource: string;
  details: string;
  ipAddress: string;
}

// Mock data for admin sections
const MOCK_USERS: AdminUser[] = [
  {
    id: "user-001",
    name: "Alex Johnson",
    email: "alex.johnson@company.com",
    role: "Fraud Analyst",
    status: "active",
    lastLogin: "2024-01-15T10:30:00Z",
    createdAt: "2023-06-15T09:00:00Z"
  },
  {
    id: "user-002",
    name: "Maria Garcia",
    email: "maria.garcia@company.com",
    role: "Senior Investigator",
    status: "active",
    lastLogin: "2024-01-14T16:45:00Z",
    createdAt: "2023-05-20T14:22:00Z"
  },
  {
    id: "user-003",
    name: "David Chen",
    email: "david.chen@company.com",
    role: "Compliance Officer",
    status: "active",
    lastLogin: "2024-01-13T09:15:00Z",
    createdAt: "2023-07-01T11:30:00Z"
  },
  {
    id: "user-004",
    name: "System Admin",
    email: "admin@company.com",
    role: "Administrator",
    status: "active",
    lastLogin: "2024-01-15T08:00:00Z",
    createdAt: "2023-01-10T07:00:00Z"
  }
];

const MODULE_SETTINGS = [
  {
    id: "setting-001",
    category: "general",
    key: "company_name",
    value: "FinSecure Inc.",
    description: "Company name displayed in the application",
    isSensitive: false
  },
  {
    id: "setting-002",
    category: "general",
    key: "session_timeout",
    value: 30,
    description: "Session timeout in minutes",
    isSensitive: false
  },
  {
    id: "setting-003",
    category: "security",
    key: "password_min_length",
    value: 8,
    description: "Minimum password length requirement",
    isSensitive: false
  },
  {
    id: "setting-004",
    category: "security",
    key: "mfa_required",
    value: true,
    description: "Require multi-factor authentication for all users",
    isSensitive: false
  },
  {
    id: "setting-005",
    category: "integrations",
    key: "api_rate_limit",
    value: 1000,
    description: "API requests per minute limit",
    isSensitive: false
  }
];

const MOCK_INTEGRATIONS: Integration[] = [
  {
    id: "int-001",
    name: "Salesforce CRM",
    provider: "salesforce",
    status: "connected",
    lastSync: "2024-01-15T10:30:00Z",
    configCount: 5
  },
  {
    id: "int-002",
    name: "Experian Credit Bureau",
    provider: "experian",
    status: "connected",
    lastSync: "2024-01-15T09:15:00Z",
    configCount: 3
  },
  {
    id: "int-003",
    name: "Dark Web Monitor",
    provider: "darkweb-api",
    status: "error",
    lastSync: "2024-01-14T22:45:00Z",
    configCount: 2
  }
];

const MOCK_AUDIT_LOGS: AuditLogEntry[] = [
  {
    id: "log-001",
    timestamp: "2024-01-15T10:30:00Z",
    user: "alex.johnson@company.com",
    action: "investigation.created",
    resource: "INV-78491",
    details: "Created new investigation for transaction T-78491",
    ipAddress: "192.168.1.100"
  },
  {
    id: "log-002",
    timestamp: "2024-01-15T10:25:00Z",
    user: "maria.garcia@company.com",
    action: "user.role.updated",
    resource: "user-003",
    details: "Changed role from Investigator to Senior Investigator",
    ipAddress: "192.168.1.105"
  },
  {
    id: "log-003",
    timestamp: "2024-01-15T10:20:00Z",
    user: "System",
    action: "integration.sync.completed",
    resource: "int-001",
    details: "Successfully synced 124 records from Salesforce CRM",
    ipAddress: "127.0.0.1"
  }
];

export function Administration() {
  const handleUserAction = (action: string, userId: string) => {
    alert(`User action "${action}" on user ID: ${userId}`);
  };

  const handleSettingAction = (action: string, settingId: string) => {
    alert(`Setting action "${action}" on setting ID: ${settingId}`);
  };

  const handleIntegrationAction = (action: string, integrationId: string) => {
    alert(`Integration action "${action}" on integration ID: ${integrationId}`);
  };

  const handleLogAction = (action: string, logId: string) => {
    alert(`Log action "${action}" on log ID: ${logId}`);
  };
  const [activeSection, setActiveSection] = useState<AdminSection>("users-roles");
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");

  // Filtered data based on search (simplified)
  const filteredUsers = MOCK_USERS.filter(user =>
    user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.role.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredSettings = MODULE_SETTINGS.filter(setting =>
    setting.key.toLowerCase().includes(searchTerm.toLowerCase()) ||
    setting.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredIntegrations = MOCK_INTEGRATIONS.filter(int =>
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

        <div className="p-4 border-t border-outline-variant mt-auto">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              // Logout functionality
              alert("Logging out...");
            }}
            className="w-full bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
          >
            <LogOut size={16} className="mr-2" /> Logout
          </Button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <LayoutHeader
          title="Administration"
          rightContent={
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={() => setIsSidebarOpen(true)}>
                <Menu size={16} className="mr-1" /> Navigation
              </Button>
              <Button
                variant="default"
                size="sm"
                onClick={() => {
                  // Global actions would go here
                  alert("Global admin actions");
                }}
              >
                <AlertTriangle size={16} className="mr-2" /> Alerts
              </Button>
            </div>
          }
        />

        <div className="flex-1 overflow-auto p-6">
          <div className="space-y-6">
            {/* Search and Actions Bar */}
            <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-4">
              <div className="flex-1 md:auto mb-4 md:mb-0">
                <Input
                  placeholder="Search users, settings, logs..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full bg-surface-container-low border border-outline-variant"
                />
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    // Add new user/item based on section
                    switch (activeSection) {
                      case "users-roles":
                        alert("Add new user form would open");
                        break;
                      case "system-settings":
                        alert("Add new setting form would open");
                        break;
                      case "security-compliance":
                        alert("Add new policy form would open");
                        break;
                      case "integrations":
                        alert("Add new integration wizard would open");
                        break;
                      case "audit-logs":
                        alert("Export logs option would open");
                        break;
                      case "system-health":
                        alert("Refresh health checks");
                        break;
                    }
                  }}
                  className="bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
                >
                  <Plus size={14} className="mr-1" /> Add New
                </Button>
                <Button
                  variant="default"
                  size="sm"
                  onClick={() => {
                    // Refresh data
                    alert("Refreshing data...");
                  }}
                  className="bg-investment-gold text-surface hover:bg-investment-gold/90"
                >
                  <RefreshCw size={16} /> Refresh
                </Button>
              </div>
            </div>

            {/* Section Content */}
            {activeSection === "users-roles" && (
              <UsersRolesSection
                users={filteredUsers}
                onUserAction={(action, userId) => handleUserAction(action, userId)}
                onSearch={(term) => setSearchTerm(term)}
              />
            )}

            {activeSection === "system-settings" && (
              <SystemSettingsSection
                settings={filteredSettings}
                onSettingAction={(action, settingId) => handleSettingAction(action, settingId)}
                onSearch={(term) => setSearchTerm(term)}
              />
            )}

            {activeSection === "security-compliance" && (
              <SecurityComplianceSection
                onSearch={(term) => setSearchTerm(term)}
              />
            )}

            {activeSection === "integrations" && (
              <IntegrationsSection
                integrations={filteredIntegrations}
                onIntegrationAction={(action, integrationId) => handleIntegrationAction(action, integrationId)}
                onSearch={(term) => setSearchTerm(term)}
              />
            )}

            {activeSection === "audit-logs" && (
              <AuditLogsSection
                logs={MOCK_AUDIT_LOGS}
                onLogAction={(action, logId) => handleLogAction(action, logId)}
                onSearch={(term) => setSearchTerm(term)}
              />
            )}

            {activeSection === "system-health" && (
              <SystemHealthSection
                onSearch={(term) => setSearchTerm(term)}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// Users & Roles Section
function UsersRolesSection({
  users,
  onUserAction,
  onSearch
}: {
  users: AdminUser[];
  onUserAction: (action: string, userId: string) => void;
  onSearch: (term: string) => void;
}) {
  return (
    <div className="space-y-6">
      <h2 className="font-headline-lg text-headline-lg text-on-surface">Users & Roles Management</h2>
      <p className="text-body-lg text-on-surface-variant">Manage user accounts, roles, and permissions</p>

      {/* Users Table */}
      <div className="overflow-x-auto">
        <Table>
          <Header>
            <HeaderRow>
              <HeaderCell className="w-4 p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">
                <Checkbox
                  // Select all would go here
                  aria-label="Select all users"
                  className="bg-transparent border-none focus:ring-0"
                />
              </HeaderCell>
              <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Name</HeaderCell>
              <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Email</HeaderCell>
              <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Role</HeaderCell>
              <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Status</HeaderCell>
              <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Last Login</HeaderCell>
              <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left text-right">Actions</HeaderCell>
            </HeaderRow>
          </Header>
          <Body>
            {users.length === 0 ? (
              <Row>
                <Cell colSpan={8} className="p-8 text-center text-on-surface-variant">
                  <UsersRound size={32} className="mx-auto mb-4 opacity-50" />
                  <p className="text-center text-on-surface-variant">No users found</p>
                </Cell>
              </Row>
            ) : (
              users.map((user) => (
                <Row key={user.id} className="hover:bg-surface-container-high transition-colors">
                  <Cell className="w-4 p-4">
                    <Checkbox
                      checked={false} // Selection state would be managed
                      onChange={(checked) => {}}
                      onClick={(e) => e.stopPropagation()}
                      aria-label={`Select ${user.name}`}
                      className="bg-transparent border-none focus:ring-0"
                    />
                  </Cell>
                  <Cell className="p-4 text-on-surface">{user.name}</Cell>
                  <Cell className="p-4 text-on-surface">{user.email}</Cell>
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
                      variant={user.status === "active" ? "secondary" : user.status === "inactive" ? "destructive" : "warning"}
                      className="text-[10px] px-2 py-0.5"
                    >
                      {user.status.charAt(0).toUpperCase() + user.status.slice(1)}
                    </Badge>
                  </Cell>
                  <Cell className="p-4 text-on-surface">
                    {user.lastLogin ? (
                      <span className="text-xs">{new Date(user.lastLogin).toLocaleDateString()}</span>
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
                      >
                        <Edit2 size={12} />
                      </Button>
                      <Button
                        variant={user.status === "active" ? "outline" : "default"}
                        size="sm"
                        onClick={() => onUserAction("toggle-status", user.id)}
                        className="p-1 bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
                      >
                        {user.status === "active" ? (
                          <UserX size={12} />
                        ) : (
                          <UserCheck size={12} />
                        )}
                      </Button>
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => {
                          if (window.confirm(`Deactivate user ${user.name}? This action cannot be undone.`)) {
                            onUserAction("deactivate", user.id);
                          }
                        }}
                        className="p-1 bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
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

      {/* User Actions Bar */}
      <div className="flex gap-2 mt-4">
        <Button
          variant="outline"
          size="sm"
          onClick={() => onUserAction("bulk-action", "deactivate")}
          className="bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
        >
          <UserX size={14} /> Deactivate Selected
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onUserAction("bulk-action", "reset-password")}
          className="bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
        >
          <Lock size={14} /> Reset Password
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onUserAction("bulk-action", "export")}
          className="bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
        >
          <FileText size={14} /> Export List
        </Button>
      </div>
    </div>
  );
}

// System Settings Section
function SystemSettingsSection({
  settings,
  onSettingAction,
  onSearch
}: {
  settings: SystemSetting[];
  onSettingAction: (action: string, settingId: string) => void;
  onSearch: (term: string) => void;
}) {
  return (
    <div className="space-y-6">
      <h2 className="font-headline-lg text-headline-lg text-on-surface">System Settings</h2>
      <p className="text-body-lg text-on-surface-variant">Configure system-wide settings and preferences</p>

      {/* Settings by Category */}
      <div className="space-y-6">
        {[...new Set(settings.map(s => s.category))].map((category) => {
          const categorySettings = settings.filter(s => s.category === category);
          return (
            <div key={category} className="space-y-4">
              <h3 className="font-label-md text-label-md text-on-surface">{category.charAt(0).toUpperCase() + category.slice(1)} Settings</h3>
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

      {/* Settings Actions */}
      <div className="flex gap-2 mt-4">
        <Button
          variant="outline"
          size="sm"
          onClick={() => onSettingAction("reset-defaults", "")}
          className="bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
        >
          <Loader2 size={14} className="mr-1" /> Reset to Defaults
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onSettingAction("export-config", "")}
          className="bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
        >
          <FileText size={14} className="mr-1" /> Export Configuration
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onSettingAction("import-config", "")}
          className="bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
        >
          <Upload size={14} className="mr-1" /> Import Configuration
        </Button>
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
    <div className="p-4 bg-surface-container-low border border-outline-variant rounded-lg">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <Settings size={16} className="text-on-surface-variant" />
            <div>
              <h4 className="font-label-md text-label-md text-on-surface">{setting.key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</h4>
              <p className="text-body-sm text-on-surface-variant">{setting.description}</p>
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          {typeof setting.value === "boolean" && (
            <Checkbox
              checked={setting.value as boolean}
              onChange={(checked) => onAction(`toggle-${setting.id}`)}
              aria-label={`Toggle ${setting.key}`}
              className="bg-surface-container-low border border-outline-variant"
            />
          )}
          {typeof setting.value === "number" && (
            <Input
              type="number"
              value={(setting.value as number).toString()}
              onChange={(e) => {
                const value = parseInt(e.target.value) || 0;
                onAction(`update-${setting.id}-${value}`);
              }}
              className="w-24 bg-surface-container-low border border-outline-variant text-center"
            />
          )}
          {typeof setting.value === "string" && (
            <Input
              value={setting.value as string}
              onChange={(e) => onAction(`update-${setting.id}-${e.target.value}`)}
              className="w-32 bg-surface-container-low border border-outline-variant"
            />
          )}
          {!["boolean", "number", "string"].includes(typeof setting.value) && (
            <span className="text-xs text-on-surface-variant">{String(setting.value)}</span>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onAction(`edit-${setting.id}`)}
            className="p-1"
            aria-label="Edit setting"
          >
            <Edit2 size={12} />
          </Button>
        </div>
      </div>
    </div>
  );
}

// Security & Compliance Section
function SecurityComplianceSection({
  onSearch
}: {
  onSearch: (term: string) => void;
}) {
  return (
    <div className="space-y-6">
      <h2 className="font-headline-lg text-headline-lg text-on-surface">Security & Compliance</h2>
      <p className="text-body-lg text-on-surface-variant">Manage security policies, compliance settings, and access controls</p>

      {/* Security Policies */}
      <div className="space-y-6">
        <div className="space-y-4">
          <h3 className="font-label-md text-label-md text-on-surface">Authentication Policies</h3>
          <PolicyToggle
            id="mfa-required"
            label="Multi-Factor Authentication Required"
            description="Require MFA for all user logins"
            checked={true}
            onToggle={(checked) => console.log("MFA required:", checked)}
            className="bg-surface-container-low border border-outline-variant rounded-lg"
          />
          <PolicyToggle
            id="sso-enforced"
            label="Single Sign-On Enforced"
            description="Require all users to authenticate via SSO"
            checked={false}
            onToggle={(checked) => console.log("SSO enforced:", checked)}
            className="bg-surface-container-low border border-outline-variant rounded-lg"
          />
          <PolicyToggle
            id="password-policy"
            label="Enhanced Password Policy"
            description="Require special characters and regular rotation"
            checked={true}
            onToggle={(checked) => console.log("Enhanced password policy:", checked)}
            className="bg-surface-container-low border border-outline-variant rounded-lg"
          />
        </div>

        <div className="space-y-4">
          <h3 className="font-label-md text-label-md text-on-surface">Data Protection</h3>
          <PolicyToggle
            id="data-encryption"
            label="Data Encryption at Rest"
            description="Encrypt all stored data using AES-256"
            checked={true}
            onToggle={(checked) => console.log("Data encryption:", checked)}
            className="bg-surface-container-low border border-outline-variant rounded-lg"
          />
          <PolicyToggle
            id="audit-logging"
            label="Comprehensive Audit Logging"
            description="Log all user and system actions for compliance"
            checked={true}
            onToggle={(checked) => console.log("Audit logging:", checked)}
            className="bg-surface-container-low border border-outline-variant rounded-lg"
          />
          <PolicyToggle
            id="gdpr-compliance"
            label="GDPR Compliance Mode"
            description="Enable data subject rights and retention controls"
            checked={false}
            onToggle={(checked) => console.log("GDPR compliance:", checked)}
            className="bg-surface-container-low border border-outline-variant rounded-lg"
          />
        </div>

        <div className="space-y-4">
          <h3 className="font-label-md text-label-md text-on-surface">Access Controls</h3>
          <PermissionMatrix />
        </div>
      </div>

      {/* Compliance Reports */}
      <div className="mt-6">
        <h3 className="font-label-md text-label-md text-on-surface">Compliance Reports</h3>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              alert("Generating SOC 2 report...");
            }}
            className="bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
          >
            <FileText size={14} className="mr-1" /> SOC 2 Report
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              alert("Generating GDPR compliance report...");
            }}
            className="bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
          >
            <FileText size={14} className="mr-1" /> GDPR Report
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              alert("Generating ISO 27001 report...");
            }}
            className="bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
          >
            <FileText size={14} className="mr-1" /> ISO 27001 Report
          </Button>
        </div>
      </div>
    </div>
  );
}

// Policy Toggle Component
function PolicyToggle({
  id,
  label,
  description,
  checked,
  onToggle,
  className
}: {
  id: string;
  label: string;
  description: string;
  checked: boolean;
  onToggle: (checked: boolean) => void;
  className?: string;
}) {
  return (
    <label className={`${className} flex items-start gap-3 p-4 cursor-pointer hover:bg-surface-container-high transition-colors`}>
      <Checkbox
        checked={checked}
        onChange={(val) => onToggle(val)}
        onClick={(e) => e.stopPropagation()}
        aria-label={label}
        className="bg-surface-container-low border border-outline-variant"
      />
      <div className="flex-1">
        <h4 className="font-label-md text-label-md text-on-surface">{label}</h4>
        <p className="text-body-sm text-on-surface-variant">{description}</p>
      </div>
    </label>
  );
}

// Permission Matrix (simplified)
function PermissionMatrix() {
  return (
    <div className="mt-4 p-4 bg-surface-container-low border border-outline-variant rounded-lg">
      <h4 className="font-label-md text-label-md text-on-surface mb-3">Role-Based Access Control Matrix</h4>
      <div className="overflow-x-auto">
        <Table>
          <Header>
            <HeaderRow>
              <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Permissions</HeaderCell>
              <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-center">Administrator</HeaderCell>
              <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-center">Compliance Officer</HeaderCell>
              <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-center">Senior Investigator</HeaderCell>
              <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-center">Fraud Analyst</HeaderCell>
              <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-center">Viewer</HeaderCell>
            </HeaderRow>
          </Header>
          <Body>
            <Row className="hover:bg-surface-container-high transition-colors">
              <Cell className="p-4 font-label-md text-label-md text-on-surface">View Investigations</Cell>
              <Cell className="p-4 text-on-surface"><CheckCircle size={14} className="text-emerald-500" /></Cell>
              <Cell className="p-4 text-on-surface"><CheckCircle size={14} className="text-emerald-500" /></Cell>
              <Cell className="p-4 text-on-surface"><CheckCircle size={14} className="text-emerald-500" /></Cell>
              <Cell className="p-4 text-on-surface"><CheckCircle size={14} className="text-emerald-500" /></Cell>
              <Cell className="p-4 text-on-surface"><CheckCircle size={14} className="text-emerald-500" /></Cell>
            </Row>
            <Row className="hover:bg-surface-container-high transition-colors">
              <Cell className="p-4 font-label-md text-label-md text-on-surface">Create Investigations</Cell>
              <Cell className="p-4 text-on-surface"><CheckCircle size={14} className="text-emerald-500" /></Cell>
              <Cell className="p-4 text-on-surface"><CheckCircle size={14} className="text-emerald-500" /></Cell>
              <Cell className="p-4 text-on-surface"><CheckCircle size={14} className="text-emerald-500" /></Cell>
              <Cell className="p-4 text-on-surface"><CheckCircle size={14} className="text-emerald-500" /></Cell>
              <Cell className="p-4 text-on-surface"><CheckCircle size={14} className="text-emerald-500" /></Cell>
            </Row>
            <Row className="hover:bg-surface-container-high transition-colors">
              <Cell className="p-4 font-label-md text-label-md text-on-surface">Delete Evidence</Cell>
              <Cell className="p-4 text-on-surface"><CheckCircle size={14} className="text-emerald-500" /></Cell>
              <Cell className="p-4 text-on-surface"><CheckCircle size={14} className="text-emerald-500" /></Cell>
              <Cell className="p-4 text-on-surface"><X size={14} className="text-rose-500" /></Cell>
              <Cell className="p-4 text-on-surface"><X size={14} className="text-rose-500" /></Cell>
              <Cell className="p-4 text-on-surface"><X size={14} className="text-rose-500" /></Cell>
            </Row>
            <Row className="hover:bg-surface-container-high transition-colors">
              <Cell className="p-4 font-label-md text-label-md text-on-surface">Manage Users</Cell>
              <Cell className="p-4 text-on-surface"><CheckCircle size={14} className="text-emerald-500" /></Cell>
              <Cell className="p-4 text-on-surface"><X size={14} className="text-rose-500" /></Cell>
              <Cell className="p-4 text-on-surface"><X size={14} className="text-rose-500" /></Cell>
              <Cell className="p-4 text-on-surface"><X size={14} className="text-rose-500" /></Cell>
              <Cell className="p-4 text-on-surface"><X size={14} className="text-rose-500" /></Cell>
            </Row>
          </Body>
        </Table>
      </div>
    </div>
  );
}

// Integrations Section
function IntegrationsSection({
  integrations,
  onIntegrationAction,
  onSearch
}: {
  integrations: Integration[];
  onIntegrationAction: (action: string, integrationId: string) => void;
  onSearch: (term: string) => void;
}) {
  return (
    <div className="space-y-6">
      <h2 className="font-headline-lg text-headline-lg text-on-surface">Integrations</h2>
      <p className="text-body-lg text-on-surface-variant">Manage third-party service connections and data sources</p>

      {/* Integrations Table */}
      <div className="overflow-x-auto">
        <Table>
          <Header>
            <HeaderRow>
              <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Integration</HeaderCell>
              <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Provider</HeaderCell>
              <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Status</HeaderCell>
              <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Last Sync</HeaderCell>
              <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Configurations</HeaderCell>
              <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left text-right">Actions</HeaderCell>
            </HeaderRow>
          </Header>
          <Body>
            {integrations.length === 0 ? (
              <Row>
                <Cell colSpan={6} className="p-8 text-center text-on-surface-variant">
                  <Plug size={32} className="mx-auto mb-4 opacity-50" />
                  <p className="text-center text-on-surface-variant">No integrations configured</p>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onIntegrationAction("add", "")}
                    className="bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
                  >
                    <Plus size={14} className="mr-1" /> Add Integration
                  </Button>
                </Cell>
              </Row>
            ) : (
              integrations.map((integration) => (
                <Row key={integration.id} className="hover:bg-surface-container-high transition-colors">
                  <Cell className="p-4 text-on-surface">{integration.name}</Cell>
                  <Cell className="p-4">
                    <span className="text-on-surface-variant">{integration.provider}</span>
                  </Cell>
                  <Cell className="p-4">
                    <Badge
                      variant={
                        integration.status === "connected" ? "secondary" :
                        integration.status === "error" ? "destructive" : "warning"
                      }
                      className="text-[10px] px-2 py-0.5"
                    >
                      {integration.status.charAt(0).toUpperCase() + integration.status.slice(1)}
                    </Badge>
                  </Cell>
                  <Cell className="p-4 text-on-surface">
                    {integration.lastSync ? (
                      <span className="text-xs">{new Date(integration.lastSync).toLocaleString()}</span>
                    ) : (
                      <span className="text-xs text-on-surface-variant">Never</span>
                    )}
                  </Cell>
                  <Cell className="p-4 text-center">{integration.configCount}</Cell>
                  <Cell className="p-4 text-right">
                    <div className="inline-flex space-x-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onIntegrationAction("edit", integration.id)}
                        className="p-1"
                      >
                        <Edit2 size={12} />
                      </Button>
                      <Button
                        variant={
                          integration.status === "connected"
                            ? "outline"
                            : integration.status === "error"
                              ? "default"
                              : "outline"
                        }
                        size="sm"
                        onClick={() => onIntegrationAction("toggle-status", integration.id)}
                        className="p-1 bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
                      >
                        {integration.status === "connected" ? (
                          <> <> <Zap size={12} /> Test Connection </> </>
                        ) : integration.status === "error" ? (
                          <> <> <RefreshCw size={12} /> Retry </> </>
                        ) : (
                          <> <> <Plug size={12} /> Connect </> </>
                        )}
                      </Button>
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => {
                          if (window.confirm(`Disconnect ${integration.name}? This may affect dependent features.`)) {
                            onIntegrationAction("disconnect", integration.id);
                          }
                        }}
                        className="p-1 bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
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

      {/* Add Integration Button */}
      <div className="mt-4">
        <Button
          variant="default"
          size="sm"
          onClick={() => onIntegrationAction("add-wizard", "")}
          className="bg-investment-gold text-surface hover:bg-investment-gold/90"
        >
          <Plug size={16} className="mr-1" /> Add New Integration
        </Button>
      </div>
    </div>
  );
}

// Audit Logs Section
function AuditLogsSection({
  logs,
  onLogAction,
  onSearch
}: {
  logs: AuditLogEntry[];
  onLogAction: (action: string, logId: string) => void;
  onSearch: (term: string) => void;
}) {
  return (
    <div className="space-y-6">
      <h2 className="font-headline-lg text-headline-lg text-on-surface">Audit Logs</h2>
      <p className="text-body-lg text-on-surface-variant">View and export system activity logs for compliance and troubleshooting</p>

      {/* Logs Table */}
      <div className="overflow-x-auto">
        <Table>
          <Header>
            <HeaderRow>
              <HeaderCell className="w-4 p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">
                <Checkbox
                  // Select all would go here
                  aria-label="Select all logs"
                  className="bg-transparent border-none focus:ring-0"
                />
              </HeaderCell>
              <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Timestamp</HeaderCell>
              <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">User</HeaderCell>
              <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Action</HeaderCell>
              <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Resource</HeaderCell>
              <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Details</HeaderCell>
              <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left text-right">Actions</HeaderCell>
            </HeaderRow>
          </Header>
          <Body>
            {logs.length === 0 ? (
              <Row>
                <Cell colSpan={8} className="p-8 text-center text-on-surface-variant">
                  <FileText size={32} className="mx-auto mb-4 opacity-50" />
                  <p className="text-center text-on-surface-variant">No audit logs found</p>
                </Cell>
              </Row>
            ) : (
              logs.map((log) => (
                <Row key={log.id} className="hover:bg-surface-container-high transition-colors">
                  <Cell className="w-4 p-4">
                    <Checkbox
                      checked={false} // Selection state would be managed
                      onChange={(checked) => {}}
                      onClick={(e) => e.stopPropagation()}
                      aria-label={`Select log entry ${log.id}`}
                      className="bg-transparent border-none focus:ring-0"
                    />
                  </Cell>
                  <Cell className="p-4 text-on-surface">
                    {new Date(log.timestamp).toLocaleString()}
                  </Cell>
                  <Cell className="p-4 text-on-surface truncate max-w-[200px]">{log.user}</Cell>
                  <Cell className="p-4 text-on-surface">{log.action.replace(/\./g, ' ').replace(/([A-Z])/g, ' $1').trim()}</Cell>
                  <Cell className="p-4 text-on-surface truncate max-w-[200px]">{log.resource}</Cell>
                  <Cell className="p-4 text-on-surface truncate max-w-[300px]">{log.details}</Cell>
                  <Cell className="p-4 text-right">
                    <div className="inline-flex space-x-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onLogAction("view-details", log.id)}
                        className="p-1"
                      >
                        <Eye size={12} />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onLogAction("copy-reference", log.id)}
                        className="p-1"
                      >
                        <Copy size={12} />
                      </Button>
                    </div>
                  </Cell>
                </Row>
              ))
            )}
          </Body>
        </Table>
      </div>

      {/* Logs Actions Bar */}
      <div className="flex gap-2 mt-4">
        <Button
          variant="outline"
          size="sm"
          onClick={() => onLogAction("export-selected", "")}
          className="bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
        >
          <FileText size={14} className="mr-1" /> Export Selected
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onLogAction("delete-selected", "")}
          className="bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
        >
          <Trash2 size={14} className="mr-1" /> Delete Selected
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onLogAction("refresh", "")}
          className="bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
        >
          <RefreshCw size={14} /> Refresh
        </Button>
      </div>
    </div>
  );
}

// System Health Section
function SystemHealthSection({
  onSearch
}: {
  onSearch: (term: string) => void;
}) {
  return (
    <div className="space-y-6">
      <h2 className="font-headline-lg text-headline-lg text-on-surface">System Health</h2>
      <p className="text-body-lg text-on-surface-variant">Monitor system performance, service status, and resource utilization</p>

      {/* Health Status Cards */}
      <div className="grid gap-4 mb-6">
        <div className="bg-surface-container-low border border-outline-variant rounded-xl p-6 text-center">
          <div className="text-3xl font-bold text-on-surface">Healthy</div>
          <p className="text-sm text-on-surface-variant">Overall Status</p>
          <p className="text-xs text-on-surface-variant">All systems operational</p>
        </div>
        <div className="bg-surface-container-low border border-outline-variant rounded-xl p-6 text-center">
          <div className="text-3xl font-bold text-on-surface">145ms</div>
          <p className="text-sm text-on-surface-variant">API Response Time</p>
          <p className="text-xs text-on-surface-variant">Average response time across all endpoints</p>
        </div>
        <div className="bg-surface-container-low border border-outline-variant rounded-xl p-6 text-center">
          <div className="text-3xl font-bold text-on-surface">23/100</div>
          <p className="text-sm text-on-surface-variant">Database Connections</p>
          <p className="text-xs text-on-surface-variant">Active database connection pool usage</p>
        </div>
        <div className="bg-surface-container-low border border-outline-variant rounded-xl p-6 text-center">
          <div className="text-3xl font-bold text-on-surface">85%</div>
          <p className="text-sm text-on-surface-variant">Memory Usage</p>
          <p className="text-xs text-on-surface-variant">System memory utilization</p>
        </div>
      </div>

      {/* Resource Charts */}
      <div className="grid gap-4">
        <div className="bg-surface-container-low border border-outline-variant rounded-xl p-6">
          <h3 className="font-label-md text-label-md text-on-surface mb-3">CPU Usage</h3>
          <div className="h-32 bg-surface-container-highest rounded-lg flex items-center justify-center">
            <div className="text-on-surface-variant">Chart visualization would be displayed here</div>
          </div>
          <p className="mt-2 text-center text-xs text-on-surface-variant">
            Current: 45% • Threshold: 80%
          </p>
        </div>
        <div className="bg-surface-container-low border border-outline-variant rounded-xl p-6">
          <h3 className="font-label-md text-label-md text-on-surface mb-3">Network I/O</h3>
          <div className="h-32 bg-surface-container-highest rounded-lg flex items-center justify-center">
            <div className="text-on-surface-variant">Chart visualization would be displayed here</div>
          </div>
          <p className="mt-2 text-center text-xs text-on-surface-variant">
            Current: 12.5 MB/s • Threshold: 100 MB/s
          </p>
        </div>
      </div>
    </div>
  );
}

// Button Group helper
function ButtonGroup({ children }: { children: React.ReactNode }) {
  return <div className="inline-flex space-x-1">{children}</div>;
}


export default Administration;