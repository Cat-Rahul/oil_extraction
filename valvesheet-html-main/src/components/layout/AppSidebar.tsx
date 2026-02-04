import { useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  FileSpreadsheet,
  Eye,
  BookOpen,
  ShieldCheck,
  GitBranch,
  Settings,
  ChevronLeft,
  ChevronRight,
  Anchor,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  {
    title: "Dashboard",
    href: "/",
    icon: LayoutDashboard,
  },
  {
    title: "Datasheet Generator",
    href: "/generator",
    icon: FileSpreadsheet,
  },
  // {
  //   title: "Datasheet Automation",
  //   href: "/automation",
  //   icon: FileSpreadsheet,
  // },
  {
    title: "Preview & Editor",
    href: "/preview",
    icon: Eye,
  },
  {
    title: "Standards & Traceability",
    href: "/standards",
    icon: BookOpen,
  },
  {
    title: "Validation",
    href: "/validation",
    icon: ShieldCheck,
  },
  {
    title: "Approval & Versions",
    href: "/approval",
    icon: GitBranch,
  },
];

export function AppSidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();

  return (
    <aside
      className={cn(
        "flex flex-col bg-sidebar text-sidebar-foreground transition-all duration-300",
        collapsed ? "w-16" : "w-64",
      )}
    >
      {/* Logo Section */}
      <div className="flex items-center h-16 px-4 border-b border-sidebar-border bg-white">
        <div className="flex items-center gap-3">
          {!collapsed && (
            <div className="flex flex-col">
              <img src="https://www.shapoorjipallonjienergy.com/img/logo.png" width="" height="" />
              {/* <span className="text-sm font-semibold text-sidebar-foreground">FPSO AutoGen</span>
              <span className="text-[10px] text-sidebar-foreground/60 uppercase tracking-wider">
                Engineering Platform
              </span> */}
            </div>
          )}
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 overflow-y-auto">
        <ul className="space-y-1 px-2">
          {navItems.map((item) => {
            const isActive = location.pathname === item.href;
            return (
              <li key={item.href}>
                <NavLink
                  to={item.href}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-all",
                    isActive
                      ? "bg-sidebar-accent text-sidebar-primary"
                      : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-foreground",
                  )}
                >
                  <item.icon className={cn("w-5 h-5 flex-shrink-0", isActive && "text-sidebar-primary")} />
                  {!collapsed && <span>{item.title}</span>}
                </NavLink>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Settings & Collapse */}
      <div className="border-t border-sidebar-border p-2">
        <NavLink
          to="/settings"
          className={cn(
            "flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-all",
            location.pathname === "/settings"
              ? "bg-sidebar-accent text-sidebar-primary"
              : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-foreground",
          )}
        >
          <Settings className="w-5 h-5 flex-shrink-0" />
          {!collapsed && <span>Settings</span>}
        </NavLink>

        <button
          onClick={() => setCollapsed(!collapsed)}
          className="flex items-center justify-center w-full mt-2 py-2 rounded-md text-sidebar-foreground/60 hover:bg-sidebar-accent hover:text-sidebar-foreground transition-all"
        >
          {collapsed ? (
            <ChevronRight className="w-5 h-5" />
          ) : (
            <>
              <ChevronLeft className="w-5 h-5" />
              <span className="ml-2 text-xs">Collapse</span>
            </>
          )}
        </button>
      </div>
    </aside>
  );
}
