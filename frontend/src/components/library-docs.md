# FFRE Component Library Documentation

## Overview

This document provides comprehensive documentation for the FFRE (Financial Fraud Investigation Reasoning Engine) component library. The library provides a collection of reusable UI components that follow a consistent design system aligned with the FFRE design specifications.

## Getting Started

### Installation

The component library is included as part of the FFRE frontend application. No additional installation is required.

### Usage

Components can be imported directly from the `@/components/ui` alias:

```typescript
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card } from "@/components/ui/Card";
```

## Component Categories

### Form Components
Components for user input and data collection:

- **Input** - Text input fields with labels, validation states, and helper text
- **Select** - Dropdown selection components
- **Checkbox** - Toggle switches and selection boxes
- **Button** - Primary action buttons with multiple variants
- **ButtonGroup** - Groups of related actions

### Data Components
Components for displaying and interacting with data:

- **Card** - Containers for grouping related information
- **Table** - Data grids for displaying tabular information
- **Badge** - Status indicators and labels
- **Avatar** - User profile images and initials

### Feedback Components
Components for providing user feedback:

- **Alert** - Inline notification messages
- **Toast** - Temporary popup notifications
- **Progress** - Visual progress indicators
- **SkeletonLoader** - Loading placeholders (planned)

### Navigation Components
Components for application navigation:

- **Breadcrumb** - Hierarchical navigation trails
- **Tabs** - Content organization into tabbed panels
- **Pagination** - Page navigation for large datasets
- **Sidebar** - Vertical navigation menu

### Overlay Components
Components that appear above the main content:

- **Modal** - Dialog boxes for focused interactions
- **Dropdown** - Menu lists triggered by buttons
- **Tooltip** - Informational text on hover/focus
- **Popover** - Rich content overlays

### Layout Components
Components for page structure:

- **Header** - Application header with branding and navigation
- **Footer** - Application footer with links and information
- **Sidebar** - Vertical navigation panel
- **Container** - Content width constraints and centering

## Component API Reference

### Button

A customizable button component with multiple variants and sizes.

#### Props
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| variant | `"default" \| "outline" \| "ghost" \| "destructive"` | `"default"` | Visual style of the button |
| size | `"sm" \| "md" \| "lg"` | `"md"` | Size of the button |
| onClick | `(e: React.MouseEvent) => void` | `undefined` | Click handler |
| children | `ReactNode` | `required` | Button content |
| disabled | `boolean` | `false` | Disabled state |
| className | `string` | `""` | Additional CSS classes |
| asChild | `boolean` | `false` | Render as child element (for links) |

#### Variants
- **Default**: Primary action (solid background)
- **Outline**: Secondary action (border only)
- **Ghost**: Tertiary action (no background/border)
- **Destructive**: Destructive action (red background)

#### Usage Examples
```tsx
// Primary button
<Button variant="default" size="md" onClick={handleClick}>
  Submit
</Button>

// Outline button
<Button variant="outline" size="md" onClick={handleClick}>
  Cancel
</Button>

// Icon button
<Button variant="ghost" size="md" onClick={handleClick}>
  <Search size={16} /> Search
</Button>

// Button with loading state
<Button variant="default" size="md" onClick={handleClick} disabled={isLoading}>
  {isLoading ? (
    <>
      <RefreshCw size={16} className="mr-2 animate-spin" />
      Saving...
    </>
  ) : (
    <Save size={16} className="mr-2" />
    Save
  )}
</Button>
```

### Input

A text input field with label, validation, and helper text support.

#### Props
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| type | `string` | `"text"` | Input type (text, email, password, tel, etc.) |
| value | `string` | `""` | Current value |
| onChange | `(e: React.ChangeEvent) => void` | `required` | Change handler |
| placeholder | `string` | `""` | Placeholder text |
| label | `string` | `""` | Label text |
| helperText | `string` | `""` | Helper text below input |
| error | `string` | `""` | Error message (shows error state) |
| disabled | `boolean` | `false` | Disabled state |
| required | `boolean` | `false` | Required field indicator |
| className | `string` | `""` | Additional CSS classes |

#### Usage Examples
```tsx
// Basic input
<Input
  type="text"
  value={name}
  onChange={(e) => setName(e.target.value)}
  placeholder="Enter your name"
  label="Full Name"
/>

// Input with error
<Input
  type="email"
  value={email}
  onChange={(e) => setEmail(e.target.value)}
  placeholder="Enter your email"
  label="Email Address"
  error="Please enter a valid email address"
 />

// Password input with toggle
<div className="relative">
  <Input
    type={showPassword ? "text" : "password"}
    value={password}
    onChange={(e) => setPassword(e.target.value)}
    placeholder="Enter password"
    className="pr-10"
  />
  <Button
    variant="ghost"
    size="sm"
    onClick={() => setShowPassword(!showPassword)}
    className="absolute right-2 top-1/2 -translate-y-1/2 p-1"
    aria-label="Toggle password visibility"
  >
    {showPassword ? (
      <EyeOff size={16} />
    ) : (
      <Eye size={16} />
    )}
  </Button>
</div>
```

