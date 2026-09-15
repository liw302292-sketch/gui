"use client";

import { Toaster as SonnerToaster, toast } from "sonner";

export function Toaster() {
  return (
    <SonnerToaster
      position="top-center"
      toastOptions={{
        style: {
          borderRadius: "14px",
          border: "1px solid var(--color-line)",
          boxShadow: "var(--shadow-float)",
          color: "var(--color-ink)",
          fontSize: "13.5px",
        },
      }}
    />
  );
}

export { toast };

