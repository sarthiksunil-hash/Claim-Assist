"use client";

import { useState, useEffect } from "react";
import {
  Box, Flex, Text, VStack, HStack, Icon, Button,
  Badge, Spinner, Checkbox, useToast,
} from "@chakra-ui/react";
import {
  FiFileText, FiArrowRight, FiUpload, FiDownload,
  FiCheckCircle, FiShield, FiBookOpen, FiEdit3,
  FiCopy,
} from "react-icons/fi";
import Sidebar from "@/components/Sidebar";
import ChatWidget from "@/components/ChatWidget";
import Link from "next/link";
import api from "@/lib/api";

interface AppealData {
  appeal_text: string;
  regulations_cited: string[];
  confidence_score: number;
  appeal_strength: string;
  word_count: number;
  patient_name: string;
  insurer_name: string;
  denial_reason: string;
  claim_amount: number;
  generated_date: string;
}

interface PipelineResult {
  claim_summary: {
    patient_name: string;
    insurer_name: string;
    claim_amount: number;
    denial_reason: string;
  };
  overall_assessment: {
    appeal_strength: string;
    irdai_violations_count: number;
    policy_alignment_score: number;
    medical_necessity_score: number;
  };
  agents: {
    policy_agent?: {
      output?: {
        insurer_violations?: string[];
      };
    };
    medical_agent?: {
      output?: {
        medical_necessity_summary?: string;
      };
    };
  };
}

