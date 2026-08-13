import { useState } from "react";
import { Header as LayoutHeader } from "../../components/layout/Header";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../../components/ui/Select";
import { Checkbox } from "../../components/ui/Checkbox";
import { Badge } from "../../components/ui/Badge";
import { Card, CardHeader, CardTitle, CardContent } from "../../components/ui/Card";
import { Table, TableBody, Cell, HeaderCell, HeaderRow, Header, Body, Row } from "../../components/ui/Table";
import {
  User, Edit2, Mail, Phone, Settings, Bell, Share2, Lock, Zap,
  Home, Server, Briefcase, GraduationCap, Key, ShieldAlert,
  LogOut, Activity, FileText, Calendar, Glasses,
  RotateCcw, X, Plug, CircleHelp, CheckCircle, Users, UserX
} from "lucide-react";

// User profile data types
interface UserProfileData {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  phone: string | null;
  avatarUrl: string | null;
  bio: string | null;
  department: string | null;
  position: string | null;
  hireDate: string | null;
  lastLogin: string | null;
  status: "active" | "inactive" | "pending";
  mfaEnabled: boolean;
  timezone: string;
  language: string;
  theme: "light" | "dark" | "auto";
  dateFormat: string;
  timeFormat: string;
  emailNotifications: boolean;
  inAppNotifications: boolean;
  smsNotifications: boolean;
}

// Notification preference types
interface NotificationPreference {
  id: string;
  type: string;
  enabled: boolean;
  channels: string[]; // email, in-app, sms
  frequency: "immediate" | "daily" | "weekly";
}

// Activity log entry
interface ActivityLogEntry {
  id: string;
  timestamp: string;
  action: string;
  description: string;
  ipAddress: string | null;
  location: string | null;
  success: boolean;
}

// Connected application
interface ConnectedApplication {
  id: string;
  name: string;
  icon: string; // URL or identifier
  status: "connected" | "disconnected" | "error";
  scopes: string[];
  connectedAt: string;
  lastUsed: string | null;
}

// Mock user profile data
const MOCK_USER_PROFILE: UserProfileData = {
  id: "user-001",
  firstName: "Alex",
  lastName: "Johnson",
  email: "alex.johnson@company.com",
  phone: "+1 (555) 123-4567",
  avatarUrl: "/avatars/alex-johnson.jpg",
  bio: "Senior fraud investigator with 8 years of experience in financial crimes and cybersecurity.",
  department: "Fraud Investigation",
  position: "Senior Investigator",
  hireDate: "2019-03-15",
  lastLogin: "2024-01-15T10:30:00Z",
  status: "active",
  mfaEnabled: true,
  timezone: "America/New_York",
  language: "en-US",
  theme: "dark",
  dateFormat: "MM/DD/YYYY",
  timeFormat: "12-hour",
  emailNotifications: true,
  inAppNotifications: true,
  smsNotifications: false
};

// Mock notification preferences
const MOCK_NOTIFICATION_PREFERENCES: NotificationPreference[] = [
  {
    id: "notif-001",
    type: "investigation-updates",
    enabled: true,
    channels: ["email", "in-app"],
    frequency: "immediate"
  },
  {
    id: "notif-002",
    type: "system-alerts",
    enabled: true,
    channels: ["in-app", "sms"],
    frequency: "immediate"
  },
  {
    id: "notif-003",
    type: "weekly-summary",
    enabled: true,
    channels: ["email"],
    frequency: "weekly"
  },
  {
    id: "notif-004",
    type: "security-alerts",
    enabled: false,
    channels: ["email", "in-app", "sms"],
    frequency: "immediate"
  }
];

// Mock activity log
const MOCK_ACTIVITY_LOG: ActivityLogEntry[] = [
  {
    id: "act-001",
    timestamp: "2024-01-15T10:30:00Z",
    action: "investigation.viewed",
    description: "Viewed investigation INV-78491",
    ipAddress: "192.168.1.100",
    location: "New York, NY",
    success: true
  },
  {
    id: "act-002",
    timestamp: "2024-01-15T10:25:00Z",
    action: "evidence.uploaded",
    description: "Uploaded evidence file: transaction_records.pdf",
    ipAddress: "192.168.1.100",
    location: "New York, NY",
    success: true
  },
  {
    id: "act-003",
    timestamp: "2024-01-15T10:20:00Z",
    action: "report.generated",
    description: "Generated Suspicious Activity Report for INV-78490",
    ipAddress: "192.168.1.100",
    location: "New York, NY",
    success: true
  },
  {
    id: "act-004",
    timestamp: "2024-01-15T09:15:00Z",
    action: "profile.updated",
    description: "Updated phone number and notification preferences",
    ipAddress: "192.168.1.100",
    location: "New York, NY",
    success: true
  },
  {
    id: "act-005",
    timestamp: "2024-01-14T16:45:00Z",
    action: "login.success",
    description: "Successful login from Chrome on Windows",
    ipAddress: "192.168.1.100",
    location: "New York, NY",
    success: true
  }
];

