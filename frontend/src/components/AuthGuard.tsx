"use client";

import { useEffect, useState, useCallback } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Flex, Spinner, Text, VStack } from "@chakra-ui/react";

const PUBLIC_ROUTES = ["/login"];

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [isChecking, setIsChecking] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const checkAuth = useCallback(() => {
    // Public routes — allow through
    if (PUBLIC_ROUTES.includes(pathname)) {
      setIsChecking(false);
      setIsAuthenticated(true);
      return;
    }

    // On a brand-new browser session, require fresh login.
    // sessionStorage is cleared when the tab/browser closes,
    // so if our flag is missing it means this is a new session.
    const sessionActive = sessionStorage.getItem("claimassist_session_active");
    if (!sessionActive) {
      // New session — clear any stale login data and redirect
      localStorage.removeItem("claimassist_user");
      sessionStorage.clear();
      setIsAuthenticated(false);
      setIsChecking(false);
      router.replace("/login");
      return;
    }

    // Check localStorage for user
    try {
      const stored = localStorage.getItem("claimassist_user");
      if (stored) {
        const userData = JSON.parse(stored);
        if (userData && userData.email) {
          setIsAuthenticated(true);
          setIsChecking(false);
          return;
        }
      }
    } catch {
      // Invalid JSON
    }

    // Not authenticated — redirect to login
    setIsAuthenticated(false);
    setIsChecking(false);
    router.replace("/login");
  }, [pathname, router]);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  // Also listen for storage changes (logout in another tab, etc.)
  useEffect(() => {
    const onStorage = (e: StorageEvent) => {
      if (e.key === "claimassist_user" && !e.newValue) {
        setIsAuthenticated(false);
        router.replace("/login");
      }
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, [router]);

  if (isChecking) {
    return (
      <Flex
        minH="100vh"
        align="center"
        justify="center"
        bg="linear-gradient(135deg, #1A1A2E 0%, #16213E 50%, #0F3460 100%)"
      >
        <VStack spacing={4}>
          <Spinner size="xl" color="white" thickness="4px" speed="0.65s" />
          <Text color="whiteAlpha.700" fontSize="sm" fontWeight="500">
            Loading ClaimAssist...
          </Text>
        </VStack>
      </Flex>
    );
  }

  if (!isAuthenticated && !PUBLIC_ROUTES.includes(pathname)) {
    return (
      <Flex
        minH="100vh"
        align="center"
        justify="center"
        bg="linear-gradient(135deg, #1A1A2E 0%, #16213E 50%, #0F3460 100%)"
      >
        <VStack spacing={4}>
          <Spinner size="xl" color="white" thickness="4px" speed="0.65s" />
          <Text color="whiteAlpha.700" fontSize="sm" fontWeight="500">
            Redirecting to login...
          </Text>
        </VStack>
      </Flex>
    );
  }

  return <>{children}</>;
}
