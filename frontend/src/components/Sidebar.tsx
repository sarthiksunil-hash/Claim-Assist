"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import {
  Box,
  Flex,
  VStack,
  Text,
  Icon,
  Divider,
  Avatar,
  Badge,
  Tooltip,
} from "@chakra-ui/react";
import {
  FiHome,
  FiUpload,
  FiFileText,
  FiBarChart2,
  FiSettings,
  FiHelpCircle,
  FiLogOut,
  FiShield,
  FiCpu,
} from "react-icons/fi";
import { useEffect, useState } from "react";

interface NavItem {
  label: string;
  icon: React.ElementType;
  href: string;
  badge?: string;
  badgeColor?: string;
}

const mainNavItems: NavItem[] = [
  { label: "Dashboard", icon: FiHome, href: "/" },
  {
    label: "Upload Documents",
    icon: FiUpload,
    href: "/upload",
    badge: "NEW",
    badgeColor: "blue",
  },
  {
    label: "Claim Data Extraction",
    icon: FiCpu,
    href: "/pipeline",
    badge: "AI",
    badgeColor: "purple",
  },
];

const toolNavItems: NavItem[] = [
  { label: "Generate Appeal", icon: FiFileText, href: "/appeal" },
  { label: "Reports", icon: FiBarChart2, href: "/reports" },
];

const settingsNavItems: NavItem[] = [
  { label: "Settings", icon: FiSettings, href: "/settings" },
  { label: "Help & Support", icon: FiHelpCircle, href: "/help" },
];

function NavLink({ item, isActive }: { item: NavItem; isActive: boolean }) {
  return (
    <Link href={item.href} style={{ textDecoration: "none", width: "100%" }}>
      <Flex
        align="center"
        px={4}
        py={2.5}
        borderRadius="xl"
        cursor="pointer"
        bg={isActive ? "sidebar.activeBg" : "transparent"}
        color={isActive ? "sidebar.activeText" : "text.secondary"}
        fontWeight={isActive ? "600" : "500"}
        transition="all 0.2s ease"
        _hover={{
          bg: isActive ? "sidebar.activeBg" : "sidebar.hoverBg",
          color: isActive ? "sidebar.activeText" : "sidebar.hoverText",
          transform: "translateX(2px)",
        }}
        position="relative"
        role="group"
      >
        {isActive && (
          <Box
            position="absolute"
            left="-4px"
            top="50%"
            transform="translateY(-50%)"
            width="4px"
            height="60%"
            bg="brand.500"
            borderRadius="full"
          />
        )}
        <Icon
          as={item.icon}
          boxSize={5}
          mr={3}
          transition="all 0.2s"
          _groupHover={{ transform: "scale(1.05)" }}
        />
        <Text fontSize="sm">{item.label}</Text>
        {item.badge && (
          <Badge
            ml="auto"
            colorScheme={item.badgeColor || "blue"}
            variant="solid"
            fontSize="10px"
            borderRadius="full"
            px={2}
            py={0.5}
          >
            {item.badge}
          </Badge>
        )}
      </Flex>
    </Link>
  );
}

function NavSection({
  title,
  items,
  pathname,
}: {
  title: string;
  items: NavItem[];
  pathname: string;
}) {
  return (
    <Box w="full">
      <Text
        fontSize="11px"
        fontWeight="700"
        textTransform="uppercase"
        letterSpacing="wider"
        color="text.dimmed"
        px={4}
        mb={2}
      >
        {title}
      </Text>
      <VStack spacing={1} align="stretch">
        {items.map((item) => (
          <NavLink
            key={item.href}
            item={item}
            isActive={pathname === item.href}
          />
        ))}
      </VStack>
    </Box>
  );
}

export default function Sidebar() {
  const pathname = usePathname();
  const [userName, setUserName] = useState("");
  const [userEmail, setUserEmail] = useState("");

  useEffect(() => {
    const stored = localStorage.getItem("claimassist_user");
    if (stored) {
      const user = JSON.parse(stored);
      if (user.full_name) setUserName(user.full_name);
      if (user.email) setUserEmail(user.email);
    }
  }, []);

  const handleLogout = () => {
    // Clear all user-specific data
    localStorage.removeItem("claimassist_user");
    localStorage.removeItem("claimassist_token");
    localStorage.removeItem("claimassist_theme");
    localStorage.removeItem("claimassist_docs");
    localStorage.removeItem("claimassist_pipeline");
    // Clear session-scoped data (upload tracking, etc.)
    sessionStorage.clear();
    // Force full page navigation to clear all React state
    window.location.href = "/login";
  };

  return (
    <Box
      as="nav"
      position="fixed"
      left={0}
      top={0}
      bottom={0}
      width="260px"
      bg="bg.sidebar"
      borderRight="1px solid"
      borderColor="border.card"
      display="flex"
      flexDirection="column"
      zIndex={100}
      overflowY="auto"
      overflowX="hidden"
    >
      {/* Logo / Brand */}
      <Flex align="center" px={5} py={5} gap={3}>
        <Flex
          w="40px"
          h="40px"
          borderRadius="xl"
          bg="brand.500"
          align="center"
          justify="center"
          boxShadow="0 2px 8px rgba(90, 103, 216, 0.3)"
        >
          <Icon as={FiShield} color="white" boxSize={5} />
        </Flex>
        <Box>
          <Text
            fontSize="lg"
            fontWeight="800"
            color="brand.500"
            lineHeight="1.2"
            letterSpacing="-0.02em"
          >
            ClaimAssist
          </Text>
          <Text fontSize="xs" color="brand.400" fontWeight="500">
            AI-Powered Appeals
          </Text>
        </Box>
      </Flex>

      <Divider borderColor="border.card" />

      {/* Navigation */}
      <VStack spacing={6} align="stretch" px={3} py={4} flex={1}>
        <NavSection title="Main" items={mainNavItems} pathname={pathname} />
        <NavSection title="Tools" items={toolNavItems} pathname={pathname} />
        <NavSection
          title="Settings"
          items={settingsNavItems}
          pathname={pathname}
        />
      </VStack>

      <Divider borderColor="border.card" />

      {/* User Profile */}
      <Flex
        align="center"
        px={4}
        py={4}
        gap={3}
        cursor="pointer"
        _hover={{ bg: "bg.hover" }}
        transition="all 0.2s"
      >
        <Avatar
          size="sm"
          name={userName}
          bg="brand.500"
          color="white"
          fontWeight="700"
        />
        <Box flex={1}>
          <Text fontSize="sm" fontWeight="600" color="text.primary">
            {userName}
          </Text>
          <Text fontSize="xs" color="text.muted" noOfLines={1}>
            {userEmail}
          </Text>
        </Box>
        <Tooltip label="Sign out" placement="top">
          <Box onClick={handleLogout}>
            <Icon
              as={FiLogOut}
              color="text.dimmed"
              boxSize={4}
              cursor="pointer"
              _hover={{ color: "red.500" }}
              transition="color 0.2s"
            />
          </Box>
        </Tooltip>
      </Flex>
    </Box>
  );
}
