"use client";

import {
  Box, Flex, Text, VStack, Icon, Button,
} from "@chakra-ui/react";
import {
  FiSearch, FiArrowRight, FiUpload,
} from "react-icons/fi";
import Sidebar from "@/components/Sidebar";
import ChatWidget from "@/components/ChatWidget";
import Link from "next/link";

export default function AnalysisPage() {
  return (
    <Flex minH="100vh" bg="bg.page">
      <Sidebar />

      <Box ml="260px" flex={1} p={8} maxW="calc(100vw - 260px)">
        {/* Header */}
        <Flex justify="space-between" align="center" mb={6}>
          <Box>
            <Text fontSize="2xl" fontWeight="800" color="text.primary">
              Claim Analysis
            </Text>
            <Text color="text.muted" fontSize="sm">
              AI-powered analysis of your insurance claim documents
            </Text>
          </Box>
        </Flex>

        {/* Empty State */}
        <Box
          bg="bg.card"
          borderRadius="2xl"
          border="1px solid"
          borderColor="border.card"
          className="animate-fade-in"
        >
          <VStack spacing={5} py={16} px={8}>
            <Flex
              w="96px"
              h="96px"
              borderRadius="full"
              bg="brand.50"
              align="center"
              justify="center"
            >
              <Icon as={FiSearch} boxSize={10} color="brand.300" />
            </Flex>
            <VStack spacing={2}>
              <Text fontWeight="700" fontSize="lg" color="text.primary">
                No analysis available
              </Text>
              <Text fontSize="sm" color="text.muted" textAlign="center" maxW="500px" lineHeight="1.7">
                Upload your insurance documents first, then run the analysis pipeline.
                Our AI agents will examine your policy, medical reports, and denial letter
                to identify discrepancies and build your appeal case.
              </Text>
            </VStack>
            <Link href="/upload" style={{ textDecoration: "none" }}>
              <Button
                variant="primary"
                size="lg"
                rightIcon={<FiArrowRight />}
                leftIcon={<FiUpload />}
                mt={3}
              >
                Upload Documents to Get Started
              </Button>
            </Link>
          </VStack>
        </Box>
      </Box>

      <ChatWidget />
    </Flex>
  );
}