// Mock connected applications
const MOCK_CONNECTED_APPS: ConnectedApplication[] = [
  {
    id: "app-001",
    name: "Slack",
    icon: "slack",
    status: "connected",
    scopes: ["messages:read", "chat:write"],
    connectedAt: "2023-11-20T14:30:00Z",
    lastUsed: "2024-01-15T09:15:00Z"
  },
  {
    id: "app-002",
    name: "Microsoft Teams",
    icon: "teams",
    status: "connected",
    scopes: ["user.read", "chat.write"],
    connectedAt: "2023-12-01T10:00:00Z",
    lastUsed: "2024-01-14T16:30:00Z"
  },
  {
    id: "app-003",
    name: "Salesforce",
    icon: "salesforce",
    status: "disconnected",
    scopes: ["contact.read", "lead.create"],
    connectedAt: "2023-10-15T09:00:00Z",
    lastUsed: "2023-12-20T11:45:00Z"
  }
];

export function UserProfile() {
  const [activeTab, setActiveTab] = useState<"profile" | "preferences" | "notifications" | "activity" | "security" | "applications">("profile");
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState<Partial<UserProfileData>>({});

  // Handle form changes
  const handleChange = (field: keyof UserProfileData, value: any) => {
    setEditForm(prev => ({ ...prev, [field]: value }));
  };

  // Handle form submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // In a real app, this would send data to the API
    alert("Profile updated successfully!");
    setIsEditing(false);
    // Reset form to current values
    setEditForm({});
  };

  // Handle cancel edit
  const handleCancel = () => {
    setIsEditing(false);
    setEditForm({});
  };

  // Toggle notification preference
  const toggleNotification = (id: string) => {
    // In a real app, this would update the preference via API
    alert(`Toggled notification preference ${id}`);
  };

  // Toggle notification channel
  const toggleNotificationChannel = (notificationId: string, channel: string) => {
    // In a real app, this would update the preference via API
    alert(`Toggled ${channel} for notification ${notificationId}`);
  };

  // Change notification frequency
  const changeNotificationFrequency = (id: string, frequency: string) => {
    // In a real app, this would update the preference via API
    alert(`Changed frequency for ${id} to ${frequency}`);
  };

  // Disconnect application
  const disconnectApplication = (appId: string) => {
    if (window.confirm("Disconnect this application? This will revoke its access to your account.")) {
      // In a real app, this would call the API to disconnect
      alert("Application disconnected successfully");
    }
  };

  // Reconnect application
  const reconnectApplication = (appId: string) => {
    // In a real app, this would initiate OAuth flow
    alert("Opening authorization screen...");
  };

  // Enable/disable MFA
  const toggleMFA = () => {
    // In a real app, this would trigger MFA setup flow
    alert("Opening MFA setup wizard...");
  };

  // Change password
  const changePassword = () => {
    // In a real app, this would open password change modal
    alert("Opening password change dialog...");
  };

  return (
    <div className="flex h-full w-flex flex-col">
      <LayoutHeader
        title="My Profile"
        rightContent={
          <Button
            variant={isEditing ? "destructive" : "outline"}
            size="sm"
            onClick={isEditing ? handleCancel : () => setIsEditing(true)}
          >
            {isEditing ? (
              <> <> <X size={16} className="mr-1" /> Cancel </> </>
            ) : (
              <> <> <Edit2 size={16} className="mr-1" /> Edit Profile </> </>
            )}
          </Button>
        }
      />

      <div className="flex-1 overflow-y-auto p-6">
        <div className="space-y-6">
          {/* Profile Tab */}
          {activeTab === "profile" && (
            <ProfileTab
              profile={MOCK_USER_PROFILE}
              isEditing={isEditing}
              editForm={editForm}
              onChange={handleChange}
              onSubmit={handleSubmit}
              onMfaToggle={toggleMFA}
              onPasswordChange={changePassword}
              setIsEditing={setIsEditing}
              handleCancel={handleCancel}
            />
          )}

          {/* Preferences Tab */}
          {activeTab === "preferences" && (
            <PreferencesTab
              profile={MOCK_USER_PROFILE}
              isEditing={isEditing}
              editForm={editForm}
              onChange={handleChange}
              onSubmit={handleSubmit}
              setIsEditing={setIsEditing}
              handleCancel={handleCancel}
            />
          )}

          {/* Notifications Tab */}
          {activeTab === "notifications" && (
            <NotificationsTab
              preferences={MOCK_NOTIFICATION_PREFERENCES}
              onToggle={toggleNotification}
              onChannelToggle={toggleNotificationChannel}
              onFrequencyChange={changeNotificationFrequency}
            />
          )}

          {/* Activity Tab */}
          {activeTab === "activity" && (
            <ActivityTab
              logs={MOCK_ACTIVITY_LOG}
            />
          )}

          {/* Security Tab */}
          {activeTab === "security" && (
            <SecurityTab
              profile={MOCK_USER_PROFILE}
              onMfaToggle={toggleMFA}
              onPasswordChange={changePassword}
            />
          )}

          {/* Applications Tab */}
          {activeTab === "applications" && (
            <ApplicationsTab
              apps={MOCK_CONNECTED_APPS}
              onDisconnect={disconnectApplication}
              onReconnect={reconnectApplication}
            />
          )}
        </div>
      </div>
    </div>
  );
}

