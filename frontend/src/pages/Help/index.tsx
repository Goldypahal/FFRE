import { useState, useMemo } from "react";
import { Header as LayoutHeader } from "../../components/layout/Header";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../../components/ui/Select";
import { Checkbox } from "../../components/ui/Checkbox";
import { Badge } from "../../components/ui/Badge";
import { Card, CardHeader, CardTitle, CardContent } from "../../components/ui/Card";
import { Table, TableBody, Cell, Header, Body, HeaderCell, HeaderRow, Row } from "../../components/ui/Table";
import {
  HelpCircle, Search, BookOpen, FileText, Play, Share2, MessageCircle,
  Users, Settings, Bell, AlertTriangle, ClipboardList, Calendar, TrendingUp,
  Zap, Shield, Code, Menu, X, Plug, List, Grid, Plus, Eye, ThumbsUp, ThumbsDown, UserPlus
} from "lucide-react";

// Help article type
interface HelpArticle {
  id: string;
  title: string;
  category: string;
  content: string; // In reality, this would be rich text or markdown
  updatedAt: string; // ISO date
  views: number;
  helpful: number; // Count of helpful votes
  notHelpful: number; // Count of not helpful votes
  tags: string[];
  isFeatured: boolean;
  relatedArticles: string[]; // IDs
}

// Help category type
interface HelpCategory {
  id: string;
  name: string;
  icon: React.ComponentType<any>;
  articleCount: number;
}

// Support ticket type
interface SupportTicket {
  id: string;
  title: string;
  category: string;
  priority: "low" | "medium" | "high" | "urgent";
  status: "open" | "in-progress" | "resolved" | "closed";
  createdAt: string; // ISO date
  updatedAt: string; // ISO date
  assignedTo: string | null;
  tags: string[];
  description?: string;
}

// Mock help articles
const MOCK_ARTICLES: HelpArticle[] = [
  {
    id: "help-001",
    title: "Getting Started with FFIRE",
    category: "getting-started",
    content: "Welcome to FFIRE! This guide will help you get started with the Financial Fraud Investigation Reasoning Engine. You'll learn how to create your first investigation, collect evidence, and generate reports.",
    updatedAt: "2024-01-10T09:00:00Z",
    views: 1240,
    helpful: 98,
    notHelpful: 5,
    tags: ["getting-started", "tutorial", "beginner"],
    isFeatured: true,
    relatedArticles: ["help-002", "help-003"]
  },
  {
    id: "help-002",
    title: "Creating Your First Investigation",
    category: "getting-started",
    content: "Learn how to create a new investigation in FFIRE. You can start an investigation from the dashboard, from an alert, or by entering a transaction ID manually.",
    updatedAt: "2024-01-12T14:30:00Z",
    views: 890,
    helpful: 76,
    notHelpful: 3,
    tags: ["investigation", "tutorial", "create"],
    isFeatured: true,
    relatedArticles: ["help-001", "help-004"]
  },
  {
    id: "help-003",
    title: "Understanding Investigation Statuses",
    category: "investigations",
    content: "FFIRE uses several statuses to track the progress of investigations. Understanding these statuses will help you manage your workflow effectively.",
    updatedAt: "2024-01-11T16:45:00Z",
    views: 650,
    helpful: 52,
    notHelpful: 2,
    tags: ["investigation", "status", "workflow"],
    isFeatured: false,
    relatedArticles: ["help-002", "help-005"]
  },
  {
    id: "help-004",
    title: "Collecting and Managing Evidence",
    category: "evidence",
    content: "Evidence is the foundation of any investigation. Learn how to collect, organize, and analyze evidence in FFIRE to build strong cases.",
    updatedAt: "2024-01-13T10:15:00Z",
    views: 720,
    helpful: 61,
    notHelpful: 4,
    tags: ["evidence", "collection", "management"],
    isFeatured: false,
    relatedArticles: ["help-002", "help-006"]
  },
  {
    id: "help-005",
    title: "Using the Reasoning Graph",
    category: "analysis",
    content: "The reasoning graph is FFIRE's powerful AI-powered visualization tool that shows how the system reaches its conclusions. Learn how to interpret and interact with this feature.",
    updatedAt: "2024-01-14T08:30:00Z",
    views: 580,
    helpful: 49,
    notHelpful: 1,
    tags: ["analysis", "reasoning-graph", "ai"],
    isFeatured: false,
    relatedArticles: ["help-003", "help-007"]
  },
  {
    id: "help-006",
    title: "Generating Investigation Reports",
    category: "reports",
    content: "Once your investigation is complete, you'll need to generate reports to share your findings. FFIRE supports multiple report formats including PDF, JSON, and Excel.",
    updatedAt: "2024-01-15T09:00:00Z",
    views: 410,
    helpful: 35,
    notHelpful: 2,
    tags: ["reports", "generation", "export"],
    isFeatured: false,
    relatedArticles: ["help-004", "help-008"]
  },
  {
    id: "help-007",
    title: "Setting Up Alerts and Notifications",
    category: "alerts",
    content: "Stay informed about important events in your investigations with FFIRE's alerting system. Configure email, in-app, and SMS notifications for various event types.",
    updatedAt: "2024-01-09T11:20:00Z",
    views: 320,
    helpful: 28,
    notHelpful: 0,
    tags: ["alerts", "notifications", "setup"],
    isFeatured: false,
    relatedArticles: ["help-005", "help-009"]
  },
  {
    id: "help-008",
    title: "Managing User Roles and Permissions",
    category: "administration",
    content: "As an administrator, you'll need to manage user roles and permissions to ensure proper access control throughout your organization.",
    updatedAt: "2024-01-08T15:45:00Z",
    views: 210,
    helpful: 18,
    notHelpful: 1,
    tags: ["administration", "roles", "permissions"],
    isFeatured: false,
    relatedArticles: ["help-006"]
  },
  {
    id: "help-009",
    title: "Integrating Third-Party Services",
    category: "integrations",
    content: "FFIRE supports integration with various third-party services including CRM systems, credit bureaus, and law enforcement databases.",
    updatedAt: "2024-01-07T13:30:00Z",
    views: 180,
    helpful: 15,
    notHelpful: 0,
    tags: ["integrations", "setup", "api"],
    isFeatured: false,
    relatedArticles: ["help-007"]
  }
];

