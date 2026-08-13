# FFRE Component Library Specification

## Overview
This document specifies the reusable UI components used throughout the Financial Fraud Investigation Reasoning Engine (FFRE) application. These components follow a consistent design system based on the specifications defined in FFIRE_Button_Specifications.md, FFIRE_Table_Specifications.md, and FFIRE_Popup_Specifications.md.

## Design Principles

### Consistency
- All components follow the same visual language and interaction patterns
- Consistent spacing, typography, and color usage across components
- Predictable behavior and feedback mechanisms

### Accessibility
- All components meet WCAG 2.1 AA accessibility standards
- Proper ARIA labels and keyboard navigation support
- Sufficient color contrast for text and interactive elements
- Focus management for interactive components

### Reusability
- Components are designed to be reusable across different contexts
- Props-driven customization for flexibility
- Clear separation of concerns between presentation and behavior

### Performance
- Optimized rendering with React.memo where appropriate
- Efficient event handling to prevent unnecessary re-renders
- Lazy loading strategies for non-critical components

## Component Categories

### 1. Layout Components
Components that define the structure and layout of pages and sections.

#### Header
- **Location**: `src/components/layout/Header.tsx`
- **Purpose**: Top navigation bar with application branding and user controls
- **Props**:
  - `title`: string - Main title displayed in the header
  - `rightContent`: ReactNode - Content to display to be rendered on the right side
  - `className?`: string - Additional CSS classes
- **Features**:
  - Responsive design (collapses to hamburger menu on mobile)
  - Application logo/branding
  - User profile dropdown
  - Notification bell indicator
  - Responsive collapse behavior

#### Sidebar
- **Location**: `src/components/layout/Sidebar.tsx`
- **Purpose**: Navigation sidebar for application sections
- **Props**:
  - `items`: Array<{ label: string, icon: React.ComponentType, href: string, active?: boolean }>
  - `onItemClick`: (item: MenuItem) => void
  - `isCollapsed`: boolean
  - `onToggle`: () => void
- **Features**:
  - Collapsible/expandable behavior
  - Icon-only mode when collapsed
  - Active item highlighting
  - Custom icon support
  - Smooth animations

### 2. Form Components
Components for user input and data collection.

#### Input
- **Location**: `src/components/ui/Input.tsx`
- **Purpose**: Text input field with label, helper text, and validation states
- **Props**:
  - `type`: string (default: "text") - Input type (text, email, password, tel, etc.)
  - `value`: string - Current value
  - `onChange`: (e: React.ChangeEvent) => void - Change handler
  - `placeholder`: string - Placeholder text
  - `label`: string - Label text
  - `helperText`: string - Helper text below input
  - `error`: string - Error message (shows error state when present)
  - `disabled`: boolean - Disabled state
  - `required`: boolean - Required field indicator
  - `className?`: string - Additional CSS classes
- **Features**:
  - Label with required indicator (*)
  - Floating label on focus (optional enhancement)
  - Error state with red border and message
  - Disabled state with appropriate styling
  - Password toggle visibility (for password type)
  - Input masking capabilities (extensible)

#### Select
- **Location**: `src/components/ui/Select.tsx`
- **Purpose**: Dropdown select component
- **Props**:
  - `value`: string | null - Selected value
  - `onValueChange`: (value: string | null) => void - Change handler
  - `placeholder`: string - Placeholder when no selection
  - `options`: Array<{ value: string, label: string }> - Available options
  - `disabled`: boolean - Disabled state
  - `className?`: string - Additional CSS classes
- **Features**:
  - Searchable dropdown (for large option lists)
  - Keyboard navigation support
  - Clear selection option (configurable)
  - Disabled state styling
  - Customizable dropdown positioning

#### Checkbox
- **Location**: `src/components/ui/Checkbox.tsx`
- **Purpose**: Single checkbox or toggle switch
- **Props**:
  - `checked`: boolean - Checked state
  - `onChange`: (checked: boolean) => void - Change handler
  - `label`: string - Label text
  - `disabled`: boolean - Disabled state
  - `indeterminate`: boolean - Indeterminate state
  - `className?`: string - Additional CSS classes
- **Features**:
  - Standard checkbox appearance
  - Switch/toggle appearance variant (via variant prop)
  - Indeterminate state for mixed selections
  - Disabled state styling
  - Label click to toggle

