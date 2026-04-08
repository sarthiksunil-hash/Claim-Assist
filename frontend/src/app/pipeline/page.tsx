"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Box,
  Flex,
  Text,
  VStack,
  HStack,
  Badge,
  Icon,
  Button,
  Spinner,
  Table,
  Tbody,
  Tr,
  Td,
  TableContainer,
  useToast,
  Grid,
  GridItem,
  Divider,
  Input,
  FormControl,
  FormLabel,
  Collapse,
} from "@chakra-ui/react";
import {
  FiCpu,
  FiZap,
  FiShield,
  FiHeart,
  FiPlay,
  FiCheckCircle,
  FiAlertTriangle,
  FiChevronDown,
  FiChevronUp,
  FiActivity,
} from "react-icons/fi";
import Sidebar from "@/components/Sidebar";
import ChatWidget from "@/components/ChatWidget";
import { runPipeline, getExtractedDetails } from "@/lib/api";

/* ─── Types ────────────────────────────────────────── */
interface AgentResult {
  agent_id: string;
  agent_name: string;
  status: string;
  timestamp: string;
  processing_time: string;
  irdai_verified?: boolean;
  kb_verified?: boolean;
  output: Record<string, unknown>;
}

interface PipelineResponse {
  claim_id: string;
  status: string;
  total_processing_time: string;
  agents: {
    ocr_agent: Record<string, AgentResult>;
    nlp_agent: AgentResult;
    policy_agent: AgentResult;
    medical_agent: AgentResult;
  };
  overall_assessment: {
    appeal_strength: string | Record<string,unknown>;
    policy_alignment_score: number;
    medical_necessity_score: number;
    irdai_violations_count: number;
    irdai_verified: boolean;
    medical_kb_verified: boolean;
  };
}

/* ─── Compact Row ──────────────────────────────────── */
function InfoRow({ label, value, highlight }: {
  label: string;
  value: string | number | boolean | null | undefined;
  highlight?: "good" | "warn" | "bad" | "neutral";
}) {
  const colors = {
    good: "green.400",
    warn: "orange.400",
    bad: "red.400",
    neutral: "text.secondary",
  };
  const displayVal =
    value === null || value === undefined ? "—"
    : typeof value === "boolean" ? (value ? "Yes ✓" : "No ✗")
    : String(value);

  return (
    <Tr>
      <Td py={2} px={3} fontSize="xs" fontWeight="600" color="text.muted" w="45%">
        {label}
      </Td>
      <Td py={2} px={3} fontSize="xs" fontWeight="600"
        color={highlight ? colors[highlight] : "text.primary"}>
        {displayVal}
      </Td>
    </Tr>
  );
}