// Mock help categories
const MOCK_CATEGORIES: HelpCategory[] = [
  { id: "getting-started", name: "Getting Started", icon: Play, articleCount: 2 },
  { id: "investigations", name: "Investigations", icon: ClipboardList, articleCount: 2 },
  { id: "evidence", name: "Evidence Management", icon: FileText, articleCount: 1 },
  { id: "analysis", name: "Analysis & Reasoning", icon: Zap, articleCount: 1 },
  { id: "reports", name: "Reports & Export", icon: FileText, articleCount: 1 },
  { id: "alerts", name: "Alerts & Notifications", icon: Bell, articleCount: 1 },
  { id: "administration", name: "Administration", icon: Settings, articleCount: 2 },
  { id: "integrations", name: "Integrations", icon: Plug, articleCount: 1 }
];

// Mock support tickets
const MOCK_TICKETS: SupportTicket[] = [
  {
    id: "ticket-001",
    title: "Unable to upload large evidence files",
    category: "technical",
    priority: "high",
    status: "open",
    createdAt: "2024-01-14T10:30:00Z",
    updatedAt: "2024-01-14T10:30:00Z",
    assignedTo: "support-team@ffire.ai",
    tags: ["upload", "file-size", "technical"]
  },
  {
    id: "ticket-002",
    title: "Question about report formatting options",
    category: "general",
    priority: "medium",
    status: "in-progress",
    createdAt: "2024-01-13T14:15:00Z",
    updatedAt: "2024-01-14T09:00:00Z",
    assignedTo: "docs-team@ffire.ai",
    tags: ["reports", "formatting", "pdf"]
  },
  {
    id: "ticket-003",
    title: "How to configure SSO with Azure AD?",
    category: "security",
    priority: "medium",
    status: "open",
    createdAt: "2024-01-12T09:45:00Z",
    updatedAt: "2024-01-12T09:45:00Z",
    assignedTo: null,
    tags: ["sso", "azure", "authentication"]
  }
];