### Card

A container component for grouping related content with optional header and sections.

#### Props
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| className | `string` | `""` | Additional CSS classes |
| children | `ReactNode` | `required` | Card content |

#### Sub-components
- `CardHeader` - Header section
- `CardTitle` - Title within header
- `CardContent` - Main content area

#### Usage Examples
```tsx
// Basic card
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

// Card with actions
<Card className="border-l-4 border-primary">
  <CardHeader className="flex items-start justify-between pb-2">
    <div>
      <CardTitle className="text-sm font-medium text-text-secondary">
        Recent Activity
      </CardTitle>
      <p className="text-xs text-text-tertiary">
        Last updated 5 minutes ago
      </p>
    </div>
    <Button variant="outline" size="sm" onClick={handleViewAll}>
      <Eye size={14} /> View All
    </Button>
  </CardHeader>
  <CardContent className="p-4">
    {/* Content */}
  </CardContent>
</Card>
```

### Table

A data table component for displaying tabular information with features like sorting, selection, and row actions.

#### Props
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| className | `string` | `""` | Additional CSS classes |
| children | `ReactNode` | `required` | Table content (Header, Body) |

#### Sub-components
- `Header` - Table header section
- `HeaderRow` - Table header row
- `HeaderCell` - Table header cell
- `Body` - Table body section
- `Row` - Table row
- `Cell` - Table cell

#### Usage Examples
```tsx
<Table>
  <Header>
    <HeaderRow>
      <HeaderCell className="w-12">
        <Checkbox
          checked={selectedIds.length === data.length}
          onChange={(e) => handleSelectAll(e.target.checked)}
        />
      </HeaderCell>
      <HeaderCell>ID</HeaderCell>
      <HeaderCell>Title</HeaderCell>
      <HeaderCell>Status</HeaderCell>
      <HeaderCell className="text-right">Actions</HeaderCell>
    </HeaderRow>
  </Header>
  <Body>
    {data.map(item => (
      <Row key={item.id} className="hover:bg-white/5">
        <Cell className="w-12">
          <Checkbox
            checked={selectedIds.includes(item.id)}
            onChange={() => handleRowSelect(item.id)}
          />
        </Cell>
        <Cell className="font-mono">{item.id}</Cell>
        <Cell className="font-medium">{item.title}</Cell>
        <Cell>
          <Badge variant={getStatusVariant(item.status)}>
            {item.status}
          </Badge>
        </Cell>
        <Cell>{formatDate(item.date)}</Cell>
        <Cell className="text-right space-x-2">
          <Button variant="outline" size="xs" onClick={() => viewItem(item.id)}>
            <Eye size={12} /> View
          </Button>
          <Button variant="outline" size="xs" onClick={() => editItem(item.id)}>
            <Edit size={12} /> Edit
          </Button>
        </Cell>
      </Cell>
    ))}
  </Body>
</Table>
```

## Design Tokens

### Colors
The component library uses the following color palette:

| Purpose | Variable | Value | Usage |
|---------|----------|-------|-------|
| Primary | `--color-primary` | `#3B82F6` | Primary actions, links |
| Secondary | `--color-secondary` | `#10B981` | Success states |
| Warning | `--color-warning` | `#F59E0B` | Warnings, cautions |
| Destructive | `--color-destructive` | `#EF4444` | Errors, destructive actions |
| Background | `--color-bg-surface` | `#0F172A` | Main background |
| Background Dark | `--color-bg-dark` | `#020617` | Darker background variants |
| Text Primary | `--color-text-primary` | `#F8FAFC` | Primary text |
| Text Secondary | `--color-text-secondary` | `#94A3B8` | Secondary text |
| Border | `--color-border-glass` | `rgba(255, 255, 255, 0.1)` | Borders and dividers |

### Typography
| Purpose | Size | Weight | Line Height | Usage |
|---------|------|---------|-------------|-------|
| Display | `2.5rem` (40px) | 700 | 1.2 | Page titles |
| Heading | `1.5rem` (24px) | 600 | 1.3 | Section titles |
| Body | `1rem` (16px) | 400 | 1.5 | Body text |
| Caption | `0.875rem` (14px) | 400 | 1.4 | Helper text, labels |
| Overline | `0.75rem` (12px) | 500 | 1.3 | Labels, timestamps |

### Spacing
Uses a 4px-based spacing system:
- `0` = 0px
- `1` = 4px
- `2` = 8px
- `3` = 12px
- `4` = 16px
- `5` = 20px
- `6` = 24px
- `8` = 32px
- `10` = 40px
- `12` = 48px
- `16` = 64px
- `20` = 80px
- `24` = 96px