// Profile Tab Component
function ProfileTab({
  profile,
  isEditing,
  editForm,
  onChange,
  onSubmit,
  onMfaToggle,
  onPasswordChange,
  setIsEditing,
  handleCancel
}: {
  profile: UserProfileData;
  isEditing: boolean;
  editForm: Partial<UserProfileData>;
  onChange: (field: keyof UserProfileData, value: any) => void;
  onSubmit: (e: React.FormEvent) => void;
  onMfaToggle: () => void;
  onPasswordChange: () => void;
  setIsEditing: (val: boolean) => void;
  handleCancel: () => void;
}) {
  const getValue = (field: keyof UserProfileData): any => {
    return editForm[field as keyof typeof editForm] ?? profile[field];
  };

  return (
    <form onSubmit={onSubmit} className="space-y-6">
      <div className="grid gap-6 md:grid-cols-2">
        {/* Personal Information */}
        <div className="space-y-4">
          <h2 className="text-xl font-bold text-on-surface">Personal Information</h2>
          <div className="space-y-4">
            <div className="space-y-2">
              <label className="text-xs font-medium text-on-surface-variant">First Name</label>
              <Input
                value={getValue("firstName") as string || ""}
                onChange={(e) => onChange("firstName", e.target.value)}
                disabled={!isEditing}
                placeholder="Enter first name"
                className="bg-surface-container-low border border-outline-variant"
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-medium text-on-surface-variant">Last Name</label>
              <Input
                value={getValue("lastName") as string || ""}
                onChange={(e) => onChange("lastName", e.target.value)}
                disabled={!isEditing}
                placeholder="Enter last name"
                className="bg-surface-container-low border border-outline-variant"
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-medium text-on-surface-variant">Email</label>
              <Input
                type="email"
                value={getValue("email") as string || ""}
                onChange={(e) => onChange("email", e.target.value)}
                disabled={!isEditing}
                placeholder="Enter email address"
                className="bg-surface-container-low border border-outline-variant"
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-medium text-on-surface-variant">Phone Number</label>
              <Input
                type="tel"
                value={getValue("phone") || ""}
                onChange={(e) => onChange("phone", e.target.value || null)}
                disabled={!isEditing}
                placeholder="Enter phone number"
                className="bg-surface-container-low border border-outline-variant"
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-medium text-on-surface-variant">Bio</label>
              <textarea
                value={getValue("bio") || ""}
                onChange={(e) => onChange("bio", e.target.value || null)}
                disabled={!isEditing}
                className="w-full min-h-[80px] p-3 bg-surface-container-low border border-outline-variant rounded-lg"
                placeholder="Tell us about yourself..."
              />
            </div>
          </div>
        </div>

        {/* Professional Information */}
        <div className="space-y-4">
          <h2 className="text-xl font-bold text-on-surface">Professional Information</h2>
          <div className="space-y-4">
            <div className="space-y-2">
              <label className="text-xs font-medium text-on-surface-variant">Department</label>
              <Input
                value={getValue("department") || ""}
                onChange={(e) => onChange("department", e.target.value || null)}
                disabled={!isEditing}
                placeholder="Enter department"
                className="bg-surface-container-low border border-outline-variant"
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-medium text-on-surface-variant">Position</label>
              <Input
                value={getValue("position") || ""}
                onChange={(e) => onChange("position", e.target.value || null)}
                disabled={!isEditing}
                placeholder="Enter position"
                className="bg-surface-container-low border border-outline-variant"
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-medium text-on-surface-variant">Hire Date</label>
              <Input
                type="date"
                value={getValue("hireDate") || ""}
                onChange={(e) => onChange("hireDate", e.target.value || null)}
                disabled={!isEditing}
                className="bg-surface-container-low border border-outline-variant"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Account Information */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-on-surface">Account Information</h2>
        <div className="space-y-4">
          <div className="flex items-center gap-4">
            {profile.avatarUrl ? (
              <img
                src={profile.avatarUrl}
                alt="User avatar"
                className="w-20 h-20 rounded-full object-cover border-2 border-surface-container-highest"
              />
            ) : (
              <div className="w-20 h-20 flex items-center justify-center bg-surface-container-low rounded-full">
                <User size={24} className="text-on-surface-variant" />
              </div>
            )}
            <div className="space-y-2">
              <p className="font-medium text-on-surface">{`${profile.firstName} ${profile.lastName}`}</p>
              <p className="text-xs text-on-surface-variant">{profile.email}</p>
              <div className="flex items-center gap-2 mt-2">
                <Badge
                  variant={profile.status === "active" ? "secondary" : profile.status === "inactive" ? "destructive" : "warning"}
                  className="text-[10px] px-2 py-0.5"
                >
                  {profile.status.charAt(0).toUpperCase() + profile.status.slice(1)}
                </Badge>
                <Badge
                  variant={profile.mfaEnabled ? "secondary" : "outline"}
                  className="text-[10px] px-2 py-0.5"
                  onClick={onMfaToggle}
                >
                  {profile.mfaEnabled ? "MFA Enabled" : "MFA Disabled"}
                </Badge>
              </div>
            </div>
          </div>
        </div>

        {/* Security Actions */}
        <div className="space-y-4">
          <h2 className="text-xl font-bold text-on-surface">Security</h2>
          <div className="space-y-4">
            <Button
              variant="outline"
              size="sm"
              onClick={onPasswordChange}
              className="w-full bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
            >
              <Lock size={16} className="mr-1" /> Change Password
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                // Download data export
                alert("Downloading your data export...");
              }}
              className="w-full bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
            >
              <FileText size={16} className="mr-1" /> Export Data
            </Button>
          </div>
        </div>
      </div>

      {!isEditing && (
        <div className="pt-4 border-t border-outline-variant">
          <Button
            variant="default"
            size="sm"
            onClick={() => setIsEditing(true)}
            className="w-full bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
          >
            <> <Edit2 size={16} className="mr-1" /> Edit Profile </>
          </Button>
        </div>
      )}

      {isEditing && (
        <div className="flex justify-end mt-6 space-x-3">
          <Button
            variant="outline"
            size="sm"
            onClick={handleCancel}
            className="bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
          >
            Cancel
          </Button>
          <Button
            variant="default"
            size="sm"
            onClick={onSubmit}
            className="bg-investment-gold text-surface hover:bg-investment-gold/90"
          >
            Save Changes
          </Button>
        </div>
      )}
    </form>
  );
}

