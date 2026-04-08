"use client";

import { useState } from "react";
import {
  Box, Flex, Text, VStack, HStack, Icon, Button,
  Badge, Grid, GridItem, Accordion, AccordionItem,
  AccordionButton, AccordionPanel, AccordionIcon,
  Input, Textarea, useToast, Link as ChakraLink,
} from "@chakra-ui/react";
import {
  FiHelpCircle, FiMail, FiBookOpen, FiMessageCircle,
  FiShield, FiFileText, FiExternalLink, FiSend, FiAlertCircle,
  FiClock, FiUsers, FiLifeBuoy,
} from "react-icons/fi";
import Sidebar from "@/components/Sidebar";
import ChatWidget from "@/components/ChatWidget";

const SUPPORT_EMAIL = "claimassist.support@gmail.com";

const faqData = [
  {
    question: "How do I upload my insurance documents?",
    answer: "Go to the 'Upload Documents' section from the sidebar. You can upload up to 4 types of documents: Policy Document, Medical Report, Denial Letter, and Medical Bill. Supported formats include PDF, JPG, JPEG, PNG, DOC, and DOCX. Simply drag and drop your files or click 'browse files' to select them.",
  },
  {
    question: "What is the Agent Pipeline and how does it work?",
    answer: "The Agent Pipeline is our multi-agent AI system that analyzes your claim through 4 specialized agents:\n\n1. OCR Agent — Extracts text from your documents\n2. NLP Agent — Analyzes entities, sentiment, and classifies the denial\n3. Policy Agent — Validates against IRDAI regulations\n4. Medical Agent — Checks medical necessity using ICD-10 codes and clinical guidelines\n\nEach agent provides independent analysis, ensuring comprehensive coverage of your claim.",
  },
  {
    question: "How do I generate an appeal letter?",
    answer: "First, upload your documents and run the Agent Pipeline to analyze your claim. Then navigate to 'Generate Appeal' from the sidebar. You'll need to verify three confirmations (document verification, pipeline review, and legal disclaimer) before generating. The AI creates a personalized appeal letter with IRDAI regulatory citations that you can download or copy.",
  },
  {
    question: "What is PED (Pre-Existing Disease) exclusion?",
    answer: "PED refers to any illness or medical condition that was diagnosed or existed before the insurance policy was purchased. Under IRDAI regulations, PED exclusions cannot exceed 48 months (4 years) of continuous coverage. After this waiting period, pre-existing conditions must be covered by the insurer.",
  },
  {
    question: "How long does claim processing take?",
    answer: "Under IRDAI regulations, insurers must settle or reject claims within 30 days of receiving all required documents. If more information is needed, they must communicate this within 15 days. Our pipeline analysis typically completes within 5-10 seconds, giving you instant insights.",
  },
  {
    question: "Is my data secure?",
    answer: "Yes. All your documents are processed locally on our server. We do not share your personal or medical information with any third parties. The AI chatbot (powered by Ollama) runs locally, ensuring your conversations stay private. We recommend not uploading documents containing sensitive information beyond what's needed for claim analysis.",
  },
  {
    question: "What is the Insurance Ombudsman?",
    answer: "The Insurance Ombudsman is an independent authority that resolves insurance disputes. Key facts:\n• Free of cost — no lawyer needed\n• For claims up to ₹30 lakhs\n• Decision is binding on the insurer (but not on you)\n• Must file complaint within 1 year of denial\n• Available in 17 locations across India",
  },
  {
    question: "How do I contact customer support?",
    answer: `You can reach us via email at ${SUPPORT_EMAIL}. We typically respond within 24 hours on business days. For urgent issues, please include 'URGENT' in your email subject line.`,
  },
];

const quickLinks = [
  {
    title: "IRDAI Official Website",
    url: "https://irdai.gov.in",
    icon: FiShield,
    description: "Official IRDAI regulations and circulars",
  },
  {
    title: "Insurance Ombudsman",
    url: "https://www.cioins.co.in",
    icon: FiUsers,
    description: "File complaints, find nearest ombudsman office",
  },
  {
    title: "IRDAI Bima Bharosa (IGMS)",
    url: "https://bimabharosa.irdai.gov.in",
    icon: FiAlertCircle,
    description: "Integrated Grievance Management System",
  },
  {
    title: "National Consumer Disputes Redressal",
    url: "https://ncdrc.nic.in",
    icon: FiFileText,
    description: "Consumer courts for insurance disputes",
  },
];

