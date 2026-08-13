import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/Select";
import { Checkbox } from "@/components/ui/Checkbox";
import { Badge } from "@/components/ui/Badge";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Table, TableBody, Cell, HeaderCell, HeaderRow, Header, Body, Row } from "@/components/ui/Table";
import { Alert } from "@/components/ui/Alert";
import { Separator } from "@/components/ui/Separator";
import { Toast } from "@/components/ui/Toast";
import { toast } from "@/components/ui/use-toast";

import {
  Plus, Trash2, Edit, Eye, EyeOff, Mail, Lock, UserPlus,
  ShieldCheck, AlertTriangle, CheckCircle, HelpCircle,
  List, Grid, Menu, ChevronLeft, X, RefreshCw, Search,
  Calendar, Bell, Users, Settings, Zap, Code, Github,
  Gitlab, TrendingUp, Activity, MapPin, ServerCpu,
  HardDrive, BatteryCharging, Wifi, ShieldAlert
} from "lucide-react";

export function ComponentLibrary() {
  const [toastState, setToastState] = useState({
    open: false,
    variant: "default",
    title: "",
    description: ""
  });
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [isChecked, setIsChecked] = useState(false);
  const [isToggleChecked, setIsToggleChecked] = useState(false);
  const [count, setCount] = useState(0);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedValue, setSelectedValue] = useState("option1");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);

  const categories = ["all", "form", "data", "feedback", "navigation", "overlay", "layout"];

  const handleToast = (variant: "default" | "destructive" | "success" | "warning") => {
    toast({
      variant,
      title: "Action Completed",
      description: `This is a ${variant} toast notification.`,
      duration: 3000
    });
  };

  return (
    <div className="space-y-8">
      <div className="flex flex-col lg:flex-row lg:space-x-8">
        {/* Sidebar */}
        <aside className="lg:w-64">
          <h2 className="font-semibold mb-4">Component Library</h2>
          <div className="space-y-2">
            <Input
              placeholder="Search components..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="mb-2"
            />
            <div className="space-y-1">
              {categories.map((category) => (
                <label
                  key={category}
                  className="flex items-center gap-2 p-2 rounded hover:bg-white/5 transition-colors cursor-pointer"
                  onClick={() => setSelectedCategory(category)}
                >
                  <Checkbox
                    checked={selectedCategory === category}
                    onChange={() => setSelectedCategory(category)}
                    className="flex-shrink-0"
                  />
                  <span className="text-sm">{category}</span>
                </label>
              ))}
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <div className="flex-1">
          <div className="space-y-6">
            {/* Form Components */}
            {selectedCategory === "all" || selectedCategory === "form" && (
              <>
                <h2 className="font-bold text-xl mb-4">Form Components</h2>

                <div className="space-y-6">
                  {/* Input Examples */}
                  <div className="space-y-4">
                    <h3 className="font-medium mb-2">Input Fields</h3>
                    <div className="space-y-4">
                      <div className="space-y-2">
                        <label className="block text-xs font-medium text-text-secondary mb-1">
                          Email Address
                        </label>
                        <Input
                          type="email"
                          value={email}
                          onChange={(e) => setEmail(e.target.value)}
                          placeholder="Enter your email"
                        />
                      </div>
                      <div className="space-y-2">
                        <label className="block text-xs font-medium text-text-secondary mb-1">
                          Password
                        </label>
                        <div className="relative">
                          <Input
                            type={password ? "text" : "password"}
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Enter your password"
                            className="pr-10"
                          />
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setPassword(password ? "" : "password")}
                            className="absolute right-2 top-1/2 -translate-y-1/2 p-1"
                            aria-label="Toggle password visibility"
                          >
                            {password ? (
                              <EyeOff size={16} />
                            ) : (
                              <Eye size={16} />
                            )}
                          </Button>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <label className="block text-xs font-medium text-text-secondary mb-1">
                          Input with Error
                        </label>
                        <Input
                          type="text"
                          placeholder="This field has an error"
                          className="border-red-500"
                        />
                        <p className="text-xs text-red-500 mt-1">
                          Please correct this field
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Select Examples */}
                  <div className="space-y-4">
                    <h3 className="font-medium mb-2">Select Dropdown</h3>
                    <div className="space-y-4">
                      <div className="space-y-2">
                        <label className="block text-xs font-medium text-text-secondary mb-1">
                          Category Selection
                        </label>
                        <Select
                          value={selectedValue}
                          onValueChange={setSelectedValue}
                          placeholder="Select an option"
                        >
                          <SelectValue placeholder="Select category" />
                          <SelectItem value="option1">Investigation</SelectItem>
                          <SelectItem value="option2">Evidence</SelectItem>
                          <SelectItem value="option3">Report</SelectItem>
                          <SelectItem value="option4">Analytics</SelectItem>
                        </Select>
                      </div>
                    </div>
                  </div>

                  {/* Checkbox Examples */}
                  <div className="space-y-4">
                    <h3 className="font-medium mb-2">Checkboxes</h3>
                    <div className="space-y-4">
                      <div className="flex items-center space-x-3">
                        <Checkbox
                          checked={isChecked}
                          onChange={(e) => setIsChecked(e.target.checked)}
                        >
                          Remember me
                        </Checkbox>
                      </div>
                      <div className="flex items-center space-x-3">
                        <Checkbox
                          checked={isToggleChecked}
                          onChange={(e) => setIsToggleChecked(e.target.checked)}
                          className="h-4 w-4"
                        >
                          Enable notifications
                        </Checkbox>
                      </div>
                      <div className="flex items-center space-x-3">
                        <label className="flex items-center space-x-2">
                          <Checkbox
                            checked={rememberMe}
                            onChange={(e) => setRememberMe(e.target.checked)}
                          />
                          <span>Remember me</span>
                        </label>
                      </div>
                    </div>
                  </div>

                  {/* Button Examples */}
                  <div className="space-y-4">
                    <h3 className="font-medium mb-2">Buttons</h3>
                    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                      <Button variant="default" size="sm" onClick={() => handleToast("default")}>
                        Default Small
                      </Button>
                      <Button variant="default" size="md" onClick={() => handleToast("default")}>
                        Default Medium
                      </Button>
                      <Button variant="default" size="lg" onClick={() => handleToast("default")}>
                        Default Large
                      </Button>
                      <Button variant="outline" size="md" onClick={() => handleToast("default")}>
                        Outline
                      </Button>
                      <Button variant="ghost" size="md" onClick={() => handleToast("default")}>
                        Ghost
                      </Button>
                      <Button variant="destructive" size="md" onClick={() => handleToast("destructive")}>
                        Destructive
                      </Button>
                      <Button variant="default" size="md" onClick={() => handleToast("success")} className="flex items-center gap-2">
                        <Plus size={16} /> Add New
                      </Button>
                      <Button variant="outline" size="md" onClick={() => handleToast("warning")} className="flex items-center gap-2">
                        <Search size={16} /> Search
                      </Button>
                    </div>

                    <div className="mt-4">
                      <h4 className="font-medium mb-2">Button Group</h4>
                      <div className="inline-flex space-x-1">
                        <Button variant="outline" size="sm" onClick={() => handleToast("default")}>
                          <Calendar size={16} /> Today
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => handleToast("default")}>
                          <Calendar size={16} /> Week
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => handleToast("default")}>
                          <Calendar size={16} /> Month
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => handleToast("default")}>
                          <Calendar size={16} /> Year
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              </>
            )}

            {/* Data Components */}
            {selectedCategory === "all" || selectedCategory === "data" && (
              <>
                <h2 className="font-bold text-xl mb-4">Data Components</h2>

                <div className="space-y-6">
                  {/* Card Examples */}
                  <div className="space-y-4">
                    <h3 className="font-medium mb-2">Cards</h3>
                    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                      <Card className="border-l-4 border-primary">
                        <CardHeader className="pb-2">
                          <CardTitle className="text-sm font-medium text-text-secondary">
                            Total Investigations
                          </CardTitle>
                        </CardHeader>
                        <CardContent className="p-4">
                          <div className="flex items-center justify-between">
                            <div>
                              <h3 className="text-2xl font-bold">1,247</h3>
                              <p className="text-xs text-text-tertiary">+12% from last month</p>
                            </div>
                            <Users size={24} className="text-primary" />
                          </div>
                        </CardContent>
                      </Card>
                      <Card className="border-l-4 border-success">
                        <CardHeader className="pb-2">
                          <CardTitle className="text-sm font-medium text-text-secondary">
                            Avg Resolution Time
                          </CardTitle>
                        </CardHeader>
                        <CardContent className="p-4">
                          <div className="flex items-center justify-between">
                            <div>
                              <h3 className="text-2xl font-bold">4.2 days</h3>
                              <p className="text-xs text-text-tertiary">-8% improvement</p>
                            </div>
                            <Clock size={24} className="text-success" />
                          </div>
                        </CardContent>
                      </Card>
                      <Card className="border-l-4 border-warning">
                        <CardHeader className="pb-2">
                          <CardTitle className="text-sm font-medium text-text-secondary">
                            Escalation Rate
                          </CardTitle>
                        </CardHeader>
                        <CardContent className="p-4">
                          <div className="flex items-center justify-between">
                            <div>
                              <h3 className="text-2xl font-bold">15.3%</h3>
                              <p className="text-xs text-text-tertiary">+3% increase</p>
                            </div>
                            <Zap size={24} className="text-warning" />
                          </div>
                        </CardContent>
                      </Card>
                    </div>
                  </div>

                  {/* Table Examples */}
                  <div className="space-y-4">
                    <h3 className="font-medium mb-2">Data Table</h3>
                    <div className="overflow-x-auto">
                      <Table>
                        <Header>
                          <HeaderRow>
                            <HeaderCell className="w-12">
                              <Checkbox
                                checked={false}
                                onChange={() => {}}
                              />
                            </HeaderCell>
                            <HeaderCell>Investigation ID</HeaderCell>
                            <HeaderCell>Type</HeaderCell>
                            <HeaderCell>Risk Level</HeaderCell>
                            <HeaderCell>Status</HeaderCell>
                            <HeaderCell className="text-right">Actions</HeaderCell>
                          </HeaderRow>
                        </Header>
                        <Body>
                          {[1, 2, 3, 4, 5].map((i) => (
                            <Row key={`investigation-${i}`} className="hover:bg-white/5">
                              <Cell className="w-12">
                                <Checkbox
                                  checked={false}
                                  onChange={() => {}}
                                />
                              </Cell>
                              <Cell className="font-mono">INV-7849{i}</Cell>
                              <Cell>
                                {["Transaction Fraud", "Identity Theft", "Money Laundering", "Cyber Fraud", "Insurance Fraud"][i % 5]}
                              </Cell>
                              <Cell>
                                <Badge
                                  variant={["Low", "Medium", "High", "Critical"][i % 4] === "Critical" ? "destructive" :
                                         ["Low", "Medium", "High", "Critical"][i % 4] === "High" ? "warning" : "secondary"
                                }>
                                  {["Low", "Medium", "High", "Critical"][i % 4]}
                                </Badge>
                              </Cell>
                              <Cell>
                                {["Pending Review", "Investigating", "Escalated", "Cleared", "Escalated"][i % 5]}
                              </Cell>
                              <Cell className="text-right space-x-2">
                                <Button variant="outline" size="xs" onClick={() => handleToast("default")}>
                                  <Eye size={12} /> View
                                </Button>
                                <Button variant="outline" size="xs" onClick={() => handleToast("default")}>
                                  <Edit size={12} /> Edit
                                </Button>
                              </Cell>
                            </Row>
                          ))}
                        </Body>
                      </Table>
                    </div>
                  </div>

                  {/* Badge Examples */}
                  <div className="space-y-4">
                    <h3 className="font-medium mb-2">Badges</h3>
                    <div className="flex flex-wrap gap-2">
                      <Badge variant="default">Default</Badge>
                      <Badge variant="secondary">Secondary</Badge>
                      <Badge variant="destructive">Destructive</Badge>
                      <Badge variant="warning">Warning</Badge>
                      <Badge variant="success">Success</Badge>

                      {/* Size variants */}
                      <Badge variant="default" className="text-xs">Small</Badge>
                      <Badge variant="default">Default</Badge>
                      <Badge variant="default" className="text-lg">Large</Badge>
                    </div>
                  </div>
                </div>
              </>
            )}

            {/* Feedback Components */}
            {selectedCategory === "all" || selectedCategory === "feedback" && (
              <>
                <h2 className="font-bold text-xl mb-4">Feedback Components</h2>

                <div className="space-y-6">
                  {/* Alert Examples */}
                  <div className="space-y-4">
                    <h3 className="font-medium mb-2">Alerts</h3>
                    <div className="space-y-4">
                      <Alert variant="default" title="Info Alert" description="This is an informational alert." />
                      <Alert variant="success" title="Success Alert" description="Operation completed successfully." />
                      <Alert variant="warning" title="Warning Alert" description="Please review this warning." />
                      <Alert variant="destructive" title="Error Alert" description="An error occurred during processing." />
                    </div>
                  </div>

                  {/* Progress Examples (conceptual) */}
                  <div className="space-y-4">
                    <h3 className="font-medium mb-2">Progress Indicators</h3>
                    <div className="space-y-4">
                      <div className="space-y-2">
                        <p className="text-xs font-medium text-text-secondary">File Upload Progress</p>
                        <div className="w-full bg-white/10 rounded-full h-2.5">
                          <div className="bg-primary h-2.5 rounded-full transition-all duration-500" style={{ width: "65%" }}></div>
                        </div>
                        <p className="text-xs text-text-tertiary text-right">65%</p>
                      </div>
                      <div className="space-y-2">
                        <p className="text-xs font-medium text-text-secondary">Processing (Indeterminate)</p>
                        <div className="flex items-center space-x-3">
                          <div className="h-2 w-2 bg-primary animate-pulse rounded-full"></div>
                          <div className="h-2 w-2 bg-primary animate-pulse rounded-full"></div>
                          <div className="h-2 w-2 bg-primary animate-pulse rounded-full"></div>
                          <span className="text-xs text-text-tertiary">Processing...</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </>
            )}

            {/* Navigation Components */}
            {selectedCategory === "all" || selectedCategory === "navigation" && (
              <>
                <h2 className="font-bold text-xl mb-4">Navigation Components</h2>

                <div className="space-y-6">
                  {/* Breadcrumb */}
                  <div className="space-y-4">
                    <h3 className="font-medium mb-2">Breadcrumb</h3>
                    <nav className="space-y-2" aria-label="breadcrumb">
                      <ol className="flex items-center space-x-2 text-sm text-text-tertiary">
                        <li>
                          <a href="#" className="hover:text-white">Dashboard</a>
                        </li>
                        <li>
                          <Separator orientation="vertical" className="h-4" />
                        </li>
                        <li>
                          <a href="#" className="hover:text-white">Investigations</a>
                        </li>
                        <li>
                          <Separator orientation="vertical" className="h-4" />
                        </li>
                        <li>
                          <span className="text-white">Investigation Details</span>
                        </li>
                      </ol>
                    </nav>
                  </div>

                  {/* Tabs (conceptual) */}
                  <div className="space-y-4">
                    <h3 className="font-medium mb-2">Tabs</h3>
                    <div className="space-y-4">
                      <div className="flex border-b border-glass-border mb-4">
                        <button
                          className={`px-4 py-2 text-sm font-medium ${selectedValue === "overview" ? "text-white border-b-2 border-primary" : "text-text-secondary hover:text-white"}`}
                          onClick={() => setSelectedValue("overview")}
                        >
                          Overview
                        </button>
                        <button
                          className={`px-4 py-2 text-sm font-medium ${selectedValue === "details" ? "text-white border-b-2 border-primary" : "text-text-secondary hover:text-white"}`}
                          onClick={() => setSelectedValue("details")}
                        >
                          Details
                        </button>
                        <button
                          className={`px-4 py-2 text-sm font-medium ${selectedValue === "activity" ? "text-white border-b-2 border-primary" : "text-text-secondary hover:text-white"}`}
                          onClick={() => setSelectedValue("activity")}
                        >
                          Activity Log
                        </button>
                      </div>
                      <div className="p-4 bg-white/5 rounded-lg">
                        {selectedValue === "overview" && (
                          <p>Overview tab content would go here...</p>
                        )}
                        {selectedValue === "details" && (
                          <p>Details tab content would go here...</p>
                        )}
                        {selectedValue === "activity" && (
                          <p>Activity log tab content would go here...</p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </>
            )}

            {/* Overlay Components */}
            {selectedCategory === "all" || selectedCategory === "overlay" && (
              <>
                <h2 className="font-bold text-xl mb-4">Overlay Components</h2>

                <div className="space-y-6">
                  {/* Modal Examples (conceptual) */}
                  <div className="space-y-4">
                    <h3 className="font-medium mb-2">Modals & Dialogs</h3>
                    <div className="space-y-4">
                      <Button
                        variant="default"
                        size="sm"
                        onClick={() => setIsOpen(true)}
                      >
                        Open Modal
                      </Button>

                      {/* Modal Portal would go here in a real implementation */}
                      {isOpen && (
                        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
                          <div className="bg-white/90 rounded-lg p-6 w-96 max-w-[90vw] mx-4">
                            <div className="flex items-start justify-between mb-4">
                              <h3 className="font-medium">Confirm Action</h3>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setIsOpen(false)}
                                className="p-1"
                                aria-label="Close"
                              >
                                <X size={16} />
                              </Button>
                            </div>
                            <p className="text-text-tertiary mb-4">
                              Are you sure you want to perform this action? This cannot be undone.
                            </p>
                            <div className="flex justify-end space-x-3">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setIsOpen(false)}
                              >
                                Cancel
                              </Button>
                              <Button
                                variant="destructive"
                                size="sm"
                                onClick={() => setIsOpen(false)}
                              >
                                Delete Permanently
                              </Button>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Dropdown Menu Examples (conceptual) */}
                  <div className="space-y-4">
                    <h3 className="font-medium mb-2">Dropdown Menus</h3>
                    <div className="relative">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setIsOpen(!isOpen)}
                      >
                        Actions <ChevronLeft size={14} />
                      </Button>

                      {/* Dropdown Portal would go here in a real implementation */}
                      {isOpen && (
                        <div className="absolute right-0 mt-2 w-48 bg-white/90 border border-glass-border rounded-lg shadow-lg z-20">
                          <div className="space-y-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              className="w-full text-left p-3 hover:bg-white/20"
                              onClick={() => {
                                setIsOpen(false);
                                handleToast("default");
                              }}
                            >
                              <Edit size={16} className="mr-2" /> Edit
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="w-full text-left p-3 hover:bg-white/20"
                              onClick={() => {
                                setIsOpen(false);
                                handleToast("warning");
                              }}
                            >
                              <AlertTriangle size={16} className="mr-2" /> Duplicate
                            </Button>
                            <Separator className="my-1" />
                            <Button
                              variant="ghost"
                              size="sm"
                              className="w-full text-left p-3 hover:bg-white/20"
                              onClick={() => {
                                setIsOpen(false);
                                handleToast("destructive");
                              }}
                            >
                              <Trash2 size={16} className="mr-2" /> Delete
                            </Button>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Tooltip Examples (conceptual) */}
                  <div className="space-y-4">
                    <h3 className="font-medium mb-2">Tooltips</h3>
                    <div className="space-y-4">
                      <div className="relative inline-block">
                        <Button
                          variant="outline"
                          size="sm"
                        >
                          Help Icon
                          {/* Tooltip would appear here in real implementation */}
                          {/* Typically implemented with a library like floating-ui or as a separate component */}
                        </Button>
                        <p className="absolute bottom-full left-0 mb-2 text-xs bg-white/90 p-2 rounded border border-glass-border">
                          Click for help documentation
                        </p>
                      </div>

                      <Button
                        variant="outline"
                        size="sm"
                        className="mt-4"
                      >
                        Settings
                        {/* Tooltip would appear here in real implementation */}
                        <p className="absolute bottom-full left-0 mb-2 text-xs bg-white/90 p-2 rounded border border-glass-border">
                          User settings and preferences
                        </p>
                      </Button>
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default ComponentLibrary;