/* ─── Agent Card ───────────────────────────────────── */
function AgentCard({ agentId, result, step, icon, color, label }: {
  agentId: string;
  result: AgentResult | null;
  step: number;
  icon: React.ElementType;
  color: string;
  label: string;
}) {
  const [open, setOpen] = useState(true);

  const statusColor = !result ? "gray" : result.status === "completed" ? "green" : "red";
  const verified = result?.irdai_verified || result?.kb_verified;

  // Extract compact summary rows per agent type
  const rows: Array<{ label: string; value: unknown; highlight?: "good" | "warn" | "bad" | "neutral" }> = [];

  if (result?.output) {
    const o = result.output;

    if (agentId === "ocr_agent") {
      const textLen = String(o.extracted_text || "").length;
      const kv = (o.key_value_pairs || {}) as Record<string, string>;
      rows.push({ label: "Text Extracted", value: textLen > 50 ? `${textLen} characters` : "None", highlight: textLen > 50 ? "good" : "warn" });
      rows.push({ label: "Patient Name", value: kv["Patient Name"] || kv["Policyholder"] || "—" });
      rows.push({ label: "Policy No.", value: kv["Policy Number"] || "—" });
      rows.push({ label: "Hospital", value: kv["Hospital"] || "—" });
      rows.push({ label: "Claim/Bill Amount", value: kv["Bill Amount"] || kv["Claim Amount"] || "—" });
      rows.push({ label: "Diagnosis", value: kv["Diagnosis"] || "—" });
    }

    if (agentId === "nlp_agent") {
      const ents = (o.entities || {}) as Record<string, unknown[]>;
      const sent = (o.sentiment_analysis || {}) as Record<string, unknown>;
      const denial = (o.denial_classification || {}) as Record<string, unknown>;
      const summary = (o.summary || {}) as Record<string, unknown>;
      rows.push({ label: "Denial Category", value: String(summary.denial_category || denial.category || "—").replace(/_/g, " ").toUpperCase(), highlight: "warn" });
      rows.push({ label: "Confidence", value: typeof denial.confidence === "number" ? `${Math.round(Number(denial.confidence) * 100)}%` : "—" });
      rows.push({ label: "Sentiment", value: String(sent.overall_sentiment || "—"), highlight: sent.overall_sentiment === "negative" ? "bad" : "neutral" });
      rows.push({ label: "Conditions Found", value: Array.isArray(ents.medical_conditions) ? ents.medical_conditions.map((c: unknown) => (c as Record<string,string>).name).join(", ") || "None" : "—" });
      rows.push({ label: "Medications", value: Array.isArray(ents.medications) ? ents.medications.map((m: unknown) => (m as Record<string,string>).name).join(", ") || "None" : "—" });
      rows.push({ label: "Appeal Window", value: String(sent.appeal_window_mentioned || false), highlight: sent.appeal_window_mentioned ? "good" : "neutral" });
    }

    if (agentId === "policy_agent") {
      const out = o as Record<string, unknown>;
      const violations = Array.isArray(out.insurer_violations) ? out.insurer_violations as Record<string,string>[] : [];
      const compliance = Array.isArray(out.insurer_compliance_issues) ? out.insurer_compliance_issues as Record<string,string>[] : [];
      rows.push({ label: "Policy Alignment Score", value: typeof out.policy_alignment_score === "number" ? `${Math.round(Number(out.policy_alignment_score))}%` : "—", highlight: Number(out.policy_alignment_score) >= 70 ? "good" : Number(out.policy_alignment_score) >= 50 ? "warn" : "bad" });
      rows.push({ label: "IRDAI Violations Found", value: violations.length, highlight: violations.length > 0 ? "warn" : "good" });
      if (violations.length > 0) {
        rows.push({ label: "Violation Summary", value: violations.slice(0,2).map((v) => v.violation || v.description || JSON.stringify(v)).join(" | "), highlight: "bad" });
      }
      rows.push({ label: "Compliance Issues", value: compliance.length > 0 ? compliance.slice(0,2).map((c) => c.issue || JSON.stringify(c)).join("; ") : "None", highlight: compliance.length > 0 ? "warn" : "good" });
      rows.push({ label: "IRDAI Verified", value: Boolean(out.irdai_regulations_checked), highlight: out.irdai_regulations_checked ? "good" : "warn" });
    }

    if (agentId === "medical_agent") {
      const out = o as Record<string, unknown>;
      rows.push({ label: "Medical Necessity Score", value: typeof out.medical_necessity_score === "number" ? `${Math.round(Number(out.medical_necessity_score))}%` : "—", highlight: Number(out.medical_necessity_score) >= 70 ? "good" : "warn" });
      rows.push({ label: "Necessity Confirmed", value: Boolean(out.medical_necessity_confirmed), highlight: out.medical_necessity_confirmed ? "good" : "bad" });
      rows.push({ label: "ICD-10 Codes", value: Array.isArray(out.icd10_codes) ? (out.icd10_codes as string[]).join(", ") || "None" : "—" });
      rows.push({ label: "Treatment Appropriate", value: Boolean(out.treatment_appropriate), highlight: out.treatment_appropriate ? "good" : "warn" });
      rows.push({ label: "Recommendation", value: String(out.recommendation || "—") });
    }
  }

  return (
    <Box
      bg="bg.card"
      borderRadius="2xl"
      border="2px solid"
      borderColor={result ? `${color}.200` : "border.card"}
      _dark={{ borderColor: result ? `${color}.700` : "gray.700" }}
      overflow="hidden"
      opacity={result ? 1 : 0.5}
      transition="all 0.3s"
    >
      {/* Header */}
      <Flex
        px={4} py={3}
        bg={result ? `${color}.50` : "bg.hover"}
        _dark={{ bg: result ? `${color}.900` : "bg.hover" }}
        align="center"
        justify="space-between"
        cursor="pointer"
        onClick={() => result && setOpen((v) => !v)}
      >
        <HStack spacing={3}>
          <Flex
            w="32px" h="32px" borderRadius="lg"
            bg={`${color}.100`} _dark={{ bg: `${color}.800` }} align="center" justify="center"
          >
            <Icon as={icon} boxSize={4} color={`${color}.500`} />
          </Flex>
          <Box>
            <HStack spacing={2}>
              <Badge colorScheme="gray" fontSize="9px" borderRadius="full" px={2}>
                Step {step}
              </Badge>
              <Text fontWeight="700" fontSize="sm" color="text.primary">{label}</Text>
              {verified && (
                <Badge colorScheme="green" variant="subtle" fontSize="9px" borderRadius="full">
                  ✓ KB Verified
                </Badge>
              )}
            </HStack>
            {result && (
              <Text fontSize="10px" color="text.muted" mt={0.5}>
                {result.processing_time} · {result.timestamp?.slice(0, 16).replace("T", " ")}
              </Text>
            )}
          </Box>
        </HStack>
        <HStack spacing={2}>
          <Badge colorScheme={statusColor} variant="subtle" borderRadius="full" fontSize="10px">
            {result ? result.status : "Pending"}
          </Badge>
          {result && (
            <Icon as={open ? FiChevronUp : FiChevronDown} color="text.dimmed" boxSize={4} />
          )}
        </HStack>
      </Flex>

      {/* Compact Verification Table */}
      <Collapse in={open && !!result}>
        {rows.length > 0 ? (
          <TableContainer>
            <Table size="sm" variant="simple">
              <Tbody>
                {rows.map((r, i) => (
                  <InfoRow key={i} label={r.label} value={r.value as string | number | boolean | null | undefined} highlight={r.highlight} />
                ))}
              </Tbody>
            </Table>
          </TableContainer>
        ) : (
          <Box px={4} py={3}>
            <Text fontSize="xs" color="text.dimmed">No output data available.</Text>
          </Box>
        )}
      </Collapse>
    </Box>
  );
}