// Preferences Tab Component
function PreferencesTab({
  profile,
  isEditing,
  editForm,
  onChange,
  onSubmit,
  setIsEditing,
  handleCancel
}: {
  profile: UserProfileData;
  isEditing: boolean;
  editForm: Partial<UserProfileData>;
  onChange: (field: keyof UserProfileData, value: any) => void;
  onSubmit: (e: React.FormEvent) => void;
  setIsEditing: (val: boolean) => void;
  handleCancel: () => void;
}) {
  const getValue = (field: keyof UserProfileData): any => {
    return editForm[field as keyof typeof editForm] ?? profile[field];
  };

  return (
    <form onSubmit={onSubmit} className="space-y-6">
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-on-surface">Preferences</h2>
        <div className="space-y-4">
          <div className="space-y-2">
            <label className="text-xs font-medium text-on-surface-variant">Theme</label>
            <Select
              value={getValue("theme") || "auto"}
              onValueChange={(value) => onChange("theme", value)}
              disabled={!isEditing}
              className="bg-surface-container-low border border-outline-variant"
            >
              <SelectValue placeholder="Select theme" />
              <SelectItem value="light">Light</SelectItem>
              <SelectItem value="dark">Dark</SelectItem>
              <SelectItem value="auto">Auto (System)</SelectItem>
            </Select>
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium text-on-surface-variant">Language</label>
            <Select
              value={getValue("language") || "en-US"}
              onValueChange={(value) => onChange("language", value)}
              disabled={!isEditing}
              className="bg-surface-container-low border border-outline-variant"
            >
              <SelectValue placeholder="Select language" />
              <SelectItem value="en-US">English (US)</SelectItem>
              <SelectItem value="es-ES">Español</SelectItem>
              <SelectItem value="fr-FR">Français</SelectItem>
              <SelectItem value="de-DE">Deutsch</SelectItem>
              <SelectItem value="ja-JP">日本語</SelectItem>
            </Select>
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium text-on-surface-variant">Date Format</label>
            <Select
              value={getValue("dateFormat") || "MM/DD/YYYY"}
              onValueChange={(value) => onChange("dateFormat", value)}
              disabled={!isEditing}
              className="bg-surface-container-low border border-outline-variant"
            >
              <SelectValue placeholder="Select date format" />
              <SelectItem value="MM/DD/YYYY">MM/DD/YYYY</SelectItem>
              <SelectItem value="DD/MM/YYYY">DD/MM/YYYY</SelectItem>
              <SelectItem value="YYYY-MM-DD">YYYY-MM-DD</SelectItem>
            </Select>
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium text-on-surface-variant">Time Format</label>
            <Select
              value={getValue("timeFormat") || "12-hour"}
              onValueChange={(value) => onChange("timeFormat", value)}
              disabled={!isEditing}
              className="bg-surface-container-low border border-outline-variant"
            >
              <SelectValue placeholder="Select time format" />
              <SelectItem value="12-hour">12-hour (AM/PM)</SelectItem>
              <SelectItem value="24-hour">24-hour</SelectItem>
            </Select>
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium text-on-surface-variant">Timezone</label>
            <Select
              value={getValue("timezone") || "America/New_York"}
              onValueChange={(value) => onChange("timezone", value)}
              disabled={!isEditing}
              className="bg-surface-container-low border border-outline-variant"
            >
              <SelectValue placeholder="Select timezone" />
              <SelectItem value="America/New_York">Eastern Time (US & Canada)</SelectItem>
              <SelectItem value="America/Chicago">Central Time (US & Canada)</SelectItem>
              <SelectItem value="America/Denver">Mountain Time (US & Canada)</SelectItem>
              <SelectItem value="America/Los_Angeles">Pacific Time (US & Canada)</SelectItem>
              <SelectItem value="Europe/London">Greenwich Mean Time</SelectItem>
              <SelectItem value="Europe/Paris">Central European Time</SelectItem>
              <SelectItem value="Asia/Tokyo">Japan Standard Time</SelectItem>
              <SelectItem value="Asia/Shanghai">China Standard Time</SelectItem>
            </Select>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <h2 className="text-xl font-bold text-on-surface">Notification Preferences</h2>
        <div className="space-y-4">
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-xs font-medium text-on-surface-variant">
              <Checkbox
                checked={getValue("emailNotifications") || false}
                onChange={(checked) => onChange("emailNotifications", checked)}
                disabled={!isEditing}
                className="bg-surface-container-low border border-outline-variant"
              />
              Email Notifications
            </label>
          </div>
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-xs font-medium text-on-surface-variant">
              <Checkbox
                checked={getValue("inAppNotifications") || false}
                onChange={(checked) => onChange("inAppNotifications", checked)}
                disabled={!isEditing}
                className="bg-surface-container-low border border-outline-variant"
              />
              In-App Notifications
            </label>
          </div>
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-xs font-medium text-on-surface-variant">
              <Checkbox
                checked={getValue("smsNotifications") || false}
                onChange={(checked) => onChange("smsNotifications", checked)}
                disabled={!isEditing}
                className="bg-surface-container-low border border-outline-variant"
              />
              SMS Notifications
            </label>
          </div>
        </div>
      </div>

      {!isEditing && (
        <div className="pt-4 border-t border-outline-variant">
          <Button
            variant="default"
            size="sm"
            onClick={() => setIsEditing(true)}
            className="w-full bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
          >
            <Edit2 size={16} className="mr-1" /> Save Preferences
          </Button>
        </div>
      )}

      {isEditing && (
        <div className="flex justify-end mt-6 space-x-3">
          <Button
            variant="outline"
            size="sm"
            onClick={handleCancel}
            className="bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
          >
            Cancel
          </Button>
          <Button
            variant="default"
            size="sm"
            onClick={onSubmit}
            className="bg-investment-gold text-surface hover:bg-investment-gold/90"
          >
            Save Changes
          </Button>
        </div>
      )}
    </form>
  );
}

