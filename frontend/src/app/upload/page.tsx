"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Box,
  Flex,
  Text,
  Grid,
  GridItem,
  Icon,
  VStack,
  HStack,
  Button,
  Badge,
  Progress,
  Spinner,
  useToast,
} from "@chakra-ui/react";
import {
  FiUpload,
  FiFile,
  FiFileText,
  FiClipboard,
  FiDollarSign,
  FiCheck,
  FiX,
  FiArrowRight,
} from "react-icons/fi";
import Sidebar from "@/components/Sidebar";
import ChatWidget from "@/components/ChatWidget";
import { uploadDocument } from "@/lib/api";

const SESSION_DOCS_KEY = "claimassist_session_docs";

/** Read session-scoped uploaded doc info from sessionStorage */
function getSessionDocs(): Record<string, string> {
  try {
    const raw = sessionStorage.getItem(SESSION_DOCS_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

/** Save uploaded doc info (file_type → filename) to sessionStorage */
function saveSessionDoc(fileType: string, filename: string) {
  const docs = getSessionDocs();
  docs[fileType] = filename;
  sessionStorage.setItem(SESSION_DOCS_KEY, JSON.stringify(docs));
}

/** Remove a doc from session storage */
function removeSessionDoc(fileType: string) {
  const docs = getSessionDocs();
  delete docs[fileType];
  sessionStorage.setItem(SESSION_DOCS_KEY, JSON.stringify(docs));
}

interface UploadZone {
  id: string;
  label: string;
  description: string;
  icon: React.ElementType;
  accepted: string;
  color: string;
  file?: File;
  status: "idle" | "uploading" | "done" | "error";
  progress: number;
  existingFilename?: string; // from Supabase
}

const INITIAL_ZONES: Omit<UploadZone, "existingFilename">[] = [
  {
    id: "policy",
    label: "Policy Document",
    description: "Upload your insurance policy PDF",
    icon: FiFileText,
    accepted: ".pdf,.doc,.docx",
    color: "brand",
    status: "idle",
    progress: 0,
  },
  {
    id: "medical_report",
    label: "Medical Report",
    description: "Discharge summary or medical records",
    icon: FiClipboard,
    accepted: ".pdf,.jpg,.jpeg,.png",
    color: "green",
    status: "idle",
    progress: 0,
  },
  {
    id: "denial_letter",
    label: "Denial Letter",
    description: "Claim rejection letter from insurer/TPA",
    icon: FiX,
    accepted: ".pdf,.jpg,.jpeg,.png",
    color: "red",
    status: "idle",
    progress: 0,
  },
  {
    id: "medical_bill",
    label: "Medical Bill",
    description: "Hospital bills and payment receipts",
    icon: FiDollarSign,
    accepted: ".pdf,.jpg,.jpeg,.png",
    color: "orange",
    status: "idle",
    progress: 0,
  },
];

export default function UploadPage() {
  const toast = useToast();
  const router = useRouter();
  const [zones, setZones] = useState<UploadZone[]>(
    INITIAL_ZONES.map((z) => ({ ...z }))
  );
  const [dragOverId, setDragOverId] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isLoadingDocs, setIsLoadingDocs] = useState(true);

  // ── Restore uploads from sessionStorage (session-scoped) ──
  useEffect(() => {
    const sessionDocs = getSessionDocs();
    if (Object.keys(sessionDocs).length > 0) {
      setZones((prev) =>
        prev.map((zone) => {
          const filename = sessionDocs[zone.id];
          if (filename) {
            return {
              ...zone,
              status: "done" as const,
              progress: 100,
              existingFilename: filename,
            };
          }
          return zone;
        })
      );
    }
    setIsLoadingDocs(false);
  }, []);

  const handleDrop = (e: React.DragEvent, zoneId: string) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOverId(null);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelect(files[0], zoneId);
    }
  };

  const handleFileSelect = async (file: File, zoneId: string) => {
    setZones((prev) =>
      prev.map((z) =>
        z.id === zoneId
          ? { ...z, file, status: "uploading" as const, progress: 20, existingFilename: undefined }
          : z
      )
    );

    try {
      setZones((prev) =>
        prev.map((z) => (z.id === zoneId ? { ...z, progress: 50 } : z))
      );

      await uploadDocument(file, zoneId);

      // Save to sessionStorage so it persists during this session
      saveSessionDoc(zoneId, file.name);

      setZones((prev) =>
        prev.map((z) =>
          z.id === zoneId
            ? { ...z, status: "done" as const, progress: 100 }
            : z
        )
      );
      toast({
        title: "File uploaded successfully",
        description: `${file.name} has been uploaded and processed.`,
        status: "success",
        duration: 3000,
        isClosable: true,
        position: "top-right",
      });
    } catch (err) {
      console.error("Upload failed:", err);
      setZones((prev) =>
        prev.map((z) =>
          z.id === zoneId
            ? { ...z, status: "error" as const, progress: 0 }
            : z
        )
      );
      toast({
        title: "Upload failed",
        description: `Could not upload ${file.name}. Please try again.`,
        status: "error",
        duration: 4000,
        isClosable: true,
        position: "top-right",
      });
    }
  };

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement>,
    zoneId: string
  ) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileSelect(files[0], zoneId);
    }
  };

  const removeFile = (zoneId: string) => {
    removeSessionDoc(zoneId);
    setZones((prev) =>
      prev.map((z) =>
        z.id === zoneId
          ? { ...z, file: undefined, status: "idle" as const, progress: 0, existingFilename: undefined }
          : z
      )
    );
  };

  const uploadedCount = zones.filter((z) => z.status === "done").length;
  const allUploaded = uploadedCount >= 2;

  const handleStartAnalysis = async () => {
    setIsAnalyzing(true);
    toast({
      title: "Starting Analysis",
      description: "Redirecting to Claim Data Extraction...",
      status: "info",
      duration: 2000,
      isClosable: true,
      position: "top",
    });
    router.push("/pipeline");
  };

  // Display name: either the File object's name or the persisted filename from Supabase
  const getDisplayName = (zone: UploadZone): string | null => {
    if (zone.file) return zone.file.name;
    if (zone.existingFilename) return zone.existingFilename;
    return null;
  };

  const getDisplaySize = (zone: UploadZone): string | null => {
    if (zone.file) return `${(zone.file.size / 1024).toFixed(0)} KB`;
    if (zone.existingFilename) return "Saved";
    return null;
  };

  return (
    <Flex minH="100vh" bg="bg.page">
      <Sidebar />

      <Box ml="260px" flex={1} p={8} maxW="calc(100vw - 260px)">
        {/* Header */}
        <Flex justify="space-between" align="center" mb={2}>
          <Text fontSize="2xl" fontWeight="800" color="text.primary">
            Upload Documents
          </Text>
          <HStack spacing={3}>
            {isLoadingDocs && <Spinner size="sm" color="brand.400" />}
            <Badge
              colorScheme="brand"
              variant="subtle"
              borderRadius="full"
              px={4}
              py={1.5}
              fontSize="sm"
              fontWeight="600"
            >
              {uploadedCount} / {zones.length} uploaded
            </Badge>
          </HStack>
        </Flex>
        <Text color="text.muted" fontSize="sm" mb={6}>
          Upload your insurance documents to start the claim analysis pipeline.
          Minimum 2 documents required. Previously uploaded documents are
          automatically restored.
        </Text>

        {/* Upload Zones Grid */}
        <Grid templateColumns="repeat(2, 1fr)" gap={6} mb={6}>
          {zones.map((zone, index) => (
            <GridItem key={zone.id}>
              <Box
                borderRadius="2xl"
                border="2px dashed"
                borderColor={
                  zone.status === "error"
                    ? "red.400"
                    : dragOverId === zone.id
                    ? `${zone.color}.400`
                    : zone.status === "done"
                    ? `${zone.color}.300`
                    : "gray.200"
                }
                bg={
                  zone.status === "error"
                    ? "red.50"
                    : dragOverId === zone.id
                    ? `${zone.color}.50`
                    : zone.status === "done"
                    ? `${zone.color}.50`
                    : "white"
                }
                p={6}
                transition="all 0.3s ease"
                _hover={{
                  borderColor: `${zone.color}.300`,
                  bg: `${zone.color}.50`,
                  transform: "translateY(-2px)",
                }}
                onDragOver={(e) => {
                  e.preventDefault();
                  setDragOverId(zone.id);
                }}
                onDragLeave={() => setDragOverId(null)}
                onDrop={(e) => handleDrop(e, zone.id)}
                cursor="pointer"
                className="animate-fade-in-up"
                style={{ animationDelay: `${index * 100}ms` }}
                position="relative"
                overflow="hidden"
              >
                {zone.status === "uploading" && (
                  <Progress
                    value={zone.progress}
                    size="xs"
                    colorScheme="brand"
                    position="absolute"
                    top={0}
                    left={0}
                    right={0}
                    borderRadius="full"
                  />
                )}

                <VStack spacing={3} textAlign="center">
                  <Flex
                    w="56px"
                    h="56px"
                    borderRadius="xl"
                    bg={
                      zone.status === "done"
                        ? `${zone.color}.100`
                        : zone.status === "error"
                        ? "red.100"
                        : `${zone.color}.50`
                    }
                    align="center"
                    justify="center"
                  >
                    <Icon
                      as={zone.status === "done" ? FiCheck : zone.icon}
                      boxSize={6}
                      color={
                        zone.status === "done"
                          ? `${zone.color}.600`
                          : zone.status === "error"
                          ? "red.500"
                          : `${zone.color}.500`
                      }
                    />
                  </Flex>

                  <Text fontWeight="700" fontSize="md" color="text.primary">
                    {zone.label}
                  </Text>
                  <Text fontSize="sm" color="text.muted">
                    {zone.description}
                  </Text>

                  {getDisplayName(zone) ? (
                    <HStack
                      bg="bg.card"
                      px={4}
                      py={2}
                      borderRadius="lg"
                      border="1px solid"
                      borderColor="border.input"
                      spacing={3}
                    >
                      <Icon as={FiFile} color="text.muted" boxSize={4} />
                      <Text fontSize="sm" fontWeight="500" noOfLines={1} maxW="200px">
                        {getDisplayName(zone)}
                      </Text>
                      <Text fontSize="xs" color="text.dimmed">
                        {getDisplaySize(zone)}
                      </Text>
                      {(zone.status === "done" || zone.status === "error") && (
                        <Icon
                          as={FiX}
                          color="text.dimmed"
                          boxSize={4}
                          cursor="pointer"
                          _hover={{ color: "red.500" }}
                          onClick={(e) => {
                            e.stopPropagation();
                            removeFile(zone.id);
                          }}
                        />
                      )}
                    </HStack>
                  ) : (
                    <VStack spacing={1}>
                      <HStack spacing={2}>
                        <Icon as={FiUpload} color="text.dimmed" boxSize={4} />
                        <Text fontSize="sm" color="text.muted">
                          Drag & drop or{" "}
                          <Text
                            as="label"
                            color="brand.500"
                            fontWeight="600"
                            cursor="pointer"
                            _hover={{ textDecoration: "underline" }}
                            htmlFor={`file-${zone.id}`}
                          >
                            browse files
                          </Text>
                        </Text>
                      </HStack>
                      <Text fontSize="xs" color="text.dimmed">
                        Supported: {zone.accepted}
                      </Text>
                    </VStack>
                  )}

                  <input
                    id={`file-${zone.id}`}
                    type="file"
                    accept={zone.accepted}
                    style={{ display: "none" }}
                    onChange={(e) => handleInputChange(e, zone.id)}
                  />
                </VStack>
              </Box>
            </GridItem>
          ))}
        </Grid>

        {/* Start Analysis Button */}
        <Flex justify="center">
          <Button
            size="lg"
            variant="primary"
            rightIcon={<FiArrowRight />}
            isDisabled={!allUploaded || isAnalyzing}
            isLoading={isAnalyzing}
            loadingText="Starting Analysis..."
            onClick={handleStartAnalysis}
            px={10}
            py={6}
            fontSize="md"
            fontWeight="700"
            boxShadow={allUploaded ? "brand" : "none"}
            _hover={
              allUploaded
                ? {
                    transform: "translateY(-2px)",
                    boxShadow: "0 6px 25px rgba(90, 103, 216, 0.4)",
                  }
                : {}
            }
          >
            {allUploaded ? "Start Claim Analysis" : `Upload at least 2 documents (${uploadedCount}/2)`}
          </Button>
        </Flex>
      </Box>

      <ChatWidget />
    </Flex>
  );
}
