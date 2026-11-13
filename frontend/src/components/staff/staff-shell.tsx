"use client";

import { Inbox, LogOut, Moon, PanelLeftClose, PanelLeftOpen, ScrollText, Search, Sun, UserRound } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTheme } from "next-themes";
import { createContext, useContext, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import type { StaffProfile } from "@/lib/api";
import { useApprovalQueue } from "@/lib/staff-queries";
import { cn } from "@/lib/utils";

/** The top bar's search text, read by the inbox (queue filter) and the audit log (customer filter). */
const SearchContext = createContext<string>("");
export const useStaffSearch = () => useContext(SearchContext);

const NAV = [
  { href: "/console", label: "Inbox", icon: Inbox, exact: true },
  { href: "/console/audit", label: "Audit log", icon: ScrollText, exact: false },
];

/**
 * Support console shell (spec 13.4): a collapsible left sidebar (Inbox with its pending count, Audit log) and a
 * top bar with search and the user menu. Conversations open from the inbox and the audit log.
 */
export function StaffShell({ profile, onSignOut, children }: { profile: StaffProfile | undefined; onSignOut: () => void; children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);
  const [search, setSearch] = useState("");
  const pathname = usePathname();
  const queue = useApprovalQueue();
  const pending = queue.data?.items.length;
  return (
    <SearchContext.Provider value={search}>
      <div className="flex h-dvh flex-col">
        <header className="flex shrink-0 flex-wrap items-center gap-x-3 gap-y-2 border-b px-4 py-2.5 sm:h-14 sm:flex-nowrap sm:py-0">
          <Link href="/console" className="rounded-lg text-base font-semibold tracking-tight whitespace-nowrap outline-none focus-visible:ring-3 focus-visible:ring-ring/50">
            Northwind Goods <span className="font-normal text-muted-foreground">Support</span>
          </Link>
          {/* Below 640px the search takes its own full-width row, so it never shrinks to nothing. */}
          <div className="relative order-last w-full sm:order-none sm:ml-auto sm:max-w-72 sm:min-w-0">
            <Search aria-hidden="true" className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              type="search"
              aria-label="Search by customer, order or reference"
              placeholder="Search customer, order, ACT-…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-8"
            />
          </div>
          <span className="ml-auto sm:ml-0">
            <ThemeToggle />
          </span>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" aria-label="Account menu">
                <UserRound aria-hidden="true" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="min-w-56">
              {profile && (
                <DropdownMenuLabel className="flex flex-col">
                  <span className="text-sm font-medium">{profile.name}</span>
                  <span className="text-xs font-normal text-muted-foreground">{profile.email} · Support lead</span>
                </DropdownMenuLabel>
              )}
              <DropdownMenuSeparator />
              <DropdownMenuItem onSelect={onSignOut}>
                <LogOut aria-hidden="true" /> Sign out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </header>
        <div className="flex min-h-0 flex-1 flex-col md:flex-row">
          <nav
            aria-label="Console"
            className={cn(
              "flex shrink-0 gap-1 border-b p-2 md:flex-col md:border-r md:border-b-0",
              collapsed ? "md:w-14" : "md:w-52",
            )}
          >
            {NAV.map(({ href, label, icon: Icon, exact }) => {
              const active = exact ? pathname === href : pathname.startsWith(href);
              return (
                <Link
                  key={href}
                  href={href}
                  aria-current={active ? "page" : undefined}
                  title={collapsed ? label : undefined}
                  className={cn(
                    "flex items-center gap-2 rounded-lg px-2.5 py-1.5 text-sm outline-none hover:bg-muted focus-visible:ring-3 focus-visible:ring-ring/50",
                    active ? "bg-muted font-medium text-foreground" : "text-muted-foreground",
                  )}
                >
                  <Icon aria-hidden="true" className="size-4 shrink-0" />
                  <span className={cn(collapsed && "md:sr-only")}>{label}</span>
                  {href === "/console" && pending !== undefined && (
                    <span
                      aria-label={`${pending} pending`}
                      className={cn("ml-auto rounded-md bg-primary px-1.5 text-xs font-medium text-primary-foreground tabular-nums", collapsed && "md:hidden")}
                    >
                      {pending}
                    </span>
                  )}
                </Link>
              );
            })}
            <Button
              variant="ghost"
              size="icon"
              className="mt-auto hidden md:inline-flex"
              aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
              aria-expanded={!collapsed}
              onClick={() => setCollapsed((c) => !c)}
            >
              {collapsed ? <PanelLeftOpen aria-hidden="true" /> : <PanelLeftClose aria-hidden="true" />}
            </Button>
          </nav>
          <main className="flex min-h-0 min-w-0 flex-1 flex-col">{children}</main>
        </div>
      </div>
    </SearchContext.Provider>
  );
}

function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const dark = resolvedTheme === "dark";
  return (
    <Button variant="ghost" size="icon" aria-label={dark ? "Switch to light theme" : "Switch to dark theme"} onClick={() => setTheme(dark ? "light" : "dark")}>
      {dark ? <Sun aria-hidden="true" /> : <Moon aria-hidden="true" />}
    </Button>
  );
}