#### Button
- **Location**: `src/components/ui/Button.tsx`
- **Purpose**: Primary button component with multiple variants
- **Props**:
  - `variant`: "default" | "outline" | "ghost" | "destructive" - Visual style
  - `size`: "sm" | "md" | "lg" - Size variant
  - `onClick`: (e: React.MouseEvent) => void - Click handler
  - `children`: ReactNode - Button content
  - `disabled`: boolean - Disabled state
  - `className?`: string - Additional CSS classes
  - `asChild`: boolean - Render as child element (for linking)
- **Variants**:
  - **Default**: Primary action (solid background)
  - **Outline**: Secondary action (border only)
  - **Ghost**: Tertiary action (no background/border)
  - **Destructive**: Destructive action (red background)
- **Features**:
  - Loading state with spinner
  - Icon support (leading/trailing)
  - Full width option
  - Disabled state styling
  - Hover, focus, and active states

#### ButtonGroup
- **Location**: `src/components/ui/ButtonGroup.tsx`
- **Purpose**: Group of related buttons
- **Props**:
  - `children`: ReactNode - Button components
  - `className?`: string - Additional CSS classes
- **Features**:
  - Unified spacing between buttons
  - Shared hover/active states
  - Visual grouping through shared borders

### 3. Data Display Components
Components for presenting information and data.

#### Card
- **Location**: `src/components/ui/Card.tsx`
- **Purpose**: Container for grouping related content
- **Props**:
  - `className?`: string - Additional CSS classes
  - `children`: ReactNode - Card content
- **Sub-components**:
  - `CardHeader`: Header section
  - `CardTitle`: Title within header
  - `CardContent`: Main content area
- **Features**:
  - Elevated surface with shadow
  - Border radius for rounded corners
  - Flexible content layout
  - Header/content separation
  - Hover elevation effect (optional)

#### Table
- **Location**: `src/components/ui/Table.tsx`
- **Purpose**: Data table for displaying structured information
- **Props**:
  - `className?`: string - Additional CSS classes
  - `children`: ReactNode - Table content (Header, Body)
- **Sub-components**:
  - `Header`: Table header section
  - `HeaderRow`: Table header row
  - `HeaderCell`: Table header cell
  - `Body`: Table body section
  - `Row`: Table row
  - `Cell`: Table cell
- **Features**:
  - Sortable columns (via click handlers on headers)
  - Selectable rows (via checkboxes in cells)
  - Expandable rows (via expand/collapse icons)
  - Responsive design (horizontal scroll on small screens)
  - Loading and empty states
  - Custom cell rendering

#### Badge
- **Location**: `src/components/ui/Badge.tsx`
- **Purpose**: Status indicator or label
- **Props**:
  - `variant`: "default" | "secondary" | "destructive" | "warning" | "success" - Color scheme
  - `children`: ReactNode - Badge content
  - `className?`: string - Additional CSS classes
- **Variants**:
  - **Default**: Neutral/gray background
  - **Secondary**: Brand/primary color background
  - **Destructive**: Red background (for errors/warnings)
  - **Warning**: Yellow/orange background (for cautions)
  - **Success**: Green background (for success states)
- **Features**:
  - Pill-shaped or rounded rectangle
  - Text color adjustment for contrast
  - Size variations (sm, md, lg)
  - Outline variant available

#### Avatar
- **Location**: `src/components/ui/Avatar.tsx`
- **Purpose**: User avatar/image display
- **Props**:
  - `src`: string - Image URL
  - `alt`: string - Alternative text
  - `size`: "sm" | "md" | "lg" - Size variant
  - `fallback`: string - Fallback text when image fails to load
  - `className?`: string - Additional CSS classes
- **Features**:
  - Circular or square shape options
  - Fallback to initials when image fails
  - Size variations
  - Status indicator overlay (online/away/offline)
  - Group avatar stacking (for multiple users)

### 4. Feedback Components
Components for providing user feedback and notifications.

#### Alert
- **Location**: `src/components/ui/Alert.tsx`
- **Purpose**: Inline feedback message
- **Props**:
  - `variant`: "default" | "destructive" | "success" | "warning" - Message type
  - `title`: string - Alert title
  - `description`: string - Detailed message
  - `className?`: string - Additional CSS classes
- **Features**:
  - Icon based on variant
  - Dismissible option (close button)
  - Animation on appearance/dismissal
  - Accessible role="alert"

#### Toast
- **Location**: `src/components/ui/Toast.tsx`
- **Purpose**: Temporary notification popup
- **Props** (via toast() function):
  - `title`: string - Notification title
  - `description`: string - Detailed message
  - `variant`: "default" | "destructive" | "success" | "warning" - Appearance
  - `duration`: number - Display duration in ms (default: 5000)
  - `position`: "top-right" | "top-center" | "top-left" | "bottom-right" | "bottom-center" | "bottom-left" - Screen position