/* ─── Main Component ───────────────────────────────── */
export default function PipelinePage() {
  const toast = useToast();
  const [pipelineData, setPipelineData] = useState<PipelineResponse | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  // Form fields
  const [patientName, setPatientName] = useState("");
  const [insurerName, setInsurerName] = useState("");
  const [claimAmount, setClaimAmount] = useState("");
  const [denialReason, setDenialReason] = useState("");

  const [isLoadingDetails, setIsLoadingDetails] = useState(true);
  const [autoFilledFields, setAutoFilledFields] = useState<Record<string, string>>({});
  const [docsCount, setDocsCount] = useState(0);
  const [extraDetails, setExtraDetails] = useState<Record<string, string>>({});

  // Load extracted details from uploaded documents on mount
  useEffect(() => {
    const fetchDetails = async () => {
      try {
        const response = await getExtractedDetails();
        const data = response.data;
        setDocsCount(data.documents_count || 0);
        const sources: Record<string, string> = data.extraction_sources || {};

        if (data.patient_name) {
          setPatientName(data.patient_name);
          setAutoFilledFields((prev) => ({ ...prev, patient_name: sources.patient_name || "document" }));
        }
        if (data.insurer_name) {
          setInsurerName(data.insurer_name);
          setAutoFilledFields((prev) => ({ ...prev, insurer_name: sources.insurer_name || "document" }));
        }
        if (data.claim_amount) {
          setClaimAmount(data.claim_amount);
          setAutoFilledFields((prev) => ({ ...prev, claim_amount: sources.claim_amount || "document" }));
        }
        if (data.denial_reason) {
          setDenialReason(data.denial_reason);
          setAutoFilledFields((prev) => ({ ...prev, denial_reason: sources.denial_reason || "document" }));
        }

        const extras: Record<string, string> = {};
        if (data.policy_number) extras["Policy No."] = data.policy_number;
        if (data.hospital) extras["Hospital"] = data.hospital;
        if (data.diagnosis) extras["Diagnosis"] = data.diagnosis;
        setExtraDetails(extras);
      } catch (err) {
        console.log("Could not load document info:", err);
      } finally {
        setIsLoadingDetails(false);
      }
    };
    fetchDetails();
  }, []);

  const handleRunPipeline = useCallback(async () => {
    if (!patientName.trim() || !insurerName.trim() || !claimAmount || !denialReason.trim()) {
      toast({
        title: "Missing Information",
        description: "Please fill in all claim details before running the analysis.",
        status: "warning",
        duration: 3000,
        isClosable: true,
        position: "top",
      });
      return;
    }
    setIsRunning(true);
    setPipelineData(null);
    try {
      const response = await runPipeline({
        patient_name: patientName,
        insurer_name: insurerName,
        claim_amount: parseFloat(claimAmount),
        denial_reason: denialReason,
      });
      setPipelineData(response.data);
      toast({
        title: "Analysis Complete ✓",
        description: "All agents finished. Review the extracted data below.",
        status: "success",
        duration: 3000,
        isClosable: true,
        position: "top",
      });
    } catch {
      toast({
        title: "Pipeline Error",
        description: "Failed to run claim analysis. Please try again.",
        status: "error",
        duration: 4000,
        isClosable: true,
        position: "top",
      });
    } finally {
      setIsRunning(false);
    }
  }, [toast, patientName, insurerName, claimAmount, denialReason]);

  const getAgentResult = (agentId: string): AgentResult | null => {
    if (!pipelineData) return null;
    const agents = pipelineData.agents;
    if (agentId === "ocr_agent") {
      const ocrAgents = agents.ocr_agent;
      const firstKey = Object.keys(ocrAgents)[0];
      return firstKey ? ocrAgents[firstKey] : null;
    }
    const agentData = agents[agentId as keyof typeof agents];
    if (!agentData || typeof agentData !== "object" || !("agent_id" in agentData)) return null;
    return agentData as AgentResult;
  };

  const assessment = pipelineData?.overall_assessment;
  const appealStrengthStr =
    !assessment ? "—"
    : typeof assessment.appeal_strength === "string"
      ? assessment.appeal_strength
      : (assessment.appeal_strength as Record<string, unknown>)?.strength?.toString()
        || (assessment.appeal_strength as Record<string, unknown>)?.level?.toString()
        || "—";

  const strengthColor =
    appealStrengthStr === "strong" ? "green"
    : appealStrengthStr === "moderate" ? "orange"
    : "red";

  return (
    <Flex minH="100vh" bg="bg.page">
      <Sidebar />

      <Box ml="260px" flex={1} p={8} maxW="calc(100vw - 260px)">
        {/* Header */}
        <Flex justify="space-between" align="center" mb={6}>
          <Box>
            <Text fontSize="2xl" fontWeight="800" color="text.primary">
              Claim Data Extraction
            </Text>
            <Text color="text.muted" fontSize="sm">
              Verify extracted data from uploaded documents before generating appeal
            </Text>
          </Box>
          <Button
            size="md"
            bg="linear-gradient(135deg, #5A67D8 0%, #667EEA 100%)"
            color="white"
            fontWeight="700"
            borderRadius="xl"
            leftIcon={<FiPlay />}
            onClick={handleRunPipeline}
            isLoading={isRunning}
            loadingText="Analysing..."
            _hover={{ transform: "translateY(-2px)", boxShadow: "0 8px 25px rgba(90, 103, 216, 0.35)" }}
            transition="all 0.25s ease"
          >
            Run Analysis
          </Button>
        </Flex>

        {/* Claim Details Input */}
        <Box bg="bg.card" borderRadius="2xl" border="1px solid" borderColor="border.card" p={6} mb={6}>
          {/* Banners */}
          {Object.keys(autoFilledFields).length > 0 && (
            <Box bg="green.50" borderRadius="xl" border="1px solid" borderColor="green.200" px={4} py={2.5} mb={4} _dark={{ bg: "green.900", borderColor: "green.700" }}>
              <HStack spacing={3}>
                <Icon as={FiCheckCircle} color="green.500" boxSize={4} />
                <Text fontWeight="700" fontSize="sm" color="green.800" _dark={{ color: "green.200" }}>
                  {Object.keys(autoFilledFields).length} field(s) auto-filled from your {docsCount} uploaded document(s) — review and correct if needed
                </Text>
              </HStack>
            </Box>
          )}
          {docsCount === 0 && !isLoadingDetails && (
            <Box bg="orange.50" borderRadius="xl" border="1px solid" borderColor="orange.200" px={4} py={2.5} mb={4} _dark={{ bg: "orange.900", borderColor: "orange.700" }}>
              <HStack spacing={3}>
                <Icon as={FiAlertTriangle} color="orange.500" boxSize={4} />
                <Text fontWeight="700" fontSize="sm" color="orange.800" _dark={{ color: "orange.200" }}>
                  No documents found — upload your policy/medical/denial documents first, then come back here.
                </Text>
              </HStack>
            </Box>
          )}

          <Text fontWeight="700" fontSize="md" color="text.primary" mb={3}>
            Claim Details {isLoadingDetails && <Spinner size="xs" color="brand.400" ml={2} />}
          </Text>

          <Grid templateColumns="repeat(2, 1fr)" gap={4} mb={4}>
            {[
              { key: "patient_name", label: "Policyholder Name", value: patientName, setter: setPatientName, placeholder: "Full name of policyholder" },
              { key: "insurer_name", label: "Insurance Company", value: insurerName, setter: setInsurerName, placeholder: "e.g. Star Health Insurance" },
              { key: "claim_amount", label: "Claim Amount (₹)", value: claimAmount, setter: setClaimAmount, placeholder: "e.g. 285000" },
              { key: "denial_reason", label: "Denial Reason", value: denialReason, setter: setDenialReason, placeholder: "Reason stated in denial letter" },
            ].map(({ key, label, value, setter, placeholder }) => (
              <GridItem key={key}>
                <FormControl>
                  <HStack mb={1}>
                    <FormLabel fontSize="sm" fontWeight="600" color="text.primary" mb={0}>{label}</FormLabel>
                    {autoFilledFields[key] && (
                      <Badge colorScheme="green" variant="subtle" borderRadius="full" fontSize="9px" px={2}>
                        ✓ AUTO-FILLED FROM {autoFilledFields[key].toUpperCase()}
                      </Badge>
                    )}
                  </HStack>
                  <Input
                    placeholder={placeholder}
                    value={value}
                    onChange={(e) => setter(e.target.value)}
                    type={key === "claim_amount" ? "number" : "text"}
                    borderRadius="xl"
                    bg={autoFilledFields[key] ? "green.50" : "bg.input"}
                    _dark={{ bg: autoFilledFields[key] ? "green.900" : "#1E1F33" }}
                    border="2px solid"
                    borderColor={autoFilledFields[key] ? "green.200" : "transparent"}
                    _focus={{ bg: "bg.card", borderColor: "brand.400" }}
                    fontSize="sm"
                    fontWeight={autoFilledFields[key] ? "600" : "400"}
                  />
                </FormControl>
              </GridItem>
            ))}
          </Grid>

          {/* Extra extracted info chips */}
          {Object.keys(extraDetails).length > 0 && (
            <HStack spacing={4} flexWrap="wrap" bg="bg.hover" borderRadius="xl" px={4} py={2.5}>
              {Object.entries(extraDetails).map(([key, val]) => (
                <HStack key={key} spacing={1.5}>
                  <Text fontSize="xs" color="text.muted" fontWeight="600">{key}:</Text>
                  <Text fontSize="xs" color="text.primary" fontWeight="500">{val}</Text>
                </HStack>
              ))}
            </HStack>
          )}

          <Flex justify="center" mt={4}>
            <Button
              size="lg"
              bg="linear-gradient(135deg, #5A67D8 0%, #667EEA 100%)"
              color="white"
              fontWeight="700"
              borderRadius="xl"
              leftIcon={isRunning ? <Spinner size="sm" /> : <FiPlay />}
              onClick={handleRunPipeline}
              isLoading={isRunning}
              loadingText="Analysing claim..."
              _hover={{ transform: "translateY(-2px)", boxShadow: "0 8px 25px rgba(90, 103, 216, 0.35)" }}
              transition="all 0.25s ease"
              px={10}
            >
              Run Analysis
            </Button>
          </Flex>
        </Box>

        {/* Overall Assessment Banner */}
        {assessment && (
          <Box
            bg={`${strengthColor}.50`}
            _dark={{ bg: `${strengthColor}.900`, borderColor: `${strengthColor}.700` }}
            borderRadius="2xl"
            border="2px solid"
            borderColor={`${strengthColor}.200`}
            p={5}
            mb={6}
          >
            <Flex justify="space-between" align="center" flexWrap="wrap" gap={4}>
              <VStack align="start" spacing={1}>
                <HStack>
                  <Icon as={FiActivity} color={`${strengthColor}.500`} boxSize={5} />
                  <Text fontWeight="800" fontSize="lg" color={`${strengthColor}.700`} _dark={{ color: `${strengthColor}.200` }}>
                    Appeal Strength: {appealStrengthStr.toUpperCase()}
                  </Text>
                </HStack>
                <Text fontSize="sm" color="text.secondary">
                  {assessment.irdai_violations_count} IRDAI violation(s) found ·{" "}
                  {assessment.irdai_verified ? "IRDAI verified ✓" : "IRDAI check pending"}
                </Text>
              </VStack>
              <HStack spacing={6}>
                <VStack spacing={0} align="center">
                  <Text fontSize="xs" color="text.muted" fontWeight="600">POLICY ALIGNMENT</Text>
                  <Text fontSize="xl" fontWeight="800" color={Number(assessment.policy_alignment_score) >= 70 ? "green.400" : "orange.400"}>
                    {assessment.policy_alignment_score ? `${Math.round(Number(assessment.policy_alignment_score))}%` : "—"}
                  </Text>
                </VStack>
                <Divider orientation="vertical" h="40px" />
                <VStack spacing={0} align="center">
                  <Text fontSize="xs" color="text.muted" fontWeight="600">MEDICAL NECESSITY</Text>
                  <Text fontSize="xl" fontWeight="800" color={Number(assessment.medical_necessity_score) >= 70 ? "green.400" : "orange.400"}>
                    {assessment.medical_necessity_score ? `${Math.round(Number(assessment.medical_necessity_score))}%` : "—"}
                  </Text>
                </VStack>
              </HStack>
            </Flex>
          </Box>
        )}

        {/* Agent Verification Cards */}
        <Text fontWeight="700" fontSize="md" color="text.primary" mb={3}>
          {pipelineData ? "Extracted Data — Verify Each Section" : "Agent Steps"}
        </Text>
        <VStack spacing={3} align="stretch">
          {[
            { id: "ocr_agent",     icon: FiCpu,    color: "purple", label: "Step 1 · Document Data Extraction (OCR)",   step: 1 },
            { id: "nlp_agent",     icon: FiZap,    color: "orange", label: "Step 2 · NLP — Denial Classification & Entities", step: 2 },
            { id: "policy_agent",  icon: FiShield, color: "blue",   label: "Step 3 · IRDAI Policy Compliance Check",    step: 3 },
            { id: "medical_agent", icon: FiHeart,  color: "green",  label: "Step 4 · Medical Necessity Verification",   step: 4 },
          ].map(({ id, icon, color, label, step }) => (
            <AgentCard
              key={id}
              agentId={id}
              result={getAgentResult(id)}
              step={step}
              icon={icon}
              color={color}
              label={label}
            />
          ))}
        </VStack>

        {/* Running Overlay */}
        {isRunning && (
          <Box mt={6} bg="bg.card" borderRadius="2xl" border="1px solid" borderColor="brand.200" p={6} textAlign="center">
            <Spinner size="xl" color="brand.500" thickness="4px" speed="0.65s" mb={4} />
            <Text fontWeight="700" color="text.primary">Running multi-agent analysis...</Text>
            <Text fontSize="sm" color="text.muted" mt={1}>OCR → NLP → IRDAI Policy → Medical KB</Text>
          </Box>
        )}
      </Box>

      <ChatWidget />
    </Flex>
  );
}