// Notifications Tab Component
function NotificationsTab({
  preferences,
  onToggle,
  onChannelToggle,
  onFrequencyChange
}: {
  preferences: NotificationPreference[];
  onToggle: (id: string) => void;
  onChannelToggle: (notificationId: string, channel: string) => void;
  onFrequencyChange: (id: string, frequency: string) => void;
}) {
  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-on-surface">Notification Preferences</h2>
      <p className="text-on-surface-variant">Customize how and when you receive notifications</p>

      <div className="space-y-4">
        {preferences.map((pref) => (
          <NotificationPreferenceItem
            key={pref.id}
            preference={pref}
            onToggle={onToggle}
            onChannelToggle={onChannelToggle}
            onFrequencyChange={onFrequencyChange}
          />
        ))}
      </div>

      <div className="mt-4 p-4 bg-surface-container-low border border-outline-variant rounded-lg">
        <h3 className="font-medium mb-3 text-on-surface">Quiet Hours</h3>
        <div className="space-y-2">
          <label className="flex items-center gap-2 text-xs font-medium text-on-surface-variant">
            <Checkbox
              checked={false} // Would come from profile settings
              onChange={(checked) => console.log("Quiet hours enabled:", checked)}
              className="bg-surface-container-low border border-outline-variant"
            />
            Enable Quiet Hours
          </label>
          <div className="mt-2 flex gap-2">
            <Input
              type="time"
              placeholder="Start time"
              className="flex-1 bg-surface-container-low border border-outline-variant"
              disabled={true}
            />
            <span className="text-xs text-on-surface-variant">to</span>
            <Input
              type="time"
              placeholder="End time"
              className="flex-1 bg-surface-container-low border border-outline-variant"
              disabled={true}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

// Notification Preference Item
function NotificationPreferenceItem({
  preference,
  onToggle,
  onChannelToggle,
  onFrequencyChange
}: {
  preference: NotificationPreference;
  onToggle: (id: string) => void;
  onChannelToggle: (notificationId: string, channel: string) => void;
  onFrequencyChange: (id: string, frequency: string) => void;
}) {
  return (
    <div className="p-4 bg-surface-container-low border border-outline-variant rounded-lg">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h4 className="font-medium text-on-surface">{preference.type.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</h4>
          <p className="text-xs text-on-surface-variant mb-2">
            {preference.frequency === "immediate"
              ? "Sent immediately when triggered"
              : preference.frequency === "daily"
                ? "Delivered in daily digest"
                : "Delivered in weekly summary"}
          </p>
          <div className="flex flex-wrap gap-2 mb-2">
            {["email", "in-app", "sms"].map((channel) => (
              <span
                key={channel}
                className={`px-2 py-0.5 text-xs rounded cursor-pointer hover:bg-surface-container-high transition-colors ${
                  preference.channels.includes(channel)
                    ? "bg-surface-container-high"
                    : "bg-surface-container-low"
                }`}
                onClick={() => onChannelToggle(preference.id, channel)}
              >
                {channel.toUpperCase()}
              </span>
            ))}
          </div>
        </div>
        <div className="flex items-center gap-3">
          <ToggleSwitch
            checked={preference.enabled}
            onChange={(checked) => onToggle(preference.id)}
            label="Enabled"
            className="bg-surface-container-low border border-outline-variant"
          />
          <div className="flex-1 space-x-2">
            <label className="flex items-center gap-1 text-xs text-on-surface-variant">
              Frequency:
              <Select
                value={preference.frequency}
                onValueChange={(value) => onFrequencyChange(preference.id, value)}
                className="w-24 bg-surface-container-low border border-outline-variant"
              >
                <SelectItem value="immediate">Immediate</SelectItem>
                <SelectItem value="daily">Daily</SelectItem>
                <SelectItem value="weekly">Weekly</SelectItem>
              </Select>
            </label>
          </div>
        </div>
      </div>
    </div>
  );
}

// Toggle Switch Component
function ToggleSwitch({
  checked,
  onChange,
  label
}: {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  className?: string;
}) {
  return (
    <label className="flex items-center gap-3 cursor-pointer select-none">
      <span className="text-xs font-medium text-on-surface-variant">{label}</span>
      <div className="relative w-10 h-5">
        <div className="absolute inset-0 rounded-full bg-surface-container-low border border-outline-variant transition-all duration-200"></div>
        <div
          style={{ left: checked ? "20px" : "2px" }} className="absolute top-0.5 h-4 w-4 bg-investment-gold rounded-full shadow transition-all duration-200"
        ></div>
      </div>
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="absolute inset-0 w-0 h-0 opacity-0 pointer-events-none"
      />
    </label>
  );
}

// Activity Tab Component
function ActivityTab({
  logs
}: {
  logs: ActivityLogEntry[];
}) {
  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-on-surface">Activity History</h2>
      <p className="text-on-surface-variant">Recent actions and events in your account</p>

      <div className="space-y-4">
        <div className="flex items-center gap-2 mb-4">
          <input
            type="text"
            placeholder="Filter activities..."
            className="flex-1 p-3 bg-surface-container-low border border-outline-variant rounded-lg text-on-surface"
          />
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              // Export activity log
              alert("Exporting activity log...");
            }}
            className="bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
          >
            <FileText size={14} className="mr-1" /> Export
          </Button>
        </div>

        <div className="overflow-x-auto">
          <Table>
            <Header>
              <HeaderRow>
                <HeaderCell className="w-4 text-on-surface-variant">Time</HeaderCell>
                <HeaderCell className="text-on-surface-variant">Action</HeaderCell>
                <HeaderCell className="text-on-surface-variant">Description</HeaderCell>
                <HeaderCell className="w-16 text-on-surface-variant">Status</HeaderCell>
                <HeaderCell className="w-16 text-on-surface-variant">IP Address</HeaderCell>
                <HeaderCell className="w-16 text-on-surface-variant">Location</HeaderCell>
              </HeaderRow>
            </Header>
            <Body>
              {logs.length === 0 ? (
                <Row>
                  <Cell colSpan={6} className="text-center py-8">
                    <Activity size={32} className="mx-auto mb-4 opacity-50 text-on-surface-variant" />
                    <p className="text-center text-on-surface-variant">No activity found</p>
                  </Cell>
                </Row>
              ) : (
                logs.map((log) => (
                  <Row key={log.id} className="hover:bg-surface-container-high transition-colors">
                    <Cell className="text-xs text-on-surface-variant">
                      {new Date(log.timestamp).toLocaleString()}
                    </Cell>
                    <Cell className="font-medium text-on-surface">
                      {log.action.replace(/([a-z])([A-Z])/g, '$1 $2').toLowerCase()}
                    </Cell>
                    <Cell className="max-w-32 text-xs text-on-surface-variant">{log.description}</Cell>
                    <Cell className="text-center">
                      <div className={`w-3 h-3 rounded-full ${log.success ? "bg-emerald-500" : "bg-rose-500"}`} />
                    </Cell>
                    <Cell className="text-xs text-on-surface-variant">{log.ipAddress || "N/A"}</Cell>
                    <Cell className="text-xs text-on-surface-variant">{log.location || "N/A"}</Cell>
                  </Row>
                ))
              )}
            </Body>
          </Table>
        </div>

        <div className="mt-4 p-4 bg-surface-container-low border border-outline-variant rounded-lg">
          <h3 className="font-medium mb-3 text-on-surface">Activity Summary</h3>
          <div className="grid gap-4 grid-cols-2">
            <div className="text-center">
              <div className="text-2xl font-bold text-on-surface">24</div>
              <p className="text-xs text-on-surface-variant">Actions Today</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-on-surface">156</div>
              <p className="text-xs text-on-surface-variant">Actions This Week</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-on-surface">623</div>
              <p className="text-xs text-on-surface-variant">Actions This Month</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-on-surface">98%</div>
              <p className="text-xs text-on-surface-variant">Success Rate</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Security Tab Component
function SecurityTab({
  profile,
  onMfaToggle,
  onPasswordChange
}: {
  profile: UserProfileData;
  onMfaToggle: () => void;
  onPasswordChange: () => void;
}) {
  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-on-surface">Security Settings</h2>
      <p className="text-on-surface-variant">Manage your account security and access</p>

      {/* Security Status */}
      <div className="space-y-4">
        <h3 className="font-medium mb-3 text-on-surface">Account Security</h3>
        <div className="grid gap-4 grid-cols-2">
          <div className="p-4 bg-surface-container-low border border-outline-variant rounded-lg">
            <h4 className="font-medium mb-2 text-on-surface">Password</h4>
            <p className="text-xs text-on-surface-variant">Last changed: {new Date().toLocaleDateString()}</p>
            <Button
              variant="outline"
              size="sm"
              onClick={onPasswordChange}
              className="w-full mt-2 bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
            >
              <Lock size={14} className="mr-1" /> Change Password
            </Button>
          </div>
          <div className="p-4 bg-surface-container-low border border-outline-variant rounded-lg">
            <h4 className="font-medium mb-2 text-on-surface">Two-Factor Authentication</h4>
            <p className="text-xs text-on-surface-variant">
              {profile.mfaEnabled ? "Enabled" : "Disabled"}
            </p>
            <Button
              variant={profile.mfaEnabled ? "outline" : "default"}
              size="sm"
              onClick={onMfaToggle}
              className="w-full mt-2 bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
            >
              {profile.mfaEnabled ? (
                <> <> <RotateCcw size={14} className="mr-1" /> Reconfigure </> </>
              ) : (
                <> <> <Zap size={14} className="mr-1" /> Enable </> </>
              )}
            </Button>
          </div>
        </div>
      </div>

      {/* Active Sessions */}
      <div className="space-y-4">
        <h3 className="font-medium mb-3 text-on-surface">Active Sessions</h3>
        <div className="space-y-4">
          <div className="p-4 bg-surface-container-low border border-outline-variant rounded-lg">
            <h4 className="font-medium mb-2 text-on-surface">Current Session</h4>
            <p className="text-xs text-on-surface-variant">Chrome on Windows · New York, NY</p>
            <p className="text-xs text-on-surface-variant">Started: {new Date().toLocaleString()}</p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                // Terminate current session would require re-login
                alert("Terminating this session will log you out.");
              }}
              className="w-full bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
            >
              <LogOut size={14} className="mr-1" /> Log Out Elsewhere
            </Button>
          </div>
          <div className="p-4 bg-surface-container-low border border-outline-variant rounded-lg">
            <h4 className="font-medium mb-2 text-on-surface">Other Active Sessions</h4>
            <div className="space-y-2">
              <div className="flex items-center justify-between p-3 bg-surface-container-low border border-outline-variant rounded-lg">
                <div className="flex-1">
                  <p className="font-medium text-on-surface">Safari on macOS</p>
                  <p className="text-xs text-on-surface-variant">Boston, MA</p>
                </div>
                <div className="text-xs text-on-surface-variant">2 hours ago</div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    // Terminate specific session
                    alert("Session terminated");
                  }}
                  className="p-1 bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
                >
                  <X size={12} />
                </Button>
              </div>
              <div className="flex items-center justify-between p-3 bg-surface-container-low border border-outline-variant rounded-lg">
                <div className="flex-1">
                  <p className="font-medium text-on-surface">Firefox on Linux</p>
                  <p className="text-xs text-on-surface-variant">San Francisco, CA</p>
                </div>
                <div className="text-xs text-on-surface-variant">1 day ago</div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    // Terminate specific session
                    alert("Session terminated");
                  }}
                  className="p-1 bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
                >
                  <X size={12} />
                </Button>
              </div>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                // Terminate all other sessions
                if (window.confirm("Log out from all other devices? This will not affect your current session.")) {
                  alert("All other sessions terminated");
                }
              }}
              className="w-full mt-2 bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
            >
              <LogOut size={14} className="mr-1" /> Log Out All Other Sessions
            </Button>
          </div>
        </div>
      </div>

      {/* Security Events */}
      <div className="space-y-4">
        <h3 className="font-medium mb-3 text-on-surface">Recent Security Events</h3>
        <div className="space-y-4">
          <div className="p-4 bg-surface-container-low border border-outline-variant rounded-lg">
            <h4 className="font-medium mb-2 text-on-surface">Password Changed</h4>
            <p className="text-xs text-on-surface-variant">January 10, 2024 · New York, NY</p>
          </div>
          <div className="p-4 bg-surface-container-low border border-outline-variant rounded-lg">
            <h4 className="font-medium mb-2 text-on-surface">New Device Login</h4>
            <p className="text-xs text-on-surface-variant">January 12, 2024 · Chicago, IL</p>
          </div>
          <div className="p-4 bg-surface-container-low border border-outline-variant rounded-lg">
            <h4 className="font-medium mb-2 text-on-surface">Failed Login Attempt</h4>
            <p className="text-xs text-on-surface-variant">January 13, 2024 · Unknown Location</p>
          </div>
        </div>
      </div>
    </div>
  );
}