export function Help() {
  const [activeTab, setActiveTab] = useState<"knowledge-base" | "contact-support">("knowledge-base");
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [viewMode, setViewMode] = useState<"list" | "grid">("list");
  const [selectedArticle, setSelectedArticle] = useState<HelpArticle | null>(null);

  // Filter articles based on search, category, and selection
  const filteredArticles = useMemo(() => {
    return MOCK_ARTICLES.filter(article => {
      // Text search
      if (searchTerm.trim()) {
        const searchableText = `${article.title} ${article.content} ${article.tags.join(' ')}`.toLowerCase();
        const term = searchTerm.toLowerCase();
        if (!searchableText.includes(term)) return false;
      }

      // Category filter
      if (selectedCategory && article.category !== selectedCategory) return false;

      return true;
    });
  }, [searchTerm, selectedCategory]);

  // Handle article selection
  const handleArticleSelect = (article: HelpArticle | null) => {
    setSelectedArticle(article);
    // In a real implementation, we might increment view count here
  };

  // Handle category selection
  const handleCategorySelect = (category: string | null) => {
    setSelectedCategory(category);
    setSelectedArticle(null); // Reset article selection when category changes
  };

  // Handle search
  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  };

  // Clear search and filters
  const clearFilters = () => {
    setSearchTerm("");
    setSelectedCategory(null);
    setSelectedArticle(null);
  };

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
          <h3 className="font-headline-md text-headline-md text-on-surface">Help & Support</h3>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="h-8 w-8 p-1"
          >
            <Menu size={16} />
          </Button>
        </div>

        <div className="p-4 space-y-6 overflow-auto h-full">
          {/* Search */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-on-surface-variant">Search Help</label>
            <Input
              placeholder="Search articles, tutorials, documentation..."
              value={searchTerm}
              onChange={handleSearch}
              className="w-full bg-surface-container-low border border-outline-variant"
            />
          </div>

          {/* Categories */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-on-surface-variant">Topics</label>
            <div className="space-y-1">
              {MOCK_CATEGORIES.map((category) => (
                <button
                  key={category.id}
                  onClick={() => handleCategorySelect(category.id)}
                  className={`${selectedCategory === category.id ? "text-on-surface bg-surface-container-high" : "text-on-surface-variant hover:text-on-surface"}
                            flex w-full items-center gap-3 p-3 rounded-lg transition-colors`}
                >
                  <div className="flex-shrink-0">
                    <category.icon size={16} className={`text-${selectedCategory === category.id ? "on-surface" : "on-surface-variant"}`} />
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-on-surface">{category.name}</p>
                    <p className="text-xs text-on-surface-variant">{category.articleCount} articles</p>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* View Mode Toggle */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-on-surface-variant">View As</label>
            <div className="flex gap-2">
              <Button
                variant={viewMode === "list" ? "default" : "outline"}
                size="sm"
                onClick={() => setViewMode("list")}
                aria-label="List view"
                className="bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
              >
                <List size={14} />
              </Button>
              <Button
                variant={viewMode === "grid" ? "default" : "outline"}
                size="sm"
                onClick={() => setViewMode("grid")}
                aria-label="Grid view"
                className="bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
              >
                <Grid size={14} />
              </Button>
            </div>
          </div>

          {/* Clear Filters Button */}
          <div className="pt-4 border-t border-outline-variant">
            <Button
              variant="outline"
              size="sm"
              onClick={clearFilters}
              className="w-full bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
            >
              <X size={14} className="mr-1" /> Clear Filters
            </Button>
          </div>

          {/* Support Ticket Section */}
          <div className="mt-6 pt-4 border-t border-outline-variant">
            <h3 className="font-medium mb-3 text-on-surface">Need More Help?</h3>
            <p className="text-on-surface-variant">Can't find what you're looking for?</p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setActiveTab("contact-support")}
              className="w-full bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
            >
              <MessageCircle size={16} className="mr-1" /> Contact Support
            </Button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <LayoutHeader
          title="Help & Documentation"
          rightContent={
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={() => setIsSidebarOpen(true)}>
                <Menu size={16} className="mr-1" /> Navigation
              </Button>
              <Button
                variant="default"
                size="sm"
                onClick={() => {
                  // New article button (for admins/contributors)
                  alert("Create new help article");
                }}
              >
                <Plus size={16} className="mr-1" /> Contribute
              </Button>
            </div>
          }
        />

        <div className="flex-1 overflow-auto p-6">
          {activeTab === "knowledge-base" && (
            <KnowledgeBaseSection
              articles={filteredArticles}
              categories={MOCK_CATEGORIES}
              selectedArticle={selectedArticle}
              onArticleSelect={handleArticleSelect}
              viewMode={viewMode}
            />
          )}

          {activeTab === "contact-support" && (
            <ContactSupportSection
              tickets={MOCK_TICKETS}
            />
          )}
        </div>
      </div>
    </div>
  );
}

// Knowledge Base Section
function KnowledgeBaseSection({
  articles,
  categories,
  selectedArticle,
  onArticleSelect,
  viewMode
}: {
  articles: HelpArticle[];
  categories: HelpCategory[];
  selectedArticle: HelpArticle | null;
  onArticleSelect: (article: HelpArticle | null) => void;
  viewMode: "list" | "grid";
}) {
  return (
    <div className="space-y-6">
      {/* Featured Articles */}
      {!selectedArticle && (
        <div className="space-y-4">
          <h2 className="font-headline-lg text-headline-lg text-on-surface">Featured Articles</h2>
          <div className="space-y-4">
            {viewMode === "list" ? (
              <div className="space-y-3">
                {articles
                  .filter(article => article.isFeatured)
                  .slice(0, 3)
                  .map((article) => (
                    <ArticlePreview
                      key={article.id}
                      article={article}
                      onSelect={onArticleSelect}
                    />
                  ))}
              </div>
            ) : (
              <div className="grid gap-4">
                {articles
                  .filter(article => article.isFeatured)
                  .slice(0, 3)
                  .map((article) => (
                    <ArticlePreview
                      key={article.id}
                      article={article}
                      onSelect={onArticleSelect}
                    />
                  ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Article List or Grid */}
      {!selectedArticle && (
        <div className="space-y-4">
          <h2 className="font-headline-lg text-headline-lg text-on-surface">Help Articles</h2>
          <p className="text-body-lg text-on-surface-variant">
            {articles.length} articles {
              articles.length === 1 ? "was" : "were"
            } found
          </p>
          <div className="space-y-4">
            {viewMode === "list" ? (
              <div className="space-y-3">
                {articles.map((article) => (
                  <ArticleListItem
                    key={article.id}
                    article={article}
                    onSelect={onArticleSelect}
                  />
                ))}
              </div>
            ) : (
              <div className="grid gap-4">
                {articles.map((article) => (
                  <ArticlePreview
                    key={article.id}
                    article={article}
                    onSelect={onArticleSelect}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Selected Article View */}
      {selectedArticle && (
        <ArticleDetail
          article={selectedArticle}
          onClose={() => onArticleSelect(null)}
        />
      )}
    </div>
  );
}

// Contact Support Section
function ContactSupportSection({
  tickets
}: {
  tickets: SupportTicket[];
}) {
  const [newTicket, setNewTicket] = useState({
    title: "",
    category: "",
    priority: "medium" as const,
    description: ""
  });

  const [ticketCategories] = useState([
    { id: "technical", name: "Technical Issue" },
    { id: "general", name: "General Question" },
    { id: "billing", name: "Billing & Account" },
    { id: "feature", name: "Feature Request" },
    { id: "security", name: "Security Concern" }
  ]);

  const handleChange = (field: keyof typeof newTicket, value: any) => {
    setNewTicket(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // In a real app, this would submit the ticket to the API
    alert("Support ticket submitted successfully!");
    setNewTicket({
      title: "",
      category: "",
      priority: "medium" as const,
      description: ""
    });
  };

  return (
    <div className="space-y-6">
      <h2 className="font-headline-lg text-headline-lg text-on-surface">Contact Support</h2>
      <p className="text-body-lg text-on-surface-variant">
        Our support team is available to help you with any questions or issues.
        You can browse existing tickets or submit a new one.
      </p>

      {/* Existing Tickets */}
      <div className="space-y-4">
        <h3 className="font-label-md text-label-md text-on-surface">Recent Support Tickets</h3>
        <div className="space-y-4">
          <div className="overflow-x-auto">
            <Table>
              <Header>
                <HeaderRow>
                  <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Ticket ID</HeaderCell>
                  <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Title</HeaderCell>
                  <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Category</HeaderCell>
                  <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Priority</HeaderCell>
                  <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Status</HeaderCell>
                  <HeaderCell className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left text-right">Actions</HeaderCell>
                </HeaderRow>
              </Header>
              <Body>
                {tickets.length === 0 ? (
                  <Row>
                    <Cell colSpan={6} className="p-8 text-center text-on-surface-variant">
                      <MessageCircle size={32} className="mx-auto mb-4 opacity-50" />
                      <p className="text-center text-on-surface-variant">No support tickets found</p>
                    </Cell>
                  </Row>
                ) : (
                  tickets.map((ticket) => (
                    <TicketListItem
                      key={ticket.id}
                      ticket={ticket}
                    />
                  ))
                )}
              </Body>
            </Table>
          </div>
        </div>
      </div>

      {/* New Ticket Form */}
      <div className="space-y-4">
        <h3 className="font-label-md text-label-md text-on-surface">Submit a Support Ticket</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label className="text-xs font-medium text-on-surface-variant">Title</label>
            <Input
              value={newTicket.title}
              onChange={(e) => handleChange("title", e.target.value)}
              placeholder="Briefly describe your issue or question"
              className="w-full bg-surface-container-low border border-outline-variant"
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium text-on-surface-variant">Category</label>
            <Select
              value={newTicket.category}
              onValueChange={(value) => handleChange("category", value)}
              className="w-full bg-surface-container-low border border-outline-variant"
            >
              <SelectValue placeholder="Select category" />
              {ticketCategories.map((cat) => (
                <SelectItem key={cat.id} value={cat.id}>
                  {cat.name}
                </SelectItem>
              ))}
            </Select>
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium text-on-surface-variant">Priority</label>
            <Select
              value={newTicket.priority}
              onValueChange={(value) => handleChange("priority", value)}
              className="w-full bg-surface-container-low border border-outline-variant"
            >
              <SelectValue placeholder="Select priority" />
              <SelectItem value="low">Low</SelectItem>
              <SelectItem value="medium">Medium</SelectItem>
              <SelectItem value="high">High</SelectItem>
              <SelectItem value="urgent">Urgent</SelectItem>
            </Select>
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium text-on-surface-variant">Description</label>
            <textarea
              value={newTicket.description}
              onChange={(e) => handleChange("description", e.target.value)}
              className="w-full min-h-[96px] p-3 bg-surface-container-low border border-outline-variant rounded-lg"
              placeholder="Please provide as much detail as possible..."
            />
          </div>
          <div className="flex justify-end">
            <Button
              variant="outline"
              size="sm"
              onClick={(e) => {
                e.preventDefault();
                setNewTicket({
                  title: "",
                  category: "",
                  priority: "medium" as const,
                  description: ""
                });
              }}
              className="bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
            >
              Cancel
            </Button>
            <Button
              variant="default"
              size="sm"
              onClick={handleSubmit}
              className="bg-investment-gold text-surface hover:bg-investment-gold/90"
            >
              Submit Ticket
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

// Article Preview (for grid view)
function ArticlePreview({
  article,
  onSelect
}: {
  article: HelpArticle;
  onSelect: (article: HelpArticle) => void;
}) {
  return (
    <div
      className="group
                rounded-lg
                border border
                p-4
                hover:bg-surface-container-high
                transition-colors
                cursor-pointer"
      onClick={() => onSelect(article)}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h4 className="font-label-md text-label-md text-on-surface">{article.title}</h4>
          <p className="text-xs text-on-surface-variant mb-2">
            {article.category.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
          </p>
          <p className="line-clamp-2 text-on-surface-variant">{article.content.substring(0, 100)}...</p>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <div className="flex items-center gap-1">
            <Eye size={12} className="mr-1 text-on-surface-variant" />
            <span>{article.views} views</span>
          </div>
          <div className="flex items-center gap-1">
            <ThumbsUp size={12} className="mr-1 text-emerald-500" />
            <span>{article.helpful}</span>
            <ThumbsDown size={12} className="ml-1 mr-1 text-rose-500" />
            <span>{article.notHelpful}</span>
          </div>
        </div>
      </div>
      <div className="flex items-center justify-between text-xs mt-3">
        <div className="flex items-center gap-2">
          <Calendar size={12} className="mr-1 text-on-surface-variant" />
          <span>{new Date(article.updatedAt).toLocaleDateString()}</span>
        </div>
        <div className="flex items-center gap-2">
          {article.tags.slice(0, 2).map((tag) => (
            <span
              key={tag}
              className="px-1.5 py-0.5 text-xs rounded bg-surface-container-low hover:bg-surface-container-high"
            >
              #{tag}
            </span>
          ))}
          {article.tags.length > 2 && (
            <span className="px-1.5 py-0.5 text-xs rounded bg-surface-container-low hover:bg-surface-container-high">
              +{article.tags.length - 2} more
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

// Article List Item (for list view)
function ArticleListItem({
  article,
  onSelect
}: {
  article: HelpArticle;
  onSelect: (article: HelpArticle) => void;
}) {
  return (
    <div
      className="group
                flex items-start justify-between
                p-4
                hover:bg-surface-container-high
                transition-colors
                cursor-pointer"
      onClick={() => onSelect(article)}
    >
      <div className="flex-1">
        <h4 className="font-label-md text-label-md text-on-surface">{article.title}</h4>
        <p className="text-xs text-on-surface-variant mb-2">
          {article.category.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
        </p>
        <p className="text-on-surface-variant line-clamp-3">
          {article.content}
        </p>
      </div>
      <div className="flex items-end gap-3 text-xs">
        <div className="flex items-center space-x-2">
          <div className="flex items-center gap-1">
            <Eye size={12} className="mr-1 text-on-surface-variant" />
            <span>{article.views}</span>
          </div>
          <div className="flex items-center gap-1">
            <ThumbsUp size={12} className="mr-1 text-emerald-500" />
            <span>{article.helpful}</span>
            <ThumbsDown size={12} className="ml-1 mr-1 text-rose-500" />
            <span>{article.notHelpful}</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Calendar size={12} className="mr-1 text-on-surface-variant" />
          <span>{new Date(article.updatedAt).toLocaleDateString()}</span>
        </div>
      </div>
    </div>
  );
}

// Article Detail View
function ArticleDetail({
  article,
  onClose
}: {
  article: HelpArticle;
  onClose: () => void;
}) {
  const helpfulPercentage =
    article.helpful + article.notHelpful > 0
      ? Math.round((article.helpful / (article.helpful + article.notHelpful)) * 100)
      : 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-headline-lg text-headline-lg text-on-surface">{article.title}</h2>
        <Button
          variant="outline"
          size="sm"
          onClick={onClose}
          className="p-2"
          aria-label="Close article"
        >
          <X size={16} />
        </Button>
      </div>

      <div className="space-y-4">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0">
            <BookOpen size={20} className="text-on-surface-variant" />
          </div>
          <div className="flex-1">
            <p className="text-xs text-on-surface-variant">
              {article.category.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase())} •
              {new Date(article.updatedAt).toLocaleDateString()} •
              {article.views} views
            </p>
          </div>
        </div>
        <div className="prose max-w-none">
          <p>{article.content}</p>
          {article.tags.length > 0 && (
            <div className="mt-4">
              <h4 className="font-label-md text-label-md text-on-surface mb-2">Tags</h4>
              <div className="flex flex-wrap gap-2">
                {article.tags.map((tag) => (
                  <span
                    key={tag}
                    className="px-2 py-0.5 text-xs rounded bg-surface-container-low hover:bg-surface-container-high"
                  >
                    #{tag}
                  </span>
                ))}
              </div>
            </div>
          )}
          {article.relatedArticles.length > 0 && (
            <div className="mt-4">
              <h4 className="font-label-md text-label-md text-on-surface mb-2">Related Articles</h4>
              <div className="space-y-2">
                {article.relatedArticles.map((relatedId) => {
                  const relatedArticle = MOCK_ARTICLES.find(
                    (a) => a.id === relatedId
                  );
                  if (!relatedArticle) return null;
                  return (
                    <div
                      key={relatedId}
                      className="flex items-start gap-3 p-4 bg-surface-container-low border border-outline-variant rounded-lg hover:bg-surface-container-high transition-colors cursor-pointer"
                      onClick={() => {
                        // In a real app, this would navigate to the related article
                        alert(`Viewing related article: ${relatedArticle.title}`);
                      }}
                    >
                      <div className="flex-shrink-0">
                        <HelpCircle size={14} className="mr-2 text-on-surface-variant" />
                      </div>
                      <div className="flex-1">
                        <p className="font-label-md text-label-md text-on-surface">{relatedArticle.title}</p>
                        <p className="text-xs text-on-surface-variant">
                          {relatedArticle.category.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                        </p>
                      </div>
                    </div>
                  );
                }).filter(Boolean)}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Feedback Section */}
      <div className="mt-6 p-4 bg-surface-container-low border border-outline-variant rounded-lg">
        <h3 className="font-label-md text-label-md text-on-surface mb-3">Was this article helpful?</h3>
        <div className="flex gap-2">
          <Button
            variant={helpfulPercentage > 0 ? "default" : "outline"}
            size="sm"
            onClick={() => {
              // In a real app, this would send feedback to the API
              alert("Thanks for your feedback!");
            }}
            className="bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
          >
            <ThumbsUp size={16} className="mr-1" /> Yes ({helpfulPercentage}%)
          </Button>
          <Button
            variant={helpfulPercentage > 0 ? "outline" : "default"}
            size="sm"
            onClick={() => {
              // In a real app, this would send feedback to the API
              alert("Thanks for your feedback!");
            }}
            className="bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
          >
            <ThumbsDown size={16} className="mr-1" /> No ({100 - helpfulPercentage}%)
          </Button>
        </div>
      </div>
    </div>
  );
}

// Ticket List Item
function TicketListItem({
  ticket
}: {
  ticket: SupportTicket;
}) {
  return (
    <div className="p-4 bg-surface-container-low border border-outline-variant rounded-lg">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 space-y-1">
          <p className="font-label-md text-label-md text-on-surface">{ticket.title}</p>
          <p className="text-xs text-on-surface-variant">
            #{ticket.id} • {ticket.category} • {new Date(ticket.createdAt).toLocaleDateString()}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${ticket.priority === "urgent" ? "bg-rose-500" :
                     ticket.priority === "high" ? "bg-amber-500" :
                     ticket.priority === "medium" ? "bg-yellow-400" : "bg-emerald-500"}`} />
          <span className="text-xs text-on-surface-variant capitalize">
            {ticket.priority}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${ticket.status === "resolved" || ticket.status === "closed" ? "bg-emerald-500" :
                     ticket.status === "in-progress" ? "bg-amber-500" : "bg-rose-500"}`} />
          <span className="text-xs text-on-surface-variant capitalize">
            {ticket.status}
          </span>
        </div>
      </div>
      <div className="mt-2 p-3 bg-surface-container-low rounded">
        <p className="text-xs text-on-surface-variant">{ticket.description}</p>
      </div>
      <div className="flex items-end mt-3">
        {ticket.assignedTo && (
          <span className="text-xs text-on-surface-variant">
            Assigned to: {ticket.assignedTo}
          </span>
        )}
        {!ticket.assignedTo && ticket.status === "open" && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              // Assign ticket to self
              alert("Ticket assigned to you");
            }}
            className="p-1 bg-surface-container-low hover:bg-surface-container-high border border-outline-variant"
          >
            <UserPlus size={12} className="mr-1" /> Assign to Me
          </Button>
        )}
      </div>
    </div>
  );
}


export default Help;