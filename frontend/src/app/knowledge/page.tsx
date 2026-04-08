"use client";

import {
  Box, Flex, Text, VStack, Icon, Button,
} from "@chakra-ui/react";
import {
  FiDatabase, FiArrowRight, FiUpload,
} from "react-icons/fi";
import Sidebar from "@/components/Sidebar";
import ChatWidget from "@/components/ChatWidget";
import Link from "next/link";

export default function KnowledgePage() {
  return (
    <Flex minH="100vh" bg="bg.page">
      <Sidebar />
      <Box ml="260px" flex={1} p={8} maxW="calc(100vw - 260px)">
        <Flex justify="space-between" align="center" mb={6}>
          <Box>
            <Text fontSize="2xl" fontWeight="800" color="text.primary">Knowledge Graph</Text>
            <Text color="text.muted" fontSize="sm">
              Insurance policy–medical evidence relationship explorer
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
              bg="purple.50"
              _dark={{ bg: "purple.900" }}
              align="center"
              justify="center"
            >
              <Icon as={FiDatabase} boxSize={10} color="purple.300" />
            </Flex>
            <VStack spacing={2}>
              <Text fontWeight="700" fontSize="lg" color="text.primary">
                Knowledge graph is empty
              </Text>
              <Text fontSize="sm" color="text.muted" textAlign="center" maxW="500px" lineHeight="1.7">
                The knowledge graph visualizes relationships between your policy clauses,
                medical conditions, procedures, and IRDAI regulations. Upload and analyze
                your claim documents to populate the graph.
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
                Upload Documents to Build Graph
              </Button>
            </Link>
          </VStack>
        </Box>
      </Box>
      <ChatWidget />
    </Flex>
  );
}
