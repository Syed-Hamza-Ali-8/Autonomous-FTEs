"use client";

import { LogOut, Moon, Sun, UserRound } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTheme } from "next-themes";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { CustomerProfile } from "@/lib/api";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/orders", label: "My orders" },
  { href: "/support", label: "Support" },
];

export function StoreHeader({ profile, onSignOut }: { profile: CustomerProfile | undefined; onSignOut: () => void }) {
  const pathname = usePathname();
  const { resolvedTheme, setTheme } = useTheme();
  const dark = resolvedTheme === "dark";
  return (
    <header className="border-b">
      <div className="px-gutter mx-auto grid max-w-5xl grid-cols-[1fr_auto] items-center gap-x-6 py-2 sm:flex sm:h-14 sm:py-0">
        <Link href="/orders" className="rounded-lg text-base font-semibold tracking-tight whitespace-nowrap outline-none focus-visible:ring-3 focus-visible:ring-ring/50">
          Northwind Goods
        </Link>
        <nav aria-label="Main" className="order-last col-span-2 -ml-2.5 flex items-center gap-1 sm:order-none sm:ml-0">
          {NAV.map(({ href, label }) => {
            const active = pathname === href || pathname.startsWith(`${href}/`);
            return (
              <Link
                key={href}
                href={href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "rounded-lg px-2.5 py-1.5 text-sm whitespace-nowrap outline-none hover:bg-muted focus-visible:ring-3 focus-visible:ring-ring/50",
                  active ? "font-medium text-foreground" : "text-muted-foreground",
                )}
              >
                {label}
              </Link>
            );
          })}
        </nav>
        <div className="flex items-center justify-end gap-1 sm:ml-auto">
          <Button
            variant="ghost"
            size="icon"
            aria-label={dark ? "Switch to light theme" : "Switch to dark theme"}
            onClick={() => setTheme(dark ? "light" : "dark")}
          >
            {dark ? <Sun aria-hidden="true" /> : <Moon aria-hidden="true" />}
          </Button>
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
                  <span className="text-xs font-normal text-muted-foreground">{profile.email}</span>
                </DropdownMenuLabel>
              )}
              <DropdownMenuSeparator />
              <DropdownMenuItem onSelect={onSignOut}>
                <LogOut aria-hidden="true" /> Sign out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  );
}
