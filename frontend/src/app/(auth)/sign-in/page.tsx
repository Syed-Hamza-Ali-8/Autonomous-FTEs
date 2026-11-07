"use client";

import { Package, ReceiptText, UsersRound, type LucideIcon } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/lib/auth";

const POINTS: { icon: LucideIcon; text: string }[] = [
  { icon: Package, text: "Track every order" },
  { icon: ReceiptText, text: "Small refunds handled instantly" },
  { icon: UsersRound, text: "Larger requests reviewed by our team" },
];

type Errors = { email?: string; password?: string; form?: string };

function validate(email: string, password: string): Errors {
  const errors: Errors = {};
  if (!email.trim()) errors.email = "Enter your email address.";
  else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) errors.email = "Enter an email address like name@example.com.";
  if (!password) errors.password = "Enter your password.";
  return errors;
}

export default function SignInPage() {
  const auth = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<Errors>({});
  const [busy, setBusy] = useState(false);
  const emailRef = useRef<HTMLInputElement>(null);
  const passwordRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (auth.status === "signed_in") router.replace("/orders");
  }, [auth.status, router]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const found = validate(email, password);
    setErrors(found);
    if (found.email) return emailRef.current?.focus();
    if (found.password) return passwordRef.current?.focus();
    setBusy(true);
    const { error } = await auth.signIn(email.trim(), password);
    setBusy(false);
    if (error) setErrors({ form: "That email and password don't match an account. Check them and try again." });
  }

  return (
    <main className="px-gutter grid flex-1 place-items-center py-10">
      <div className="grid w-full max-w-4xl gap-6 md:grid-cols-2 md:items-stretch md:gap-10">
        <section aria-label="About Northwind Goods" className="flex flex-col gap-2 md:gap-6 md:rounded-xl md:bg-muted md:p-8">
          <div className="flex flex-col gap-1.5">
            <p className="text-2xl font-semibold tracking-tight md:text-3xl">Northwind Goods</p>
            <p className="text-sm text-muted-foreground md:text-base">Your orders, deliveries and refunds, with help when you need it.</p>
          </div>
          <ul className="hidden flex-col gap-4 md:flex">
            {POINTS.map(({ icon: Icon, text }) => (
              <li key={text} className="flex items-center gap-3 text-sm">
                <span aria-hidden="true" className="grid size-9 place-items-center rounded-lg border bg-background">
                  <Icon className="size-4" />
                </span>
                {text}
              </li>
            ))}
          </ul>
        </section>

        <form
          onSubmit={onSubmit}
          noValidate
          aria-labelledby="sign-in-title"
          className="flex w-full flex-col gap-5 rounded-xl border bg-card p-6 md:p-8"
        >
          <h1 id="sign-in-title" className="text-xl font-semibold">
            Sign in
          </h1>
          <Field
            id="email"
            label="Email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={setEmail}
            error={errors.email}
            ref={emailRef}
          />
          <Field
            id="password"
            label="Password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={setPassword}
            error={errors.password}
            ref={passwordRef}
          />
          {errors.form && (
            <p role="alert" className="text-sm text-destructive">
              {errors.form}
            </p>
          )}
          <Button type="submit" size="lg" className="h-10" aria-disabled={busy}>
            {busy ? "Signing in..." : "Sign in"}
          </Button>
        </form>
      </div>
    </main>
  );
}

function Field({
  ref,
  id,
  label,
  type,
  autoComplete,
  value,
  onChange,
  error,
}: {
  ref: React.Ref<HTMLInputElement>;
  id: string;
  label: string;
  type: string;
  autoComplete: string;
  value: string;
  onChange: (v: string) => void;
  error?: string;
}) {
  const errorId = `${id}-error`;
  return (
    <div className="flex flex-col gap-2">
      <Label htmlFor={id}>{label}</Label>
      <Input
        ref={ref}
        id={id}
        type={type}
        autoComplete={autoComplete}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : undefined}
        className="h-10"
      />
      {error && (
        <p id={errorId} className="text-sm text-destructive">
          {error}
        </p>
      )}
    </div>
  );
}
