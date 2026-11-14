"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { StaffShell } from "@/components/staff/staff-shell";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Toaster } from "@/components/ui/sonner";
import { ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useStaffProfile } from "@/lib/staff-queries";

// Client-side gate for the UX only. Every byte is still authorised by the API per request, from
// app.staff_users (invariant 22): a customer, or anyone else, gets 403 from every /v1/staff route.
export default function ConsoleLayout({ children }: { children: React.ReactNode }) {
  const auth = useAuth();
  const router = useRouter();
  useEffect(() => {
    if (auth.status === "signed_out") router.replace("/sign-in");
  }, [auth.status, router]);
  if (auth.status !== "signed_in") {
    return (
      <div className="px-gutter py-6" aria-busy="true" aria-label="Loading">
        <Skeleton className="h-8 w-48" />
      </div>
    );
  }
  return <StaffGate onSignOut={() => void auth.signOut()}>{children}</StaffGate>;
}

function StaffGate({ children, onSignOut }: { children: React.ReactNode; onSignOut: () => void }) {
  const profile = useStaffProfile();
  if (profile.error instanceof ApiError && profile.error.status === 403) {
    return (
      <main className="px-gutter mx-auto flex w-full max-w-md flex-1 flex-col justify-center gap-4 py-12">
        <h1 className="text-xl font-semibold">No staff access</h1>
        <p className="text-sm text-muted-foreground">You&apos;re signed in, but this login isn&apos;t a support lead account.</p>
        <Button variant="outline" className="self-start" onClick={onSignOut}>
          Sign out
        </Button>
      </main>
    );
  }
  if (profile.error) {
    return (
      <main className="px-gutter mx-auto flex w-full max-w-md flex-1 flex-col justify-center gap-4 py-12">
        <h1 className="text-xl font-semibold">The console couldn&apos;t load</h1>
        <p className="text-sm text-muted-foreground">Check your connection and try again.</p>
        <Button variant="outline" className="self-start" onClick={() => void profile.refetch()}>
          Try again
        </Button>
      </main>
    );
  }
  if (!profile.data) {
    return (
      <div className="px-gutter py-6" aria-busy="true" aria-label="Loading">
        <Skeleton className="h-8 w-48" />
      </div>
    );
  }
  return (
    <>
      <StaffShell profile={profile.data} onSignOut={onSignOut}>
        {children}
      </StaffShell>
      <Toaster position="bottom-right" />
    </>
  );
}