// Applications Tab Component
function ApplicationsTab({
  apps,
  onDisconnect,
  onReconnect
}: {
  apps: ConnectedApplication[];
  onDisconnect: (appId: string) => void;
  onReconnect: (appId: string) => void;
}) {
  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-on-surface">Connected Applications</h2>
      <p className="text-on-surface-variant">Manage applications that have access to your account</p>

      <div className="space-y-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-medium text-on-surface">Connected Applications</h3>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              // Initiate connection flow
              alert("Opening connection wizard...");
            }}
            className="bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
          >
            <Plug size={16} className="mr-1" /> Connect New App
          </Button>
        </div>

        <div className="space-y-4">
          {apps.length === 0 ? (
            <div className="text-center py-8">
              <Plug size={32} className="mx-auto mb-4 opacity-50 text-on-surface-variant" />
              <p className="text-center text-on-surface-variant">No connected applications</p>
            </div>
          ) : (
            <div className="space-y-4">
              {apps.map((app) => (
                <ConnectedApplicationItem
                  key={app.id}
                  application={app}
                  onDisconnect={onDisconnect}
                  onReconnect={onReconnect}
                />
              ))}
            </div>
          )}
        </div>

        <div className="mt-4 p-4 bg-surface-container-low border border-outline-variant rounded-lg">
          <h3 className="font-medium mb-3 text-on-surface">Application Permissions Explained</h3>
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <CircleHelp size={14} className="mr-1 text-on-surface-variant" />
              <span className="text-xs text-on-surface-variant">Applications may request various permissions to access your data and perform actions on your behalf.</span>
            </div>
            <div className="mt-2 space-y-1">
              <div className="flex items-center gap-2">
                <CheckCircle size={12} className="mr-1 text-emerald-500" />
                <span className="text-xs text-on-surface-variant">Read Access: View your data</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle size={12} className="mr-1 text-emerald-500" />
                <span className="text-xs text-on-surface-variant">Write Access: Create or modify data</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle size={12} className="mr-1 text-emerald-500" />
                <span className="text-xs text-on-surface-variant">Admin Access: Full control over your account</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Connected Application Item