### Border Radius
- `none` = 0px
- `sm` = 2px
- `default` = 4px
- `md` = 6px
- `lg` = 8px
- `xl` = 12px
- `full` = 9999px

### Shadows
- `sm` = 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)
- `default` = 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.06)
- `md` = 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)
- `lg` = 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)
- `xl` = 0 25px 50px -12px rgba(0, 0, 0, 0.25)
- `2xl` = 0 25px 50px -12px rgba(0, 0, 0, 0.25)

## Accessibility Guidelines

All components in the library follow WCAG 2.1 AA accessibility guidelines:

### Keyboard Navigation
- All interactive elements are keyboard accessible
- Logical tab order is maintained
- Focus indicators are clearly visible
- Modal traps focus when open
- Dropdowns can be opened/closed with keyboard

### Screen Reader Support
- All interactive elements have appropriate ARIA labels
- Form elements have associated labels
- Live regions are used for dynamic content
- Landmark regions are used where appropriate
- Icon-only buttons have aria-label attributes

### Color Contrast
- All text meets minimum 4.5:1 contrast ratio
- Large text (18pt+) meets 3:1 contrast ratio
- UI components meet 3:1 contrast for non-text elements
- Focus indicators meet 3:1 contrast against adjacent colors

### Touch Targets
- Minimum touch target size is 44x44px
- Adequate spacing between interactive elements
- Consider mobile thumb zones for placement

## Best Practices

### Component Usage
1. **Prefer composition over props** - Combine simple components rather than adding numerous props
2. **Keep components focused** - Each component should have a single responsibility
3. **Use semantic HTML** - Leverage native HTML elements where appropriate
4. **Handle edge cases** - Consider empty, loading, and error states
5. **Optimize performance** - Use React.memo for expensive components when appropriate

### Styling
1. **Use utility-first approach** - Leverage Tailwind CSS utilities
2. **Maintain consistency** - Use existing component variants rather than creating new styles
3. **Responsive design** - Test at multiple breakpoints
4. **Dark mode support** - Ensure components work in both light and dark themes
5. **Avoid !important** - Use specificity rather than overrides

### Accessibility
1. **Test with keyboard** - Navigate without mouse
2. **Use screen readers** - Verify announcements are correct
3. **Check color contrast** - Use tools to verify ratios
4. **Provide alternative text** - For icons and images
5. **Manage focus** - Especially in modals and dialogs

### Performance
1. **Memoize expensive calculations** - Use useMemo and useCallback
2. **Lazy load non-critical components** - Use React.lazy and Suspense
3. **Virtualize long lists** - Consider windowing for large datasets
4. **Optimize images** - Use appropriate formats and sizes
5. **Minimize re-renders** - Split state logically

## Contributing

### Adding New Components
1. Check if similar functionality exists
2. Follow the existing component structure
3. Add proper TypeScript typings
4. Include JSDoc comments for complex props
5. Ensure accessibility compliance
6. Add to this documentation
7. Write unit tests if applicable
8. Update the library specification document

### Modifying Existing Components
1. Ensure backward compatibility
2. Update documentation if API changes
3. Test with existing usage patterns
4. Consider impact on dependent components
5. Follow semantic versioning guidelines

### Reporting Issues
1. Check if issue already exists
2. Provide clear reproduction steps
3. Include screenshots if applicable
4. Specify browser and device information
5. Suggest potential solutions if possible

## Changelog

### v1.0.0 (Initial Release)
- Initial release of component library
- Includes all UI components specified in design documents
- Full TypeScript support
- Accessibility compliance (WCAG 2.1 AA)
- Responsive design for all breakpoints
- Dark mode support

### v1.1.0 (Planned)
- Additional form components (Radio, Switch, Slider)
- Enhanced table features (column pinning, row selection)
- Advanced card variations (with actions, footers)
- Improved tooltip and popover implementations
- Skeleton loader components for loading states

### v1.2.0 (Planned)
- Data visualization components (charts, graphs)
- Timeline and process flow components
- Enhanced modal and dialog system
- Drag and drop interfaces
- Customizable themes and styling options

## Related Documentation

- [FFIRE_Button_Specifications.md](FFIRE_Button_Specifications.md) - Button design specifications
- [FFIRE_Table_Specifications.md](FFIRE_Table_Specifications.md) - Table design specifications
- [FFIRE_Popup_Specifications.md](FFIRE_Popup_Specfications.md) - Popup and modal specifications
- [FFIRE_Screen_Specifications.md](FFIRE_Screen_Specifications.md) - Screen layout specifications
- [FFIRE_UX_Flows.md](FFIRE_UX_Flows.md) - User experience flows
- [FFIRE_Information_Architecture.md](FFIRE_Information_Architecture.md) - Information architecture
- [FFIRE_Backend_Prompts.md](FFIRE_Backend_Prompts.md) - Backend integration prompts
- [FFIRE_Button_Prompts.md](FFIRE_Button_Prompts.md) - Button action prompts