export default function HelpPage() {
  const toast = useToast();
  const [contactName, setContactName] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [contactMessage, setContactMessage] = useState("");
  const [isSending, setIsSending] = useState(false);

  const handleSendMessage = async () => {
    if (!contactName.trim() || !contactEmail.trim() || !contactMessage.trim()) {
      toast({
        title: "Missing Fields",
        description: "Please fill in all fields before sending.",
        status: "warning",
        duration: 3000,
        isClosable: true,
        position: "top",
      });
      return;
    }

    setIsSending(true);
    try {
      // Simulate sending
      await new Promise((r) => setTimeout(r, 1000));
      toast({
        title: "Message Sent!",
        description: `Your message has been sent to ${SUPPORT_EMAIL}. We'll get back to you within 24 hours.`,
        status: "success",
        duration: 5000,
        isClosable: true,
        position: "top",
      });
      setContactName("");
      setContactEmail("");
      setContactMessage("");
    } catch {
      toast({
        title: "Send Failed",
        description: "Could not send your message. Please try emailing directly.",
        status: "error",
        duration: 3000,
        isClosable: true,
        position: "top",
      });
    } finally {
      setIsSending(false);
    }
  };

  return (
    <Flex minH="100vh" bg="bg.page">
      <Sidebar />
      <Box ml="260px" flex={1} p={8} maxW="calc(100vw - 260px)">
        {/* Header */}
        <Flex justify="space-between" align="center" mb={6}>
          <Box>
            <Text fontSize="2xl" fontWeight="800" color="text.primary">Help & Support</Text>
            <Text color="text.muted" fontSize="sm">
              Get help with ClaimAssist AI, learn about insurance processes, and contact support
            </Text>
          </Box>
          <Badge
            colorScheme="green"
            variant="subtle"
            borderRadius="full"
            px={4}
            py={2}
            fontSize="sm"
          >
            <Icon as={FiLifeBuoy} mr={1} /> Help Centre
          </Badge>
        </Flex>

        {/* Quick Contact Cards */}
        <Grid templateColumns="repeat(3, 1fr)" gap={4} mb={6}>
          <GridItem>
            <Box
              bg="linear-gradient(135deg, #5A67D8 0%, #667EEA 100%)"
              borderRadius="2xl"
              p={5}
              color="white"
              className="animate-fade-in"
            >
              <HStack spacing={3} mb={3}>
                <Flex w="40px" h="40px" borderRadius="xl" bg="whiteAlpha.200" align="center" justify="center">
                  <Icon as={FiMail} boxSize={5} />
                </Flex>
                <Text fontWeight="700" fontSize="sm">Email Support</Text>
              </HStack>
              <Text fontSize="sm" fontWeight="600" mb={1}>{SUPPORT_EMAIL}</Text>
              <Text fontSize="xs" opacity={0.8}>Response within 24 hours</Text>
            </Box>
          </GridItem>
          <GridItem>
            <Box
              bg="linear-gradient(135deg, #38B2AC 0%, #4FD1C5 100%)"
              borderRadius="2xl"
              p={5}
              color="white"
              className="animate-fade-in"
            >
              <HStack spacing={3} mb={3}>
                <Flex w="40px" h="40px" borderRadius="xl" bg="whiteAlpha.200" align="center" justify="center">
                  <Icon as={FiMessageCircle} boxSize={5} />
                </Flex>
                <Text fontWeight="700" fontSize="sm">AI Chatbot</Text>
              </HStack>
              <Text fontSize="sm" fontWeight="600" mb={1}>Available 24/7</Text>
              <Text fontSize="xs" opacity={0.8}>Click the chat icon to start</Text>
            </Box>
          </GridItem>
          <GridItem>
            <Box
              bg="linear-gradient(135deg, #ED8936 0%, #F6AD55 100%)"
              borderRadius="2xl"
              p={5}
              color="white"
              className="animate-fade-in"
            >
              <HStack spacing={3} mb={3}>
                <Flex w="40px" h="40px" borderRadius="xl" bg="whiteAlpha.200" align="center" justify="center">
                  <Icon as={FiClock} boxSize={5} />
                </Flex>
                <Text fontWeight="700" fontSize="sm">Support Hours</Text>
              </HStack>
              <Text fontSize="sm" fontWeight="600" mb={1}>Mon - Sat: 9 AM - 6 PM</Text>
              <Text fontSize="xs" opacity={0.8}>Indian Standard Time (IST)</Text>
            </Box>
          </GridItem>
        </Grid>

        <Grid templateColumns="2fr 1fr" gap={6}>
          {/* FAQ Section */}
          <GridItem>
            <Box
              bg="bg.card"
              borderRadius="2xl"
              border="1px solid"
              borderColor="border.card"
              p={6}
              className="animate-fade-in"
            >
              <HStack spacing={3} mb={5}>
                <Flex
                  w="48px" h="48px" borderRadius="xl"
                  bg="brand.50" align="center" justify="center"
                >
                  <Icon as={FiHelpCircle} boxSize={6} color="brand.500" />
                </Flex>
                <Box>
                  <Text fontWeight="700" fontSize="lg" color="text.primary">
                    Frequently Asked Questions
                  </Text>
                  <Text fontSize="xs" color="text.muted">
                    Find answers to common questions
                  </Text>
                </Box>
              </HStack>

              <Accordion allowMultiple>
                {faqData.map((faq, index) => (
                  <AccordionItem
                    key={index}
                    border="none"
                    mb={2}
                  >
                    <AccordionButton
                      px={4}
                      py={3}
                      borderRadius="xl"
                      bg="bg.page"
                      _hover={{ bg: "brand.50" }}
                      _expanded={{ bg: "brand.50", color: "brand.700" }}
                      transition="all 0.2s"
                    >
                      <HStack flex={1} textAlign="left" spacing={3}>
                        <Flex
                          w="28px" h="28px" borderRadius="lg"
                          bg="brand.100" align="center" justify="center"
                          flexShrink={0}
                        >
                          <Text fontSize="xs" fontWeight="800" color="brand.600">
                            {index + 1}
                          </Text>
                        </Flex>
                        <Text fontWeight="600" fontSize="sm">{faq.question}</Text>
                      </HStack>
                      <AccordionIcon />
                    </AccordionButton>
                    <AccordionPanel px={4} py={3}>
                      <Text fontSize="sm" color="text.secondary" lineHeight="1.8" whiteSpace="pre-line">
                        {faq.answer}
                      </Text>
                    </AccordionPanel>
                  </AccordionItem>
                ))}
              </Accordion>
            </Box>
          </GridItem>

          {/* Right Column */}
          <GridItem>
            <VStack spacing={6} align="stretch">
              {/* Quick Links */}
              <Box
                bg="bg.card"
                borderRadius="2xl"
                border="1px solid"
                borderColor="border.card"
                p={6}
                className="animate-fade-in"
              >
                <HStack spacing={3} mb={4}>
                  <Icon as={FiBookOpen} boxSize={5} color="blue.500" />
                  <Text fontWeight="700" fontSize="md" color="text.primary">
                    Useful Resources
                  </Text>
                </HStack>

                <VStack spacing={3} align="stretch">
                  {quickLinks.map((link, i) => (
                    <ChakraLink
                      key={i}
                      href={link.url}
                      isExternal
                      _hover={{ textDecoration: "none" }}
                    >
                      <Flex
                        p={3}
                        borderRadius="xl"
                        bg="bg.page"
                        _hover={{ bg: "blue.50", transform: "translateX(3px)" }}
                        transition="all 0.2s"
                        align="center"
                        justify="space-between"
                      >
                        <HStack spacing={3}>
                          <Icon as={link.icon} boxSize={4} color="blue.500" />
                          <Box>
                            <Text fontSize="sm" fontWeight="600" color="text.primary">
                              {link.title}
                            </Text>
                            <Text fontSize="xs" color="text.muted">
                              {link.description}
                            </Text>
                          </Box>
                        </HStack>
                        <Icon as={FiExternalLink} boxSize={3} color="text.dimmed" />
                      </Flex>
                    </ChakraLink>
                  ))}
                </VStack>
              </Box>

              {/* Contact Form */}
              <Box
                bg="bg.card"
                borderRadius="2xl"
                border="1px solid"
                borderColor="border.card"
                p={6}
                className="animate-fade-in"
              >
                <HStack spacing={3} mb={4}>
                  <Icon as={FiSend} boxSize={5} color="green.500" />
                  <Text fontWeight="700" fontSize="md" color="text.primary">
                    Send Us a Message
                  </Text>
                </HStack>

                <VStack spacing={3}>
                  <Input
                    placeholder="Your Name"
                    value={contactName}
                    onChange={(e) => setContactName(e.target.value)}
                    borderRadius="xl"
                    bg="bg.input"
                    border="2px solid"
                    borderColor="transparent"
                    _focus={{ borderColor: "brand.400", bg: "bg.card" }}
                    fontSize="sm"
                  />
                  <Input
                    placeholder="Your Email"
                    type="email"
                    value={contactEmail}
                    onChange={(e) => setContactEmail(e.target.value)}
                    borderRadius="xl"
                    bg="bg.input"
                    border="2px solid"
                    borderColor="transparent"
                    _focus={{ borderColor: "brand.400", bg: "bg.card" }}
                    fontSize="sm"
                  />
                  <Textarea
                    placeholder="Describe your issue or question..."
                    value={contactMessage}
                    onChange={(e) => setContactMessage(e.target.value)}
                    borderRadius="xl"
                    bg="bg.input"
                    border="2px solid"
                    borderColor="transparent"
                    _focus={{ borderColor: "brand.400", bg: "bg.card" }}
                    fontSize="sm"
                    rows={4}
                    resize="none"
                  />
                  <Button
                    w="full"
                    leftIcon={<FiSend />}
                    bg="linear-gradient(135deg, #5A67D8 0%, #667EEA 100%)"
                    color="white"
                    borderRadius="xl"
                    onClick={handleSendMessage}
                    isLoading={isSending}
                    loadingText="Sending..."
                    _hover={{ transform: "translateY(-1px)", boxShadow: "md" }}
                    transition="all 0.2s"
                  >
                    Send Message
                  </Button>
                </VStack>
              </Box>
            </VStack>
          </GridItem>
        </Grid>
      </Box>
      <ChatWidget />
    </Flex>
  );
}