function ConnectedApplicationItem({
  application,
  onDisconnect,
  onReconnect
}: {
  application: ConnectedApplication;
  onDisconnect: (appId: string) => void;
  onReconnect: (appId: string) => void;
}) {
  return (
    <div className="p-4 bg-surface-container-low border border-outline-variant rounded-lg">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0">
              {/* Icon would be rendered here based on application.icon */}
              <div className="w-8 h-8 flex items-center justify-center bg-surface-container-low">
                <Users size={16} className="text-on-surface-variant" />
              </div>
            </div>
            <div className="flex-1 space-y-1">
              <h4 className="font-medium text-on-surface">{application.name}</h4>
              <p className="text-xs text-on-surface-variant">
                Connected: {new Date(application.connectedAt).toLocaleDateString()}
              </p>
              <p className="text-xs text-on-surface-variant">
                Scopes: {application.scopes.map(s => s.split('.').pop()).join(', ')}
              </p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${application.status === "connected" ? "bg-emerald-500" :
                     application.status === "disconnected" ? "bg-rose-500" : "bg-amber-500"}`} />
          <span className="text-xs text-on-surface-variant capitalize">
            {application.status}
          </span>
        </div>
      </div>

      <div className="flex items-center justify-between mt-4">
        <div className="flex items-center gap-2">
          {application.lastUsed ? (
            <span className="text-xs text-on-surface-variant">
              Last used: {new Date(application.lastUsed).toLocaleString()}
            </span>
          ) : (
            <span className="text-xs text-on-surface-variant">Never used</span>
          )}
        </div>
        <div className="flex gap-2">
          {application.status === "connected" && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onDisconnect(application.id)}
              className="p-1 bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
            >
              <UserX size={12} /> Disconnect
            </Button>
          )}
          {(application.status === "disconnected" || application.status === "error") && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onReconnect(application.id)}
              className="p-1 bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
            >
              <Plug size={12} /> Reconnect
            </Button>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              // Manage scopes/permissions
              alert("Manage permissions for this application");
            }}
            className="p-1 bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
          >
            <Settings size={12} /> Manage
          </Button>
        </div>
      </div>
    </div>
  );
}

export default UserProfile;