export default function AppealPage() {
  const toast = useToast();
  const [pipelineResult, setPipelineResult] = useState<PipelineResult | null>(null);
  const [appealData, setAppealData] = useState<AppealData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);

  // Checkbox confirmations before generation
  const [ackDocs, setAckDocs] = useState(false);
  const [ackReview, setAckReview] = useState(false);
  const [ackLegal, setAckLegal] = useState(false);

  const allChecked = ackDocs && ackReview && ackLegal;

  // Fetch latest pipeline result on mount
  useEffect(() => {
    const fetchPipelineResult = async () => {
      try {
        const res = await api.get("/api/pipeline/latest-result");
        if (res.data && res.data.status === "completed") {
          setPipelineResult(res.data);
        }
      } catch (err) {
        console.log("No pipeline result yet:", err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchPipelineResult();
  }, []);

  const handleGenerateAppeal = async () => {
    if (!pipelineResult || !allChecked) return;

    setIsGenerating(true);
    try {
      const cs = pipelineResult.claim_summary;
      const assessment = pipelineResult.overall_assessment;
      const violations = pipelineResult.agents?.policy_agent?.output?.insurer_violations || [];
      const medFindings = pipelineResult.agents?.medical_agent?.output?.medical_necessity_summary || "";

      const res = await api.post("/api/appeals/generate", {
        patient_name: cs.patient_name,
        insurer_name: cs.insurer_name,
        claim_amount: cs.claim_amount,
        denial_reason: cs.denial_reason,
        appeal_strength: assessment.appeal_strength,
        policy_violations: violations,
        medical_findings: medFindings,
        include_regulations: true,
        include_medical_evidence: true,
      });

      setAppealData(res.data);
      toast({
        title: "Appeal Letter Generated",
        description: `${res.data.word_count} words, ${res.data.appeal_strength} strength`,
        status: "success",
        duration: 4000,
        isClosable: true,
        position: "top",
      });
    } catch (err) {
      console.error("Appeal generation failed:", err);
      toast({
        title: "Generation Failed",
        description: "Could not generate the appeal letter. Please try again.",
        status: "error",
        duration: 4000,
        isClosable: true,
        position: "top",
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDownload = () => {
    if (!appealData) return;
    const blob = new Blob([appealData.appeal_text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `appeal_letter_${appealData.patient_name?.replace(/\s+/g, "_") || "draft"}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast({
      title: "Downloaded",
      description: "Appeal letter saved as text file.",
      status: "success",
      duration: 2000,
      isClosable: true,
      position: "top",
    });
  };

  const [isDownloadingPDF, setIsDownloadingPDF] = useState(false);

  const handleDownloadPDF = async () => {
    if (!appealData) return;
    setIsDownloadingPDF(true);
    try {
      const res = await api.post("/api/appeals/download-pdf", {
        appeal_text: appealData.appeal_text,
        patient_name: appealData.patient_name,
        insurer_name: appealData.insurer_name,
        claim_amount: appealData.claim_amount,
        denial_reason: appealData.denial_reason,
        appeal_strength: appealData.appeal_strength,
        confidence_score: appealData.confidence_score,
        regulations_cited: appealData.regulations_cited || [],
        word_count: appealData.word_count,
      }, { responseType: "blob" });

      const blob = new Blob([res.data], { type: "application/pdf" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `Appeal_Letter_${appealData.patient_name?.replace(/\s+/g, "_") || "draft"}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast({
        title: "PDF Downloaded",
        description: "Professional appeal letter PDF saved.",
        status: "success",
        duration: 3000,
        isClosable: true,
        position: "top",
      });
    } catch (err) {
      console.error("PDF download failed:", err);
      toast({
        title: "PDF Download Failed",
        description: "Could not generate PDF. Please try the text download.",
        status: "error",
        duration: 4000,
        isClosable: true,
        position: "top",
      });
    } finally {
      setIsDownloadingPDF(false);
    }
  };

  const handleCopy = async () => {
    if (!appealData) return;
    try {
      await navigator.clipboard.writeText(appealData.appeal_text);
      toast({
        title: "Copied",
        description: "Appeal letter copied to clipboard.",
        status: "success",
        duration: 2000,
        isClosable: true,
        position: "top",
      });
    } catch {
      toast({ title: "Copy failed", status: "error", duration: 2000, isClosable: true });
    }
  };

  return (
    <Flex minH="100vh" bg="bg.page">
      <Sidebar />
      <Box ml="260px" flex={1} p={8} maxW="calc(100vw - 260px)">
        <Flex justify="space-between" align="center" mb={6}>
          <Box>
            <Text fontSize="2xl" fontWeight="800" color="text.primary">Generate Appeal</Text>
            <Text color="text.muted" fontSize="sm">
              AI-generated appeal letters based on your claim analysis
            </Text>
          </Box>
          {appealData && (
            <HStack spacing={3}>
              <Button
                size="sm"
                leftIcon={<FiCopy />}
                variant="outline"
                onClick={handleCopy}
                borderRadius="xl"
              >
                Copy
              </Button>
              <Button
                size="sm"
                leftIcon={<FiDownload />}
                variant="outline"
                onClick={handleDownload}
                borderRadius="xl"
              >
                .TXT
              </Button>
              <Button
                size="sm"
                leftIcon={<FiDownload />}
                bg="linear-gradient(135deg, #5A67D8 0%, #667EEA 100%)"
                color="white"
                borderRadius="xl"
                onClick={handleDownloadPDF}
                isLoading={isDownloadingPDF}
                loadingText="Generating..."
                _hover={{ transform: "translateY(-1px)", boxShadow: "0 6px 20px rgba(90, 103, 216, 0.3)" }}
                transition="all 0.25s ease"
              >
                Download PDF
              </Button>
            </HStack>
          )}
        </Flex>

        {/* Loading */}
        {isLoading && (
          <Flex justify="center" py={20}>
            <Spinner size="xl" color="brand.500" />
          </Flex>
        )}

        {/* No Pipeline Result */}
        {!isLoading && !pipelineResult && (
          <Box
            bg="bg.card"
            borderRadius="2xl"
            border="1px solid"
            borderColor="border.card"
            className="animate-fade-in"
          >
            <VStack spacing={5} py={16} px={8}>
              <Flex w="96px" h="96px" borderRadius="full" bg="green.50" _dark={{ bg: "green.900" }} align="center" justify="center">
                <Icon as={FiFileText} boxSize={10} color="green.300" />
              </Flex>
              <VStack spacing={2}>
                <Text fontWeight="700" fontSize="lg" color="text.primary">
                  No appeal letter generated yet
                </Text>
                <Text fontSize="sm" color="text.muted" textAlign="center" maxW="520px" lineHeight="1.7">
                  To generate an appeal letter, you need to first upload your documents and run
                  the claim analysis pipeline. The AI will then create a detailed, regulation-backed
                  appeal letter with citations and IRDAI references.
                </Text>
              </VStack>
              <Link href="/upload" style={{ textDecoration: "none" }}>
                <Button variant="primary" size="lg" rightIcon={<FiArrowRight />} leftIcon={<FiUpload />} mt={3}>
                  Upload Documents First
                </Button>
              </Link>
            </VStack>
          </Box>
        )}

        {/* Pipeline Result Available — Pre-generation */}
        {!isLoading && pipelineResult && !appealData && (
          <VStack spacing={6} align="stretch" className="animate-fade-in">
            {/* Claim Summary Card */}
            <Box
              bg="linear-gradient(135deg, #1A1A2E 0%, #3C366B 35%, #5A67D8 100%)"
              borderRadius="2xl"
              p={6}
              color="white"
            >
              <Text fontWeight="700" fontSize="lg" mb={3}>
                Claim Summary — Ready for Appeal
              </Text>
              <HStack spacing={8} flexWrap="wrap">
                <VStack align="start" spacing={0}>
                  <Text fontSize="xs" color="whiteAlpha.600">Patient</Text>
                  <Text fontWeight="600" fontSize="sm">{pipelineResult.claim_summary.patient_name}</Text>
                </VStack>
                <VStack align="start" spacing={0}>
                  <Text fontSize="xs" color="whiteAlpha.600">Insurer</Text>
                  <Text fontWeight="600" fontSize="sm">{pipelineResult.claim_summary.insurer_name}</Text>
                </VStack>
                <VStack align="start" spacing={0}>
                  <Text fontSize="xs" color="whiteAlpha.600">Amount</Text>
                  <Text fontWeight="600" fontSize="sm">₹{pipelineResult.claim_summary.claim_amount?.toLocaleString()}</Text>
                </VStack>
                <VStack align="start" spacing={0}>
                  <Text fontSize="xs" color="whiteAlpha.600">Denial</Text>
                  <Text fontWeight="600" fontSize="sm">{pipelineResult.claim_summary.denial_reason}</Text>
                </VStack>
                <Badge
                  colorScheme={
                    pipelineResult.overall_assessment.appeal_strength === "strong" ? "green"
                    : pipelineResult.overall_assessment.appeal_strength === "moderate" ? "yellow"
                    : "red"
                  }
                  variant="solid"
                  borderRadius="full"
                  px={4}
                  py={1}
                  fontSize="sm"
                  fontWeight="800"
                >
                  {pipelineResult.overall_assessment.appeal_strength?.toUpperCase()} APPEAL
                </Badge>
              </HStack>
            </Box>

            {/* Checkbox Confirmations */}
            <Box
              bg="bg.card"
              borderRadius="2xl"
              border="1px solid"
              borderColor="border.card"
              p={6}
            >
              <HStack spacing={2} mb={4}>
                <Icon as={FiShield} color="brand.500" boxSize={5} />
                <Text fontWeight="700" fontSize="lg" color="text.primary">
                  Confirm Before Generating
                </Text>
              </HStack>
              <Text fontSize="sm" color="text.muted" mb={5}>
                Please verify the following before generating the appeal letter:
              </Text>

              <VStack align="start" spacing={4}>
                <Checkbox
                  isChecked={ackDocs}
                  onChange={(e) => setAckDocs(e.target.checked)}
                  colorScheme="brand"
                  size="lg"
                >
                  <VStack align="start" spacing={0} ml={1}>
                    <Text fontSize="sm" fontWeight="600" color="text.primary">
                      Document Verification
                    </Text>
                    <Text fontSize="xs" color="text.muted">
                      I confirm that all uploaded documents (policy, medical records, denial letter) are genuine and accurate
                    </Text>
                  </VStack>
                </Checkbox>

                <Checkbox
                  isChecked={ackReview}
                  onChange={(e) => setAckReview(e.target.checked)}
                  colorScheme="brand"
                  size="lg"
                >
                  <VStack align="start" spacing={0} ml={1}>
                    <Text fontSize="sm" fontWeight="600" color="text.primary">
                      Pipeline Review
                    </Text>
                    <Text fontSize="xs" color="text.muted">
                      I have reviewed the pipeline analysis results and the claim details are correct
                    </Text>
                  </VStack>
                </Checkbox>

                <Checkbox
                  isChecked={ackLegal}
                  onChange={(e) => setAckLegal(e.target.checked)}
                  colorScheme="brand"
                  size="lg"
                >
                  <VStack align="start" spacing={0} ml={1}>
                    <Text fontSize="sm" fontWeight="600" color="text.primary">
                      Legal Disclaimer
                    </Text>
                    <Text fontSize="xs" color="text.muted">
                      I understand this is an AI-generated appeal and I will review it for accuracy before sending
                    </Text>
                  </VStack>
                </Checkbox>
              </VStack>

              <Flex justify="center" mt={6}>
                <Button
                  size="lg"
                  bg={allChecked ? "linear-gradient(135deg, #5A67D8 0%, #667EEA 100%)" : "gray.200"}
                  color={allChecked ? "white" : "gray.500"}
                  fontWeight="700"
                  borderRadius="xl"
                  leftIcon={<FiEdit3 />}
                  onClick={handleGenerateAppeal}
                  isDisabled={!allChecked}
                  isLoading={isGenerating}
                  loadingText="Generating Appeal..."
                  px={10}
                  _hover={allChecked ? { transform: "translateY(-2px)", boxShadow: "0 8px 25px rgba(90, 103, 216, 0.35)" } : {}}
                  transition="all 0.25s ease"
                >
                  Generate Appeal Letter
                </Button>
              </Flex>
            </Box>
          </VStack>
        )}

        {/* Generated Appeal Letter */}
        {appealData && (
          <VStack spacing={6} align="stretch" className="animate-fade-in">
            {/* Stats Bar */}
            <HStack spacing={4} flexWrap="wrap">
              <Badge colorScheme="green" variant="subtle" borderRadius="full" px={4} py={2} fontSize="sm">
                <Icon as={FiCheckCircle} mr={1} /> Generated Successfully
              </Badge>
              <Badge colorScheme="brand" variant="subtle" borderRadius="full" px={4} py={2} fontSize="sm">
                {appealData.word_count} words
              </Badge>
              <Badge
                colorScheme={appealData.appeal_strength === "strong" ? "green" : appealData.appeal_strength === "moderate" ? "yellow" : "red"}
                variant="subtle"
                borderRadius="full"
                px={4}
                py={2}
                fontSize="sm"
              >
                {appealData.appeal_strength?.toUpperCase()} Appeal
              </Badge>
              <Badge colorScheme="purple" variant="subtle" borderRadius="full" px={4} py={2} fontSize="sm">
                Confidence: {appealData.confidence_score}%
              </Badge>
            </HStack>

            {/* Appeal Letter Content */}
            <Box
              bg="bg.card"
              borderRadius="2xl"
              border="1px solid"
              borderColor="border.card"
              p={8}
            >
              <Text
                fontFamily="'Georgia', serif"
                fontSize="sm"
                lineHeight="2"
                whiteSpace="pre-wrap"
                color="text.primary"
              >
                {appealData.appeal_text}
              </Text>
            </Box>

            {/* Regulations Cited */}
            {appealData.regulations_cited && appealData.regulations_cited.length > 0 && (
              <Box
                bg="bg.card"
                borderRadius="2xl"
                border="1px solid"
                borderColor="border.card"
                p={6}
              >
                <HStack spacing={2} mb={3}>
                  <Icon as={FiBookOpen} color="blue.500" boxSize={5} />
                  <Text fontWeight="700" fontSize="md" color="text.primary">
                    Regulations Cited ({appealData.regulations_cited.length})
                  </Text>
                </HStack>
                <VStack align="start" spacing={2}>
                  {appealData.regulations_cited.map((reg: string, i: number) => (
                    <HStack key={i} spacing={2}>
                      <Box w="5px" h="5px" borderRadius="full" bg="blue.400" flexShrink={0} />
                      <Text fontSize="sm" color="text.secondary">{reg}</Text>
                    </HStack>
                  ))}
                </VStack>
              </Box>
            )}
          </VStack>
        )}
      </Box>
      <ChatWidget />
    </Flex>
  );
}
