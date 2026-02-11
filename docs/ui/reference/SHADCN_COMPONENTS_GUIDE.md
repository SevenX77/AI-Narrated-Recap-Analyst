# shadcn/ui 组件完整指南

> 基于 https://ui.shadcn.com 的完整组件研究和设计模式分析

## 📚 目录

1. [整体架构](#整体架构)
2. [组件分类](#组件分类)
3. [布局模式](#布局模式)
4. [设计原则](#设计原则)
5. [实践建议](#实践建议)

---

## 🏗️ 整体架构

### 核心理念

shadcn/ui 不是传统的组件库，而是一个 **复制粘贴组件集合**：
- ✅ 完全控制组件代码
- ✅ 基于 Radix UI + Tailwind CSS
- ✅ 可自定义、可扩展
- ✅ TypeScript 支持
- ❌ 不是 npm 包（除了 CLI）

### 技术栈

```
shadcn/ui
  ├── Radix UI (无头组件基础)
  ├── Tailwind CSS (样式)
  ├── class-variance-authority (变体管理)
  ├── clsx + tailwind-merge (类名合并)
  └── lucide-react (图标)
```

---

## 🎨 组件分类

### 1. 基础组件 (Basic Components)

#### **Button** 按钮
- **变体**: default, outline, ghost, destructive, secondary, link
- **尺寸**: xs, sm, default, lg, icon
- **关键特性**: 
  - 支持 `asChild` 属性（组合其他组件）
  - Icon 支持（inline-start/inline-end）
  - Loading 状态（Spinner）
  - 圆角变体（rounded-full）

```tsx
<Button variant="outline" size="sm">
  <Icon className="mr-2" />
  Button Text
</Button>
```

#### **Input** 输入框
- 支持前缀/后缀图标
- 错误状态处理
- Input Group 组合

#### **Badge** 徽章
- 变体: default, secondary, destructive, outline
- 用于状态标签、计数等

#### **Card** 卡片
```tsx
<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
    <CardDescription>Description</CardDescription>
  </CardHeader>
  <CardContent>Content</CardContent>
  <CardFooter>Footer</CardFooter>
</Card>
```

### 2. 表单组件 (Form Components)

#### **Form** 表单系统
- 基于 React Hook Form
- 集成 Zod 验证
- Field、Label、Message 子组件

#### **Select / Combobox**
- Select: 简单下拉选择
- Combobox: 带搜索的下拉框

#### **Checkbox / Radio / Switch**
- 全部基于 Radix UI
- 支持表单集成

#### **Textarea**
- 自适应高度选项
- 最大/最小高度控制

### 3. 导航组件 (Navigation Components)

#### **Sidebar** ⭐ 核心布局组件
```tsx
<SidebarProvider>
  <AppSidebar />
  <SidebarInset>
    <header>...</header>
    <main>...</main>
  </SidebarInset>
</SidebarProvider>
```

**关键属性**:
```typescript
interface SidebarProps {
  side: 'left' | 'right'
  variant: 'sidebar' | 'floating' | 'inset'
  collapsible: 'offcanvas' | 'icon' | 'none'
  defaultOpen?: boolean
  open?: boolean // 受控模式
  onOpenChange?: (open: boolean) => void
}
```

**折叠模式**:
- `offcanvas`: 移动端覆盖模式
- `icon`: 折叠为图标栏
- `none`: 不可折叠

**最佳实践**:
```tsx
// 侧边栏组件结构
<Sidebar>
  <SidebarHeader>Logo/Title</SidebarHeader>
  <SidebarContent>
    <SidebarGroup>
      <SidebarGroupLabel>Section</SidebarGroupLabel>
      <SidebarGroupContent>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton>Item</SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  </SidebarContent>
  <SidebarFooter>User Info</SidebarFooter>
</Sidebar>
```

#### **Navigation Menu**
- 顶部导航栏
- 支持下拉菜单
- 响应式设计

#### **Breadcrumb** 面包屑
```tsx
<Breadcrumb>
  <BreadcrumbList>
    <BreadcrumbItem>
      <BreadcrumbLink href="/">Home</BreadcrumbLink>
    </BreadcrumbItem>
    <BreadcrumbSeparator />
    <BreadcrumbItem>
      <BreadcrumbPage>Current</BreadcrumbPage>
    </BreadcrumbItem>
  </BreadcrumbList>
</Breadcrumb>
```

#### **Tabs** 标签页
- 水平/垂直布局
- 受控/非受控模式

### 4. 反馈组件 (Feedback Components)

#### **Toast / Sonner**
- **Toast**: Radix UI 原生
- **Sonner**: 更现代的 toast 库（推荐）
```tsx
import { toast } from 'sonner'
toast.success('Success message')
```

#### **Dialog / AlertDialog**
- Dialog: 通用对话框
- AlertDialog: 确认/警告对话框

#### **Tooltip**
- 延迟显示
- 多方向支持
- 动画效果

#### **Skeleton** 骨架屏
```tsx
<Skeleton className="h-4 w-full" />
<SkeletonCard />
```

### 5. 数据展示组件 (Data Display)

#### **Table / DataTable**
- 基础表格
- DataTable: 带排序、过滤、分页

#### **Command** 命令面板
```tsx
<Command>
  <CommandInput placeholder="Search..." />
  <CommandList>
    <CommandGroup heading="Suggestions">
      <CommandItem>Item 1</CommandItem>
    </CommandGroup>
  </CommandList>
</Command>
```

#### **Chart** 图表系统 ⭐
基于 Recharts，包括：
- **Area Chart**: 面积图（6种变体）
- **Bar Chart**: 柱状图（7种变体）
- **Line Chart**: 折线图（5种变体）
- **Pie Chart**: 饼图（4种变体）
- **Radar Chart**: 雷达图
- **Radial Chart**: 径向图

**图表特性**:
- 响应式设计
- 交互式工具提示
- 图例支持
- 渐变/图标支持
- 自定义轴

```tsx
<ChartContainer config={chartConfig}>
  <AreaChart data={data}>
    <CartesianGrid strokeDasharray="3 3" />
    <XAxis dataKey="name" />
    <YAxis />
    <ChartTooltip content={<ChartTooltipContent />} />
    <Area 
      type="monotone" 
      dataKey="value" 
      fill="hsl(var(--primary))" 
    />
  </AreaChart>
</ChartContainer>
```

### 6. 其他实用组件

#### **Separator** 分隔线
- 水平/垂直
- 不同粗细

#### **ScrollArea** 滚动区域
- 自定义滚动条样式
- 虚拟滚动支持

#### **Collapsible** 折叠面板
- 动画展开/折叠
- 受控/非受控

#### **Accordion** 手风琴
- 单选/多选模式
- 平滑动画

---

## 🎯 布局模式

### 1. Dashboard 布局

**标准 Dashboard 结构**:
```tsx
<div className="flex h-screen">
  {/* Sidebar */}
  <Sidebar />
  
  {/* Main Content */}
  <div className="flex-1 flex flex-col">
    {/* Header */}
    <Header />
    
    {/* Content Area */}
    <main className="flex-1 overflow-auto p-6">
      {/* Breadcrumb */}
      <Breadcrumb />
      
      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>...</Card>
      </div>
      
      {/* Charts */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <ChartContainer>...</ChartContainer>
        </Card>
      </div>
      
      {/* Data Table */}
      <Card>
        <DataTable />
      </Card>
    </main>
  </div>
</div>
```

**关键尺寸**:
```css
--sidebar-width: calc(var(--spacing) * 72)  /* 288px */
--header-height: calc(var(--spacing) * 12)   /* 48px */
```

### 2. Sidebar 布局变体

#### **Variant 1: sidebar** (默认)
- 固定宽度侧边栏
- 桌面端始终可见
- 移动端可折叠

#### **Variant 2: floating**
- 浮动侧边栏（带阴影）
- 不占据布局空间

#### **Variant 3: inset**
- 内嵌式侧边栏
- 与主内容有间距

#### **折叠到图标模式**:
```tsx
<SidebarProvider defaultOpen={false}>
  <AppSidebar collapsible="icon" />
  ...
</SidebarProvider>
```

### 3. Blocks 示例

shadcn/ui 提供了 **预制 Blocks**（完整页面模板）：

#### **Dashboard Blocks**
- `dashboard-01`: 带侧边栏、图表、数据表格
- `dashboard-02`: 多卡片统计面板
- `dashboard-03`: 销售仪表板

#### **Sidebar Blocks**
- `sidebar-03`: 带子菜单的侧边栏
- `sidebar-07`: 可折叠到图标的侧边栏

#### **Login/Signup Blocks**
- `login-03`: 带背景色的登录页
- `login-04`: 登录页+图片布局

**使用方式**:
```bash
npx shadcn add dashboard-01
```

---

## 🎨 设计原则

### 1. 颜色系统

shadcn/ui 使用 **CSS 变量** 定义颜色：

```css
:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  --primary: 222.2 47.4% 11.2%;
  --primary-foreground: 210 40% 98%;
  --secondary: 210 40% 96.1%;
  --muted: 210 40% 96.1%;
  --muted-foreground: 215.4 16.3% 46.9%;
  --accent: 210 40% 96.1%;
  --border: 214.3 31.8% 91.4%;
  --ring: 222.2 84% 4.9%;
  /* ... */
}
```

**语义化颜色**:
- `background`: 页面背景
- `foreground`: 主文本颜色
- `primary`: 主色调（CTA按钮等）
- `secondary`: 次要色
- `muted`: 柔和背景（卡片、输入框等）
- `accent`: 强调色（hover 状态等）
- `destructive`: 危险操作颜色

### 2. 间距系统

使用 Tailwind 默认间距：
- **小间距**: `gap-2` (8px), `gap-3` (12px)
- **中间距**: `gap-4` (16px), `gap-6` (24px)
- **大间距**: `gap-8` (32px), `gap-12` (48px)

**容器 padding**:
- 移动端: `p-4` 或 `px-4`
- 桌面端: `p-6` 或 `px-6`

### 3. 字体层次

```css
/* 标题层次 */
h1: 30px, font-weight: 600, letter-spacing: -0.75px
h2: 24px, font-weight: 600, letter-spacing: -0.5px
h3: 20px, font-weight: 600
h4: 16px, font-weight: 600

/* 正文 */
body: 16px, font-weight: 400
small: 14px
xs: 12px
```

### 4. 圆角设计

```css
--radius: 0.5rem; /* 默认 8px */

/* 使用 */
rounded-lg: border-radius: var(--radius)
rounded-md: border-radius: calc(var(--radius) - 2px)
rounded-sm: border-radius: calc(var(--radius) - 4px)
```

### 5. 动画时机

```css
/* 快速交互 */
transition-colors duration-150

/* 标准动画 */
transition-all duration-200

/* 较慢动画 */
transition-all duration-300
```

---

## 💡 实践建议

### 1. 组件使用最佳实践

#### ✅ 推荐做法

```tsx
// 1. 使用语义化变体
<Button variant="destructive">Delete</Button>

// 2. 合理使用 asChild
<Button asChild>
  <Link to="/profile">Profile</Link>
</Button>

// 3. 图标正确使用
<Button>
  <Icon data-icon="inline-start" />
  Text
</Button>

// 4. 表单正确结构
<Form {...form}>
  <FormField
    control={form.control}
    name="email"
    render={({ field }) => (
      <FormItem>
        <FormLabel>Email</FormLabel>
        <FormControl>
          <Input {...field} />
        </FormControl>
        <FormMessage />
      </FormItem>
    )}
  />
</Form>
```

#### ❌ 避免做法

```tsx
// 1. 不要硬编码颜色
<div className="bg-blue-500"> ❌
<div className="bg-primary"> ✅

// 2. 不要混用 Button 和 Link 的样式
<a className="inline-flex items-center..."> ❌
<Button asChild><Link /></Button> ✅

// 3. 不要忽略表单验证
<Input onChange={...} /> ❌
<Form><FormField /></Form> ✅
```

### 2. 响应式设计

```tsx
// 移动优先设计
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {items.map(item => <Card key={item.id} />)}
</div>

// 侧边栏响应式
<SidebarProvider>
  <Sidebar collapsible="offcanvas" /> {/* 移动端覆盖 */}
  ...
</SidebarProvider>
```

### 3. 性能优化

```tsx
// 1. 虚拟滚动长列表
<ScrollArea>
  <VirtualList items={...} />
</ScrollArea>

// 2. 延迟加载重型组件
const Chart = lazy(() => import('./components/Chart'))

// 3. 表格分页
<DataTable
  data={data}
  pageSize={10}
  pagination
/>
```

### 4. 主题定制

```tsx
// 1. 修改 CSS 变量
:root {
  --primary: 210 100% 50%; /* 自定义主色 */
}

// 2. 修改圆角
:root {
  --radius: 0.75rem; /* 更大的圆角 */
}

// 3. Dark Mode
.dark {
  --background: 222.2 84% 4.9%;
  --foreground: 210 40% 98%;
}
```

### 5. 可访问性 (A11y)

shadcn/ui 基于 Radix UI，天然支持：
- ✅ 键盘导航
- ✅ 屏幕阅读器支持
- ✅ ARIA 属性
- ✅ Focus 管理

**额外注意**:
```tsx
// 1. 为图标添加 aria-label
<Button variant="ghost" size="icon" aria-label="Close">
  <X />
</Button>

// 2. 为表单字段添加描述
<FormField>
  <FormDescription>
    This is a hint for the field
  </FormDescription>
</FormField>
```

---

## 📦 推荐组合

### Dashboard 推荐组合

```tsx
// 核心布局
- SidebarProvider + Sidebar + SidebarInset
- Breadcrumb

// 数据展示
- Card (统计卡片)
- ChartContainer + Area/Bar/Line Chart
- DataTable

// 交互组件
- Command (全局搜索)
- Toast/Sonner (通知)
- Dialog (操作确认)
```

### Admin Panel 推荐组合

```tsx
- Sidebar (可折叠)
- DataTable (CRUD 操作)
- Form (创建/编辑)
- AlertDialog (删除确认)
- Badge (状态标签)
- Pagination
```

### Settings Page 推荐组合

```tsx
- Tabs (设置分类)
- Form (表单配置)
- Switch (开关选项)
- Select (下拉选择)
- Separator (分组分隔)
- Toast (保存反馈)
```

---

## 🔗 参考资源

- [shadcn/ui 官网](https://ui.shadcn.com/)
- [Radix UI 文档](https://www.radix-ui.com/)
- [Tailwind CSS 文档](https://tailwindcss.com/)
- [CVA 文档](https://cva.style/docs)
- [Recharts 文档](https://recharts.org/)

---

## 📸 截图参考

项目中已保存的 shadcn/ui 参考截图：
- `docs/ui/reference/shadcn-components-page.png` - 组件列表页
- `docs/ui/reference/shadcn-button-page.png` - Button 组件详情
- `docs/ui/reference/shadcn-sidebar-docs.png` - Sidebar 组件完整文档
- `docs/ui/reference/shadcn-blocks-page.png` - Blocks 页面布局
- `docs/ui/reference/shadcn-charts-page.png` - Charts 页面示例

---

**最后更新**: 2026-02-10
**版本**: shadcn/ui v4.x (Radix UI)
