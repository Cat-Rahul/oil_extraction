import { Bell, Search, User, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface AppHeaderProps {
  title: string;
  breadcrumbs?: { label: string; href?: string }[];
}

export function AppHeader({ title, breadcrumbs }: AppHeaderProps) {
  return (
    <header className="flex items-center justify-between h-16 px-6 border-b border-border bg-card">
      {/* Left Section - Title & Breadcrumbs */}
      <div className="flex flex-col">
        <h1 className="text-lg font-semibold text-foreground">&nbsp;</h1>
      </div>

      {/* Right Section - Actions */}
      <div className="flex items-center gap-4">
        {/* Project Selector */}
        {/* <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" className="gap-2 h-9">
              <span className="text-sm font-medium">FPSO Prosperity</span>
              <ChevronDown className="w-4 h-4 text-muted-foreground" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel>Select Project</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem>FPSO Prosperity</DropdownMenuItem>
            <DropdownMenuItem>FPSO Harmony</DropdownMenuItem>
            <DropdownMenuItem>FPSO Pioneer</DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="text-muted-foreground">View all projects...</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu> */}

        {/* Search */}
        <Button variant="ghost" size="icon" className="h-9 w-9">
          <Search className="w-4 h-4" />
        </Button>

        {/* Notifications */}
        <Button variant="ghost" size="icon" className="h-9 w-9 relative">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-accent rounded-full" />
        </Button>

        {/* User Menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="gap-2 h-9 pl-2 pr-3">
              <div className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center">
                <User className="w-4 h-4 text-primary" />
              </div>
              <span className="text-sm font-medium">J. Morrison</span>
              <ChevronDown className="w-3 h-3 text-muted-foreground" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            <DropdownMenuLabel>Lead Process Engineer</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem>Profile</DropdownMenuItem>
            <DropdownMenuItem>Preferences</DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem>Sign out</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