- **Features**:
  - Auto-dismiss after timeout
  - Pause on hover
  - Swipe to dismiss (touch devices)
  - Stacking behavior
  - Customizable positioning
  - Action button support

#### Progress
- **Location**: `src/components/ui/Progress.tsx`
- **Purpose**: Visual progress indicator
- **Props**:
  - `value`: number - Current progress (0-100)
  - `indeterminate`: boolean - Indeterminate animation
  - `size`: "sm" | "md" | "lg" - Size variant
  - `className?`: string - Additional CSS classes
- **Features**:
  - Determinate and indeterminate states
  - Animated progress fill
  - Label display option (percentage or custom text)
  - Color variants (primary, success, warning, error)

### 5. Navigation Components
Components for navigation and routing.

#### Breadcrumb
- **Location**: `src/components/ui/Breadcrumb.tsx`
- **Purpose**: Hierarchical navigation trail
- **Props**:
  - `items`: Array<{ label: string, href?: string }> - Breadcrumb items
  - `className?`: string - Additional CSS classes
- **Features**:
  - Separator between items (typically "/")
  - Current page not linked
  - Truncation for long paths
  - Accessible aria-label

#### Pagination
- **Location**: `src/components/ui/Pagination.tsx`
- **Purpose**: Page navigation for lists/tables
- **Props**:
  - `page`: number - Current page number
  - `totalPages`: number - Total number of pages
  - `onPageChange`: (page: number) => void - Page change handler
  - `className?`: string - Additional CSS classes
- **Features**:
  - Previous/next buttons
  - Page number links
  - Ellipsis for large page ranges
  - Jump to first/last page
  - Disabled states for boundaries
  - Compact and expanded variants

### 6. Overlay Components
Components that appear above other content.

#### Modal
- **Location**: `src/components/ui/Modal.tsx`
- **Purpose**: Dialog overlay for focused interactions
- **Props**:
  - `open`: boolean - Visibility state
  - `onClose`: () => void - Close handler
  - `title`: string - Modal title
  - `children`: ReactNode - Modal content
  - `size`: "sm" | "md" | "lg" | "full" - Size variant
  - `className?`: string - Additional CSS classes
- **Features**:
  - Focus trap for accessibility
  - Click outside to close (configurable)
  - ESC key to close
  - Animation on enter/exit
  - Scrolling content when needed
  - Header, body, footer sections

#### Dropdown Menu
- **Location**: `src/components/ui/DropdownMenu.tsx`
- **Purpose**: Contextual menu triggered by button/action
- **Props**:
  - `trigger`: ReactNode - Element that triggers the menu
  - `items`: Array<{ label: string, icon?: React.ComponentType, onClick: () => void, disabled?: boolean }>
  - `alignment`: "start" | "end" | "center" - Horizontal alignment
  - `position`: "top" | "bottom" - Vertical placement
  - `className?`: string - Additional CSS classes
- **Features**:
  - Keyboard navigation (arrow keys, enter, escape)
  - Click outside to close
  - Icons alongside menu items
  - Dividers between sections
  - Disabled item styling
  - Submenu support (nested menus)

#### Tooltip
- **Location**: `src/components/ui/Tooltip.tsx`
- **Purpose**: Informational tooltip on hover/focus
- **Props**:
  - `content`: string - Tooltip text
  - `side`: "top" | "bottom" | "left" | "right" - Placement
  - `align`: "start" | "center" | "end" - Alignment along side
  - `delay`: number - Show delay in ms (default: 0)
  - `skipDelay`: boolean - Skip delay on focus
  - `className?`: string - Additional CSS classes
- **Features**:
  - Smart repositioning to avoid overflow
  - Arrow pointing to trigger element
  - Fade in/out animation
  - Max width with text wrapping
  - Interactive content support (forms, buttons)

## Component Implementation Guidelines

### Styling Approach
- **Tailwind CSS**: Utility-first CSS framework for rapid UI development
- **CSS Variables**: Theme colors, spacing, and radii defined in CSS variables
- **Variants**: Variants defined through props rather than separate components
- **Dark Mode**: All components support dark mode through CSS variables

### Component API Design
- **Controlled Components**: Form components controlled via props (value/onChange)
- **Uncontrolled Options**: Support for uncontrolled mode via defaultValue prop
- **Event Handlers**: Consistent naming (onChange, onClick, onBlur, etc.)
- **Children Pattern**: Flexible content injection where appropriate
- **Composition**: Components designed to work together (e.g., FormField combining Label, Input, HelpText)

