"use client";

import { useState, useEffect } from "react";
import {
  Box, Flex, Text, VStack, HStack, Icon, 
  Badge, Grid, GridItem, Spinner,
  Progress,
} from "@chakra-ui/react";
import {
  FiBarChart2, FiFileText, FiCheckCircle, FiClock, FiShield,
  FiHeart, FiActivity, FiTrendingUp,
} from "react-icons/fi";
import Sidebar from "@/components/Sidebar";
import ChatWidget from "@/components/ChatWidget";
import api from "@/lib/api";

interface PipelineResult {
  pipeline_id: string;
  status: string;
  total_processing_time: string;
  timestamp: string;
  claim_summary: {
    patient_name: string;
    insurer_name: string;
    claim_amount: number;
    denial_reason: string;
  };
  overall_assessment: {
    appeal_strength: string;
    policy_alignment_score: number;
    medical_necessity_score: number;
    irdai_violations_count: number;
    irdai_verified: boolean;
    medical_kb_verified: boolean;
  };
}

export default function ReportsPage() {
  const [pipelineResult, setPipelineResult] = useState<PipelineResult | null>(null);
  const [docsCount, setDocsCount] = useState(0);
  const [appealsCount, setAppealsCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch pipeline result
        const pipelineRes = await api.get("/api/pipeline/latest-result");
        if (pipelineRes.data && pipelineRes.data.status === "completed") {
          setPipelineResult(pipelineRes.data);
        }
      } catch (e) {
        console.log("No pipeline result:", e);
      }

      try {
        // Fetch documents count
        const docsRes = await api.get("/api/documents/");
        setDocsCount(docsRes.data?.total || 0);
      } catch (e) {
        console.log("No docs:", e);
      }

      try {
        // Fetch appeals count
        const appealsRes = await api.get("/api/appeals/");
        setAppealsCount(appealsRes.data?.total || 0);
      } catch (e) {
        console.log("No appeals:", e);
      }

      setIsLoading(false);
    };
    fetchData();
  }, []);

  if (isLoading) {
    return (
      <Flex minH="100vh" bg="bg.page">
        <Sidebar />
        <Flex ml="260px" flex={1} justify="center" align="center">
          <Spinner size="xl" color="brand.500" thickness="4px" />
        </Flex>
      </Flex>
    );
  }

  const assessment = pipelineResult?.overall_assessment;
  const summary = pipelineResult?.claim_summary;

  return (
    <Flex minH="100vh" bg="bg.page">
      <Sidebar />
      <Box ml="260px" flex={1} p={8} maxW="calc(100vw - 260px)">
        {/* Header */}
        <Flex justify="space-between" align="center" mb={6}>
          <Box>
            <Text fontSize="2xl" fontWeight="800" color="text.primary">
              Reports
            </Text>
            <Text color="text.muted" fontSize="sm">
              Overview of your claim analysis, pipeline results, and appeal status
            </Text>
          </Box>
          {pipelineResult && (
            <Badge
              colorScheme="green"
              variant="subtle"
              borderRadius="full"
              px={4}
              py={2}
              fontSize="sm"
            >
              <Icon as={FiCheckCircle} mr={1} />
              Pipeline Complete
            </Badge>
          )}
        </Flex>

        {/* No Data State */}
        {!pipelineResult && (
          <Box
            bg="bg.card"
            borderRadius="2xl"
            border="1px solid"
            borderColor="border.card"
            className="animate-fade-in"
          >
            <VStack spacing={5} py={16} px={8}>
              <Flex w="96px" h="96px" borderRadius="full" bg="brand.50" align="center" justify="center">
                <Icon as={FiBarChart2} boxSize={10} color="brand.300" />
              </Flex>
              <VStack spacing={2}>
                <Text fontWeight="700" fontSize="lg" color="text.primary">
                  No reports available yet
                </Text>
                <Text fontSize="sm" color="text.muted" textAlign="center" maxW="480px" lineHeight="1.7">
                  Upload documents and run the claim analysis pipeline to see detailed reports
                  with scores, regulatory analysis, and appeal recommendations.
                </Text>
              </VStack>
            </VStack>
          </Box>
        )}

        {/* Reports Content */}
        {pipelineResult && (
          <VStack spacing={6} align="stretch" className="animate-fade-in">
            {/* Stats Grid */}
            <Grid templateColumns="repeat(4, 1fr)" gap={4}>
              <GridItem>
                <Box bg="bg.card" borderRadius="2xl" border="1px solid" borderColor="border.card" p={5}>
                  <HStack spacing={3} mb={3}>
                    <Flex w="40px" h="40px" borderRadius="xl" bg="brand.50" align="center" justify="center">
                      <Icon as={FiFileText} boxSize={5} color="brand.500" />
                    </Flex>
                    <Text fontSize="xs" fontWeight="600" color="text.muted" textTransform="uppercase">
                      Documents
                    </Text>
                  </HStack>
                  <Text fontSize="2xl" fontWeight="800" color="text.primary">{docsCount}</Text>
                  <Text fontSize="xs" color="text.muted">uploaded & processed</Text>
                </Box>
              </GridItem>
              <GridItem>
                <Box bg="bg.card" borderRadius="2xl" border="1px solid" borderColor="border.card" p={5}>
                  <HStack spacing={3} mb={3}>
                    <Flex w="40px" h="40px" borderRadius="xl" bg="green.50" _dark={{ bg: "green.900" }} align="center" justify="center">
                      <Icon as={FiCheckCircle} boxSize={5} color="green.500" />
                    </Flex>
                    <Text fontSize="xs" fontWeight="600" color="text.muted" textTransform="uppercase">
                      Appeals
                    </Text>
                  </HStack>
                  <Text fontSize="2xl" fontWeight="800" color="text.primary">{appealsCount}</Text>
                  <Text fontSize="xs" color="text.muted">generated</Text>
                </Box>
              </GridItem>
              <GridItem>
                <Box bg="bg.card" borderRadius="2xl" border="1px solid" borderColor="border.card" p={5}>
                  <HStack spacing={3} mb={3}>
                    <Flex w="40px" h="40px" borderRadius="xl" bg="red.50" _dark={{ bg: "red.900" }} align="center" justify="center">
                      <Icon as={FiShield} boxSize={5} color="red.500" />
                    </Flex>
                    <Text fontSize="xs" fontWeight="600" color="text.muted" textTransform="uppercase">
                      IRDAI Violations
                    </Text>
                  </HStack>
                  <Text fontSize="2xl" fontWeight="800" color="text.primary">
                    {assessment?.irdai_violations_count || 0}
                  </Text>
                  <Text fontSize="xs" color="text.muted">found in denial</Text>
                </Box>
              </GridItem>
              <GridItem>
                <Box bg="bg.card" borderRadius="2xl" border="1px solid" borderColor="border.card" p={5}>
                  <HStack spacing={3} mb={3}>
                    <Flex w="40px" h="40px" borderRadius="xl" bg="purple.50" _dark={{ bg: "purple.900" }} align="center" justify="center">
                      <Icon as={FiActivity} boxSize={5} color="purple.500" />
                    </Flex>
                    <Text fontSize="xs" fontWeight="600" color="text.muted" textTransform="uppercase">
                      Processing Time
                    </Text>
                  </HStack>
                  <Text fontSize="2xl" fontWeight="800" color="text.primary">
                    {pipelineResult.total_processing_time}
                  </Text>
                  <Text fontSize="xs" color="text.muted">pipeline duration</Text>
                </Box>
              </GridItem>
            </Grid>

            {/* Claim Summary */}
            <Box
              bg="linear-gradient(135deg, #1A1A2E 0%, #3C366B 35%, #5A67D8 100%)"
              borderRadius="2xl"
              p={6}
              color="white"
            >
              <Text fontWeight="700" fontSize="lg" mb={4}>Claim Summary</Text>
              <Grid templateColumns="repeat(2, 1fr)" gap={4}>
                <HStack spacing={3}>
                  <Text fontSize="xs" color="whiteAlpha.600" minW="80px">Patient:</Text>
                  <Text fontWeight="600" fontSize="sm">{summary?.patient_name}</Text>
                </HStack>
                <HStack spacing={3}>
                  <Text fontSize="xs" color="whiteAlpha.600" minW="80px">Insurer:</Text>
                  <Text fontWeight="600" fontSize="sm">{summary?.insurer_name}</Text>
                </HStack>
                <HStack spacing={3}>
                  <Text fontSize="xs" color="whiteAlpha.600" minW="80px">Amount:</Text>
                  <Text fontWeight="600" fontSize="sm">₹{summary?.claim_amount?.toLocaleString()}</Text>
                </HStack>
                <HStack spacing={3}>
                  <Text fontSize="xs" color="whiteAlpha.600" minW="80px">Denial:</Text>
                  <Text fontWeight="600" fontSize="sm">{summary?.denial_reason}</Text>
                </HStack>
              </Grid>
            </Box>

            {/* Scores */}
            <Grid templateColumns="repeat(3, 1fr)" gap={4}>
              {/* Appeal Strength */}
              <GridItem>
                <Box bg="bg.card" borderRadius="2xl" border="1px solid" borderColor="border.card" p={6}>
                  <HStack spacing={2} mb={4}>
                    <Icon as={FiTrendingUp} boxSize={5} color="brand.500" />
                    <Text fontWeight="700" fontSize="md" color="text.primary">Appeal Strength</Text>
                  </HStack>
                  <Flex justify="center" mb={4}>
                    <Badge
                      colorScheme={
                        assessment?.appeal_strength === "strong" ? "green"
                        : assessment?.appeal_strength === "moderate" ? "yellow"
                        : "red"
                      }
                      variant="solid"
                      borderRadius="full"
                      px={6}
                      py={2}
                      fontSize="lg"
                      fontWeight="800"
                      textTransform="uppercase"
                    >
                      {assessment?.appeal_strength}
                    </Badge>
                  </Flex>
                  <Text fontSize="xs" color="text.muted" textAlign="center">
                    Based on policy analysis and medical evidence
                  </Text>
                </Box>
              </GridItem>

              {/* Policy Alignment */}
              <GridItem>
                <Box bg="bg.card" borderRadius="2xl" border="1px solid" borderColor="border.card" p={6}>
                  <HStack spacing={2} mb={4}>
                    <Icon as={FiShield} boxSize={5} color="blue.500" />
                    <Text fontWeight="700" fontSize="md" color="text.primary">Policy Alignment</Text>
                  </HStack>
                  <Text fontSize="3xl" fontWeight="800" color="blue.600" textAlign="center" mb={2}>
                    {assessment?.policy_alignment_score || 0}%
                  </Text>
                  <Progress
                    value={assessment?.policy_alignment_score || 0}
                    size="sm"
                    colorScheme="blue"
                    borderRadius="full"
                    mb={2}
                  />
                  <HStack justify="center" spacing={2}>
                    {assessment?.irdai_verified && (
                      <Badge colorScheme="blue" variant="subtle" borderRadius="full" fontSize="10px">
                        <Icon as={FiShield} mr={1} /> IRDAI Verified
                      </Badge>
                    )}
                  </HStack>
                </Box>
              </GridItem>

              {/* Medical Necessity */}
              <GridItem>
                <Box bg="bg.card" borderRadius="2xl" border="1px solid" borderColor="border.card" p={6}>
                  <HStack spacing={2} mb={4}>
                    <Icon as={FiHeart} boxSize={5} color="green.500" />
                    <Text fontWeight="700" fontSize="md" color="text.primary">Medical Necessity</Text>
                  </HStack>
                  <Text fontSize="3xl" fontWeight="800" color="green.600" textAlign="center" mb={2}>
                    {assessment?.medical_necessity_score || 0}%
                  </Text>
                  <Progress
                    value={assessment?.medical_necessity_score || 0}
                    size="sm"
                    colorScheme="green"
                    borderRadius="full"
                    mb={2}
                  />
                  <HStack justify="center" spacing={2}>
                    {assessment?.medical_kb_verified && (
                      <Badge colorScheme="green" variant="subtle" borderRadius="full" fontSize="10px">
                        <Icon as={FiHeart} mr={1} /> KB Verified
                      </Badge>
                    )}
                  </HStack>
                </Box>
              </GridItem>
            </Grid>

            {/* Pipeline Info */}
            <Box bg="bg.card" borderRadius="2xl" border="1px solid" borderColor="border.card" p={5}>
              <HStack spacing={3} mb={3}>
                <Icon as={FiClock} boxSize={4} color="text.dimmed" />
                <Text fontWeight="600" fontSize="sm" color="text.muted">Pipeline Details</Text>
              </HStack>
              <HStack spacing={8} flexWrap="wrap">
                <HStack spacing={2}>
                  <Text fontSize="xs" color="text.dimmed">Pipeline ID:</Text>
                  <Text fontSize="xs" fontWeight="600" color="text.primary">{pipelineResult.pipeline_id}</Text>
                </HStack>
                <HStack spacing={2}>
                  <Text fontSize="xs" color="text.dimmed">Completed:</Text>
                  <Text fontSize="xs" fontWeight="600" color="text.primary">
                    {new Date(pipelineResult.timestamp).toLocaleString()}
                  </Text>
                </HStack>
                <HStack spacing={2}>
                  <Text fontSize="xs" color="text.dimmed">Duration:</Text>
                  <Text fontSize="xs" fontWeight="600" color="text.primary">{pipelineResult.total_processing_time}</Text>
                </HStack>
              </HStack>
            </Box>
          </VStack>
        )}
      </Box>
      <ChatWidget />
    </Flex>
  );
}
