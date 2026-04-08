"use client";

import { useState, useRef, useEffect } from "react";
import {
  Box,
  Flex,
  Text,
  Input,
  IconButton,
  VStack,
  Icon,
  Avatar,
  Spinner,
  Badge,
} from "@chakra-ui/react";
import { FiMessageCircle, FiX, FiSend, FiCpu } from "react-icons/fi";
import api from "@/lib/api";

interface Message {
  id: number;
  text: string;
  sender: "user" | "ai";
  timestamp: Date;
}

export default function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 0,
      text: "Hello! I'm ClaimAssist AI, your intelligent insurance claim assistant. I can help you understand insurance terms, IRDAI regulations, claim processes, and appeal strategies.\n\nTry asking me anything about health insurance!",
      sender: "ai",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load past chat history from Supabase on first open
  const [historyLoaded, setHistoryLoaded] = useState(false);

  useEffect(() => {
    if (!isOpen || historyLoaded) return;
    setHistoryLoaded(true);

    api.get("/api/chat/history")
      .then((res) => {
        const past = res.data?.messages || [];
        if (past.length === 0) return;

        const loaded: Message[] = past
          .filter((m: Record<string, string>) => m.content && m.content.trim() !== "")
          .map((m: Record<string, string>, i: number) => ({
            id: Date.now() + i + 1,
            text: m.content || "",
            sender: (m.role === "user" ? "user" : "ai") as "user" | "ai",
            timestamp: new Date(m.created_at || Date.now()),
          }));

        if (loaded.length === 0) return;

        setMessages((prev) => {
          // Keep the greeting (id=0), append history
          const greeting = prev.filter((m) => m.id === 0);
          return [...greeting, ...loaded];
        });
      })
      .catch((err) => {
        console.log("Chat history unavailable:", err.message || err);
      });
  }, [isOpen, historyLoaded]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || isTyping) return;

    const userMessage: Message = {
      id: Date.now(),
      text: input,
      sender: "user",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const userInput = input;
    setInput("");
    setIsTyping(true);

    try {
      // Call backend API
      const response = await api.post("/api/chat/", { message: userInput });
      const data = response.data;

      const aiMessage: Message = {
        id: Date.now() + 1,
        text: data.response || "Sorry, I couldn't process that. Please try again.",
        sender: "ai",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      console.error("Chat error:", error);
      const errorMessage: Message = {
        id: Date.now() + 1,
        text: "Sorry, I'm having trouble connecting to the AI service. Please check if the backend server is running and try again.",
        sender: "ai",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  // Format text with basic markdown-like support
  const formatText = (text: string) => {
    // Very basic formatting: bold (**text**) and line breaks
    return text.split("\n").map((line, i) => {
      // Bold
      const parts = line.split(/\*\*(.*?)\*\*/g);
      return (
        <Text key={i} as="span" display="block" mb={line === "" ? 2 : 0.5}>
          {parts.map((part, j) =>
            j % 2 === 1 ? (
              <Text key={j} as="span" fontWeight="700">
                {part}
              </Text>
            ) : (
              <Text key={j} as="span">
                {part}
              </Text>
            )
          )}
        </Text>
      );
    });
  };

  return (
    <>
      {/* Chat Toggle Button */}
      {!isOpen && (
        <Box
          position="fixed"
          bottom="24px"
          right="24px"
          zIndex={1000}
          className="animate-fade-in"
        >
          <IconButton
            aria-label="Open chat"
            icon={<FiMessageCircle size={24} />}
            onClick={() => setIsOpen(true)}
            w="60px"
            h="60px"
            borderRadius="full"
            bg="brand.500"
            color="white"
            boxShadow="0 4px 20px rgba(90, 103, 216, 0.4)"
            _hover={{
              bg: "brand.600",
              transform: "scale(1.05)",
              boxShadow: "0 6px 25px rgba(90, 103, 216, 0.5)",
            }}
            _active={{ transform: "scale(0.95)" }}
            transition="all 0.2s ease"
          />
          {/* Notification dot */}
          <Box
            position="absolute"
            top="0"
            right="0"
            w="16px"
            h="16px"
            bg="red.500"
            borderRadius="full"
            border="3px solid white"
          />
        </Box>
      )}

      {/* Chat Panel */}
      {isOpen && (
        <Box
          position="fixed"
          bottom="24px"
          right="24px"
          width="400px"
          height="560px"
          bg="bg.card"
          borderRadius="2xl"
          boxShadow="0 12px 40px rgba(0, 0, 0, 0.15)"
          zIndex={1000}
          display="flex"
          flexDirection="column"
          overflow="hidden"
          className="animate-fade-in-up"
          border="1px solid"
          borderColor="border.card"
        >
          {/* Header */}
          <Flex
            align="center"
            justify="space-between"
            px={4}
            py={3}
            bg="linear-gradient(135deg, #5A67D8 0%, #667EEA 100%)"
            color="white"
          >
            <Flex align="center" gap={3}>
              <Avatar size="sm" name="AI" bg="whiteAlpha.300" color="white" fontSize="xs" fontWeight="800" />
              <Box>
                <Flex align="center" gap={2}>
                  <Text fontWeight="700" fontSize="sm">
                    ClaimAssist AI
                  </Text>
                  <Badge
                    bg="whiteAlpha.200"
                    color="white"
                    fontSize="9px"
                    borderRadius="full"
                    px={1.5}
                    py={0.5}
                  >
                    <Flex align="center" gap={1}>
                      <Icon as={FiCpu} boxSize={2.5} />
                      Ollama
                    </Flex>
                  </Badge>
                </Flex>
                <Text fontSize="xs" opacity={0.8}>
                  Insurance & IRDAI Expert
                </Text>
              </Box>
            </Flex>
            <IconButton
              aria-label="Close chat"
              icon={<FiX />}
              size="sm"
              variant="ghost"
              color="white"
              _hover={{ bg: "whiteAlpha.200" }}
              onClick={() => setIsOpen(false)}
            />
          </Flex>

          {/* Messages */}
          <VStack
            flex={1}
            overflowY="auto"
            px={4}
            py={3}
            spacing={3}
            align="stretch"
            sx={{
              "&::-webkit-scrollbar": { width: "4px" },
              "&::-webkit-scrollbar-track": { bg: "transparent" },
              "&::-webkit-scrollbar-thumb": { bg: "gray.200", borderRadius: "full" },
            }}
          >
            {messages.map((msg) => (
              <Flex
                key={msg.id}
                justify={msg.sender === "user" ? "flex-end" : "flex-start"}
                className="animate-fade-in"
              >
                <Box
                  maxW="88%"
                  px={4}
                  py={2.5}
                  borderRadius={
                    msg.sender === "user"
                      ? "18px 18px 4px 18px"
                      : "18px 18px 18px 4px"
                  }
                  bg={msg.sender === "user" ? "brand.500" : "bg.hover"}
                  color={msg.sender === "user" ? "white" : "text.secondary"}
                  fontSize="sm"
                  lineHeight="1.6"
                >
                  {msg.sender === "ai" ? (
                    <Box>{formatText(msg.text)}</Box>
                  ) : (
                    msg.text
                  )}
                </Box>
              </Flex>
            ))}

            {isTyping && (
              <Flex justify="flex-start">
                <Flex
                  align="center"
                  gap={2}
                  px={4}
                  py={2.5}
                  borderRadius="18px 18px 18px 4px"
                  bg="bg.hover"
                >
                  <Spinner size="xs" color="brand.400" />
                  <Text fontSize="sm" color="text.muted">
                    Thinking...
                  </Text>
                </Flex>
              </Flex>
            )}

            <div ref={messagesEndRef} />
          </VStack>

          {/* Suggested Questions */}
          {messages.length <= 2 && !isTyping && (
            <Flex px={4} py={2} gap={2} flexWrap="wrap" borderTop="1px solid" borderColor="border.subtle">
              {["What is PED?", "IRDAI rules", "Claim denied?"].map((q) => (
                <Box
                  key={q}
                  px={3}
                  py={1}
                  bg="brand.50"
                  color="brand.600"
                  fontSize="xs"
                  fontWeight="600"
                  borderRadius="full"
                  cursor="pointer"
                  _hover={{ bg: "brand.100" }}
                  transition="all 0.15s"
                  onClick={() => {
                    setInput(q);
                  }}
                >
                  {q}
                </Box>
              ))}
            </Flex>
          )}

          {/* Input */}
          <Flex px={4} py={3} borderTop="1px solid" borderColor="border.card" gap={2}>
            <Input
              placeholder="Ask about insurance, IRDAI, claims..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
              size="sm"
              borderRadius="full"
              bg="bg.input"
              border="1px solid"
              borderColor="border.input"
              _focus={{
                borderColor: "brand.400",
                bg: "bg.card",
                boxShadow: "0 0 0 1px rgba(90, 103, 216, 0.3)",
              }}
              fontSize="sm"
            />
            <IconButton
              aria-label="Send message"
              icon={<FiSend />}
              onClick={sendMessage}
              size="sm"
              borderRadius="full"
              bg="brand.500"
              color="white"
              _hover={{ bg: "brand.600" }}
              isDisabled={!input.trim() || isTyping}
            />
          </Flex>

          {/* Footer */}
          <Flex justify="center" py={1.5} bg="bg.hover">
            <Text fontSize="10px" color="text.dimmed">
              Powered by Ollama + Mistral AI
            </Text>
          </Flex>
        </Box>
      )}
    </>
  );
}