### Accessibility Standards
- **ARIA Attributes**: Proper roles, states, and properties
- **Keyboard Navigation**: Full keyboard operability
- **Focus Management**: Logical focus order and trapping where needed
- **Screen Reader Support**: Proper labels, descriptions, and live regions
- **Color Contrast**: Minimum 4.5:1 ratio for text, 3:1 for UI components

### Performance Considerations
- **Memoization**: React.memo for pure components
- **Lazy Loading**: Code splitting for non-critical components
- **Event Debouncing**: For expensive operations (search, resize)
- **Virtualization**: For large lists/tables (implemented in specific components)
- **CSS Optimization**: Purge unused Tailwind CSS in production

### Extension Points
- **Variants**: Component variants controlled via props (size, variant, color)
- **Slots**: Children prop for flexible content insertion
- **Callbacks**: Event handlers for customization
- **Class Names**: className prop for additional styling
- **Render Props**: For complex customization scenarios

## Component Library Structure
```
src/
├── components/
│   ├── layout/           # Layout components (Header, Sidebar)
│   ├── ui/               # Primitive UI components (Button, Input, etc.)
│   ├── layout/           # Page-level layouts
│   └── widgets/          # Complex domain-specific widgets
├── hooks/                # Custom React hooks
├── utils/                # Utility functions
├── styles/               # CSS and Tailwind configuration
└── pages/                # Page components
```

## Theming and Customization

### Design Tokens
Defined in `styles/globals.css` using CSS custom properties:

```css
:root {
  --color-background: #0f172a;
  --color-surface: #1e293b;
  --color-primary: #3b82f6;
  --color-secondary: #64748b;
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-error: #ef4444;
  --color-border: #334155;
  --color-text-primary: #f8fafc;
  --color-text-secondary: #94a3b8;
  --color-text-muted: #64748b;
  
  --radius-sm: 0.25rem;
  --radius-md: 0.5rem;
  --radius-lg: 0.75rem;
  --radius-full: 9999px;
  
  --space-px: 1px;
  --space-0: 0;
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.25rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  --space-10: 2.5rem;
  --space-12: 3rem;
  --space-16: 4rem;
  --space-20: 5rem;
  --space-24: 6rem;
  --space-32: 8rem;
}
```

### Component Variants
Each component supports variants through props:
- **Size**: sm, md, lg (and sometimes xl)
- **Variant**: default, outline, ghost, destructive (for buttons)
- **Color Scheme**: Inherited from context or explicitly set

## Usage Examples

### Basic Button Usage
```tsx
import { Button } from "@/components/ui/Button";

// Primary action button
<Button variant="default" size="md" onClick={() => handleSave()}>
  Save Changes
</Button>

// Secondary action button
<Button variant="outline" size="md" onClick={() => handleCancel()}>
  Cancel
</Button>

// Dangerous action button
<Button variant="destructive" size="md" onClick={() => handleDelete()}>
  Delete Item
</Button>
```

### Form with Validation
```tsx
import { Input, Button } from "@/components/ui";
import { useState } from "react";

function LoginForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Validation logic
    if (!email.includes("@")) {
      setError("Please enter a valid email");
      return;
    }
    // Submit logic
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="space-y-4">
        <Input
          label="Email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          error={error}
        />
        
        <Input
          label="Password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        
        <Button type="submit" variant="default" className="w-full">
          Sign In
        </Button>
      </div>
    </form>
  );
}
```

