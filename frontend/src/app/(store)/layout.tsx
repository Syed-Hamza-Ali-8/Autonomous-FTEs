"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";

import { ChatProvider } from "@/components/chat/chat-provider";
import { StoreHeader } from "@/components/store/store-header";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useProfile } from "@/lib/queries";

// Client-side gate for the UX only. Every byte of data is still authorised by the API per request.
export default function StoreLayout({ children }: { children: React.ReactNode }) {
  const auth = useAuth();
  const router = useRouter();
  useEffect(() => {
    if (auth.status === "signed_out") router.replace("/sign-in");
  }, [auth.status, router]);

  if (auth.status !== "signed_in") {
    return (
      <div className="px-gutter mx-auto w-full max-w-5xl py-6" aria-busy="true" aria-label="Loading">
        <Skeleton className="h-8 w-48" />
      </div>
    );
  }
  return <SignedInStore onSignOut={() => void auth.signOut()}>{children}</SignedInStore>;
}

function SignedInStore({ children, onSignOut }: { children: React.ReactNode; onSignOut: () => void }) {
  const profile = useProfile();
  const pathname = usePathname();
  if (profile.error instanceof ApiError && profile.error.status === 403) {
    return (
      <main className="px-gutter mx-auto flex w-full max-w-md flex-1 flex-col justify-center gap-4 py-12">
        <h1 className="text-xl font-semibold">No store account</h1>
        <p className="text-sm text-muted-foreground">
          You&apos;re signed in, but this login isn&apos;t linked to a Northwind Goods customer account.
        </p>
        <Button variant="outline" className="self-start" onClick={onSignOut}>
          Sign out
        </Button>
      </main>
    );
  }
  if (pathname === "/support") {
    // A full-height column so the chat fills the viewport below the header (100dvh tracks the
    // browser UI and, with interactive-widget=resizes-content, the on-screen keyboard).
    return (
      <ChatProvider>
        <div className="flex h-dvh flex-col">
          <StoreHeader profile={profile.data} onSignOut={onSignOut} />
          <main className="mx-auto flex min-h-0 w-full max-w-5xl flex-1 flex-col sm:px-gutter sm:py-8">{children}</main>
        </div>
      </ChatProvider>
    );
  }
  return (
    <ChatProvider>
      <StoreHeader profile={profile.data} onSignOut={onSignOut} />
      <main className="px-gutter mx-auto w-full max-w-5xl flex-1 pt-8 pb-16">{children}</main>
    </ChatProvider>
  );
}
