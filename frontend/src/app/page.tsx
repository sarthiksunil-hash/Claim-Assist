"use client";

import { useState, useEffect } from "react";
import {
  Box,
  Flex,
  Text,
  Grid,
  GridItem,
  Icon,
  Button,
  HStack,
  VStack,
  Badge,
  Spinner,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
} from "@chakra-ui/react";
import {
  FiSearch,
  FiFileText,
  FiActivity,
  FiTrendingUp,
  FiUpload,
  FiClock,
  FiArrowRight,
  FiDatabase,
} from "react-icons/fi";
import Sidebar from "@/components/Sidebar";
import StatsCard from "@/components/StatsCard";
import ChatWidget from "@/components/ChatWidget";
import Link from "next/link";
import { getDashboardStats } from "@/lib/api";

interface DashboardStats {
  total_documents: number;
  claims_analyzed: number;
  appeals_generated: number;
  success_rate: number;
  active_cases: number;
  recent_claims: Array<{
    patient_name: string;
    insurer: string;
    status: string;
    timestamp: string;
  }>;
}

export default function Dashboard() {
  const [userName, setUserName] = useState("");
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    try {
      const stored = localStorage.getItem("claimassist_user");
      if (stored) {
        const userData = JSON.parse(stored);
        const name = userData.full_name || userData.email || "User";
        setUserName(name.split(" ")[0]);
      }
    } catch {
      setUserName("User");
    }
  }, []);

  // Fetch real dashboard stats from backend
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await getDashboardStats();
        setStats(response.data);
      } catch (err) {
        console.log("Dashboard stats fetch error:", err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchStats();
  }, []);

  const claimsAnalyzed = stats?.claims_analyzed ?? 0;
  const appealsGenerated = stats?.appeals_generated ?? 0;
  const activeCases = stats?.active_cases ?? 0;
  const totalDocs = stats?.total_documents ?? 0;
  const recentClaims = stats?.recent_claims ?? [];

  return (
    <Flex minH="100vh" bg="bg.page">
      <Sidebar />

      {/* Main Content */}
      <Box ml="260px" flex={1} p={8} maxW="calc(100vw - 260px)">
        {/* Header */}
        <Flex justify="space-between" align="center" mb={6}>
          <Text fontSize="2xl" fontWeight="800" color="text.primary">
            Dashboard
          </Text>
          <HStack spacing={3}>
            <Button
              variant="secondary"
              size="sm"
              leftIcon={<FiClock />}
              fontSize="sm"
            >
              Last 7 Days
            </Button>
          </HStack>
        </Flex>

        {/* Welcome Banner */}
        <Box
          borderRadius="2xl"
          p={8}
          mb={6}
          position="relative"
          overflow="hidden"
          bg="linear-gradient(135deg, #5A67D8 0%, #667EEA 40%, #7F9CF5 100%)"
          color="white"
          className="animate-fade-in"
        >
          {/* Decorative circles */}
          <Box
            position="absolute"
            top="-40px"
            right="-20px"
            w="200px"
            h="200px"
            borderRadius="full"
            bg="whiteAlpha.100"
          />
          <Box
            position="absolute"
            bottom="-60px"
            right="100px"
            w="150px"
            h="150px"
            borderRadius="full"
            bg="whiteAlpha.100"
          />
          <Flex
            align="center"
            gap={2}
            mb={2}
            position="relative"
            zIndex={1}
          >
            <Box
              w="10px"
              h="10px"
              borderRadius="full"
              bg="green.300"
            />
            <Text fontSize="xs" fontWeight="600" opacity={0.9}>
              PERSONAL DASHBOARD
            </Text>
          </Flex>
          <Text
            fontSize="3xl"
            fontWeight="800"
            mb={2}
            position="relative"
            zIndex={1}
          >
            Welcome back, {userName || "User"} 👋
          </Text>
          <Text
            fontSize="md"
            opacity={0.9}
            position="relative"
            zIndex={1}
          >
            Your claim appeal journey continues. Analyze denials, generate
            appeals, and fight for your insurance rights.
          </Text>
        </Box>

        {/* Stats Grid — real data from API */}
        <Grid templateColumns="repeat(4, 1fr)" gap={5} mb={6}>
          <GridItem>
            <StatsCard
              label="Documents Scanned"
              value={isLoading ? "..." : totalDocs}
              icon={FiDatabase}
              trend={totalDocs > 0 ? totalDocs : 0}
              trendLabel="uploaded"
              delay={50}
            />
          </GridItem>
          <GridItem>
            <StatsCard
              label="Claims Analyzed"
              value={isLoading ? "..." : claimsAnalyzed}
              icon={FiSearch}
              trend={claimsAnalyzed > 0 ? claimsAnalyzed : 0}
              trendLabel="total"
              iconBg="green.50"
              iconColor="green.500"
              delay={100}
            />
          </GridItem>
          <GridItem>
            <StatsCard
              label="Appeals Generated"
              value={isLoading ? "..." : appealsGenerated}
              icon={FiFileText}
              trend={appealsGenerated > 0 ? appealsGenerated : 0}
              trendLabel="generated"
              iconBg="purple.50"
              iconColor="purple.500"
              delay={150}
            />
          </GridItem>
          <GridItem>
            <StatsCard
              label="Active Cases"
              value={isLoading ? "..." : activeCases}
              icon={FiActivity}
              trend={activeCases > 0 ? activeCases : 0}
              trendLabel="cases"
              iconBg="orange.50"
              iconColor="orange.500"
              delay={200}
            />
          </GridItem>
        </Grid>

        {/* Quick Actions */}
        <Grid templateColumns="repeat(2, 1fr)" gap={5} mb={6}>
          <GridItem>
            <Link href="/upload" style={{ textDecoration: "none" }}>
              <Flex
                bg="bg.card"
                borderRadius="2xl"
                p={6}
                border="1px solid"
                borderColor="border.card"
                align="center"
                gap={4}
                cursor="pointer"
                transition="all 0.3s ease"
                _hover={{
                  transform: "translateY(-2px)",
                  boxShadow: "0 8px 25px rgba(90, 103, 216, 0.1)",
                  borderColor: "brand.200",
                }}
                className="animate-fade-in-up stagger-3"
              >
                <Flex
                  w="52px"
                  h="52px"
                  borderRadius="xl"
                  bg="brand.50"
                  align="center"
                  justify="center"
                >
                  <Icon as={FiUpload} boxSize={6} color="brand.500" />
                </Flex>
                <Box>
                  <Text fontWeight="700" fontSize="md" color="text.primary">
                    Upload New Claim
                  </Text>
                  <Text fontSize="sm" color="text.muted">
                    Upload policy, medical reports & denial letters
                  </Text>
                </Box>
              </Flex>
            </Link>
          </GridItem>
          <GridItem>
            <Link href="/appeal" style={{ textDecoration: "none" }}>
              <Flex
                bg="bg.card"
                borderRadius="2xl"
                p={6}
                border="1px solid"
                borderColor="border.card"
                align="center"
                gap={4}
                cursor="pointer"
                transition="all 0.3s ease"
                _hover={{
                  transform: "translateY(-2px)",
                  boxShadow: "0 8px 25px rgba(90, 103, 216, 0.1)",
                  borderColor: "brand.200",
                }}
                className="animate-fade-in-up stagger-4"
              >
                <Flex
                  w="52px"
                  h="52px"
                  borderRadius="xl"
                  bg="green.50"
                  _dark={{ bg: "green.900" }}
                  align="center"
                  justify="center"
                >
                  <Icon as={FiTrendingUp} boxSize={6} color="green.500" />
                </Flex>
                <Box>
                  <Text fontWeight="700" fontSize="md" color="text.primary">
                    View Recent Appeals
                  </Text>
                  <Text fontSize="sm" color="text.muted">
                    Track appeal status and download letters
                  </Text>
                </Box>
              </Flex>
            </Link>
          </GridItem>
        </Grid>

        {/* Recent Claims Section */}
        <Box
          bg="bg.card"
          borderRadius="2xl"
          border="1px solid"
          borderColor="border.card"
          overflow="hidden"
          className="animate-fade-in-up stagger-5"
        >
          <Flex
            justify="space-between"
            align="center"
            px={6}
            py={4}
            borderBottom="1px solid"
            borderColor="border.subtle"
          >
            <Text fontWeight="700" fontSize="lg" color="text.primary">
              Recent Claims
            </Text>
            {recentClaims.length > 0 && (
              <Badge colorScheme="brand" variant="subtle" borderRadius="full" px={3}>
                {recentClaims.length} claim{recentClaims.length !== 1 ? "s" : ""}
              </Badge>
            )}
          </Flex>

          {isLoading ? (
            <Flex justify="center" py={12}>
              <Spinner size="lg" color="brand.500" />
            </Flex>
          ) : recentClaims.length > 0 ? (
            <TableContainer>
              <Table variant="simple" size="sm">
                <Thead>
                  <Tr>
                    <Th fontSize="xs" color="text.muted">Patient</Th>
                    <Th fontSize="xs" color="text.muted">Insurer</Th>
                    <Th fontSize="xs" color="text.muted">Status</Th>
                    <Th fontSize="xs" color="text.muted">Date</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {recentClaims.map((claim, idx) => (
                    <Tr key={idx} _hover={{ bg: "bg.hover" }}>
                      <Td fontWeight="600" fontSize="sm">{claim.patient_name}</Td>
                      <Td fontSize="sm" color="text.secondary">{claim.insurer}</Td>
                      <Td>
                        <Badge
                          colorScheme={claim.status === "completed" ? "green" : "orange"}
                          variant="subtle"
                          borderRadius="full"
                          fontSize="10px"
                        >
                          {claim.status}
                        </Badge>
                      </Td>
                      <Td fontSize="xs" color="text.muted">
                        {claim.timestamp ? new Date(claim.timestamp).toLocaleDateString() : "—"}
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </TableContainer>
          ) : (
            <VStack spacing={4} py={12} px={6}>
              <Flex
                w="80px"
                h="80px"
                borderRadius="full"
                bg="brand.50"
                align="center"
                justify="center"
              >
                <Icon as={FiFileText} boxSize={8} color="brand.300" />
              </Flex>
              <VStack spacing={1}>
                <Text fontWeight="700" fontSize="md" color="text.primary">
                  No claims yet
                </Text>
                <Text fontSize="sm" color="text.muted" textAlign="center" maxW="400px">
                  Upload your first claim documents to get started. Our AI will analyze
                  your policy, medical reports, and denial letters.
                </Text>
              </VStack>
              <Link href="/upload" style={{ textDecoration: "none" }}>
                <Button
                  variant="primary"
                  size="md"
                  rightIcon={<FiArrowRight />}
                  mt={2}
                >
                  Upload Your First Claim
                </Button>
              </Link>
            </VStack>
          )}
        </Box>
      </Box>

      <ChatWidget />
    </Flex>
  );
}