### Data Table with Actions
```tsx
import { Table, Button, Badge } from "@/components/ui";
import { Checkbox } from "@/components/ui/Checkbox";

function InvestigationsTable({ investigations }: { investigations: Investigation[] }) {
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  const handleSelectAll = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.checked) {
      setSelectedIds(investigations.map(i => i.id));
    } else {
      setSelectedIds([]);
    }
  };

  const handleRowSelect = (id: string, checked: boolean) => {
    setSelectedIds(prev => 
      checked ? [...prev, id] : prev.filter(itemId => itemId !== id)
    );
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">Investigations</h2>
        <Button variant="outline" size="sm" onClick={() => createInvestigation()}>
          New Investigation
        </Button>
      </div>
      
      <div className="overflow-x-auto">
        <Table>
          <Header>
            <HeaderRow>
              <HeaderCell className="w-12">
                <Checkbox
                  checked={selectedIds.length === investigations.length}
                  onChange={(e) => handleSelectAll(e)}
                />
              </HeaderCell>
              <HeaderCell>ID</HeaderCell>
              <HeaderCell>Title</HeaderCell>
              <HeaderCell>Status</HeaderCell>
              <HeaderCell>Updated</HeaderCell>
              <HeaderCell className="text-right">Actions</HeaderCell>
            </HeaderRow>
          </Header>
          <Body>
            {investigations.map(investigation => (
              <Row key={investigation.id} className="hover:bg-white/5">
                <Cell className="w-12">
                  <Checkbox
                    checked={selectedIds.includes(investigation.id)}
                    onChange={(e) => handleRowSelect(investigation.id, e.target.checked)}
                  />
                </Cell>
                <Cell className="font-mono">{investigation.id}</Cell>
                <Cell className="font-medium">{investigation.title}</Cell>
                <Cell>
                  <Badge variant={getStatusVariant(investigation.status)}>
                    {investigation.status}
                  </Badge>
                </Cell>
                <Cell className="text-sm">{formatDate(investigation.updatedAt)}</Cell>
                <Cell className="text-right space-x-2">
                  <Button variant="outline" size="xs" onClick={() => viewInvestigation(investigation.id)}>
                    <Eye size={14} /> View
                  </Button>
                  <Button variant="outline" size="xs" onClick={() => editInvestigation(investigation.id)}>
                    <Edit size={14} /> Edit
                  </Button>
                </Cell>
              </Cell>
            ))}
          </Body>
        </Table>
      </div>
    </div>
  );
}
```

## Component Development Process

### 1. Requirements Gathering
- Identify UI pattern needed
- Review existing similar components
- Define props and behaviors
- Consider accessibility requirements

### 2. Implementation
- Create component file in appropriate directory
- Implement with TypeScript interfaces for props
- Apply styling using Tailwind CSS
- Add proper accessibility attributes
- Include JSDoc comments for complex props

### 3. Documentation
- Add component to this specification document
- Include usage examples
- Note any accessibility considerations
- Specify any known limitations

### 4. Testing
- Visual testing for different states
- Accessibility testing (axe, manual keyboard navigation)
- Responsive design testing
- Performance profiling for complex components

### 5. Review
- Code review for consistency with patterns
- Accessibility review
- Design review against specifications
- Performance considerations

## Maintenance Guidelines

### Naming Conventions
- Use PascalCase for component names (Button, Input, Table)
- Use camelCase for props (onChange, isDisabled)
- Use kebab-case for CSS classes and variants
- Prefix private functions with underscore (_)

### File Organization
- One component per file
- Export component as default export
- Place related sub-components in same file (Header, Title, Content within Card)
- Group related components in subdirectories when appropriate

### Versioning
- Follow semantic versioning for breaking changes
- Document breaking changes in CHANGELOG.md
- Provide migration guides for major version updates
- Maintain backward compatibility where possible

## Future Enhancements

### Planned Components
- **DataGrid**: Advanced table with filtering, sorting, column pinning
- **FormBuilder**: Dynamic form generation from schema
- **Timeline**: Vertical timeline for process visualization
- **TreeView**: Hierarchical data display with expand/collapse
- **Wizzard**: Multi-step form guide
- **DataPicker**: Date and time selection components
- **Slider**: Input range component
- **Rating**: Star rating component
- **Carousel**: Image/content carousel
- **SkeletonLoader**: Loading placeholders

### Accessibility Improvements
- Enhanced screen reader support
- Improved keyboard navigation patterns
- Better focus visible indicators
- Extended ARIA live region usage

### Performance Optimizations
- Virtual scrolling for large lists
- Image lazy loading
- CSS containment for complex components
- Web workers for expensive computations

## Dependencies
- React 18+
- Tailwind CSS 3+
- Headless UI (for accessibility primitives)
- Lucide React (for icons)
- Class variance authority (for variant styling)

## Related Documentation
- [FFIRE_Button_Specifications.md](FFIRE_Button_Specifications.md)
- [FFIRE_Table_Specifications.md](FFIRE_Table_Specifications.md)
- [FFIRE_Popup_Specifications.md](FFIRE_Popup_Specfications.md)
- [FFIRE_Screen_Specifications.md](FFIRE_Screen_Specifications.md)
- [FFIRE_UX_Flows.md](FFIRE_UX_Flows.md)
- [FFIRE_Information_Architecture.md](FFIRE_Information_Architecture.md)
- [FFIRE_Backend_Prompts.md](FFIRE_Backend_Prompts.md)