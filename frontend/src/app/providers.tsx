"use client";

import { ChakraProvider } from "@chakra-ui/react";
import theme from "@/theme";
import AuthGuard from "@/components/AuthGuard";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ChakraProvider theme={theme}>
      <AuthGuard>{children}</AuthGuard>
    </ChakraProvider>
  );
}
