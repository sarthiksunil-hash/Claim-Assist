"use client";

import {
  Box,
  Flex,
  Text,
  Icon,
  Stat,
  StatHelpText,
  StatArrow,
} from "@chakra-ui/react";
import { IconType } from "react-icons";

interface StatsCardProps {
  label: string;
  value: string | number;
  icon: IconType;
  trend?: number;
  trendLabel?: string;
  iconBg?: string;
  iconColor?: string;
  delay?: number;
}

export default function StatsCard({
  label,
  value,
  icon,
  trend,
  trendLabel,
  iconBg = "brand.50",
  iconColor = "brand.500",
  delay = 0,
}: StatsCardProps) {
  return (
    <Box
      bg="bg.card"
      borderRadius="2xl"
      p={5}
      border="1px solid"
      borderColor="border.card"
      transition="all 0.3s ease"
      _hover={{
        transform: "translateY(-4px)",
        boxShadow: "0 8px 25px rgba(90, 103, 216, 0.1)",
        borderColor: "brand.200",
      }}
      className="animate-fade-in-up"
      style={{ animationDelay: `${delay}ms` }}
      position="relative"
      overflow="hidden"
    >
      {/* Subtle gradient overlay */}
      <Box
        position="absolute"
        top={0}
        right={0}
        width="80px"
        height="80px"
        bg="bg.accent"
        borderRadius="full"
        transform="translate(30%, -30%)"
        opacity={0.5}
      />

      <Flex justify="space-between" align="flex-start" mb={3}>
        <Box>
          <Text
            fontSize="xs"
            fontWeight="600"
            textTransform="uppercase"
            letterSpacing="wider"
            color="text.muted"
            mb={1}
          >
            {label}
          </Text>
          <Text
            fontSize="2xl"
            fontWeight="800"
            color="text.primary"
            lineHeight="1.1"
          >
            {value}
          </Text>
        </Box>
        <Flex
          w="44px"
          h="44px"
          borderRadius="xl"
          bg={iconBg}
          align="center"
          justify="center"
          flexShrink={0}
        >
          <Icon as={icon} boxSize={5} color={iconColor} />
        </Flex>
      </Flex>

      {trend !== undefined && (
        <Stat size="sm">
          <StatHelpText mb={0} fontSize="xs" color="text.muted">
            <StatArrow type={trend >= 0 ? "increase" : "decrease"} />
            <Text as="span" fontWeight="600" color={trend >= 0 ? "green.500" : "red.500"}>
              {Math.abs(trend)}%
            </Text>{" "}
            {trendLabel || "vs last week"}
          </StatHelpText>
        </Stat>
      )}
    </Box>
  );
}
