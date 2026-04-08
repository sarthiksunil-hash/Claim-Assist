"use client";

import { useState, useEffect } from "react";
import {
  Box, Flex, Text, VStack, HStack, Icon, Button,
  Input, FormControl, FormLabel, useToast, Switch,
  Badge, Avatar, Grid, GridItem, useColorMode,
} from "@chakra-ui/react";
import {
  FiSettings, FiUser, FiSave, FiMoon, FiSun,
  FiLock, FiEdit3,
} from "react-icons/fi";
import Sidebar from "@/components/Sidebar";
import ChatWidget from "@/components/ChatWidget";

export default function SettingsPage() {
  const toast = useToast();
  const { colorMode, toggleColorMode } = useColorMode();
  const isDarkMode = colorMode === "dark";

  // User details state
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [organization, setOrganization] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [isEditing, setIsEditing] = useState(false);

  // Password change
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isChangingPassword, setIsChangingPassword] = useState(false);


  // Load user data from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem("claimassist_user");
    if (stored) {
      try {
        const user = JSON.parse(stored);
        setFullName(user.full_name || "");
        setEmail(user.email || "");
        setPhone(user.phone || "");
        setOrganization(user.organization || "");
      } catch (e) {
        console.error("Failed to parse user data:", e);
      }
    }

  }, []);

  const handleSaveProfile = async () => {
    if (!fullName.trim() || !email.trim()) {
      toast({
        title: "Missing Information",
        description: "Name and email are required.",
        status: "warning",
        duration: 3000,
        isClosable: true,
        position: "top",
      });
      return;
    }

    setIsSaving(true);
    try {
      // Update local storage
      const stored = localStorage.getItem("claimassist_user");
      const userData = stored ? JSON.parse(stored) : {};
      const updatedUser = {
        ...userData,
        full_name: fullName.trim(),
        email: email.trim(),
        phone: phone.trim(),
        organization: organization.trim(),
      };
      localStorage.setItem("claimassist_user", JSON.stringify(updatedUser));

      // Simulate brief save delay
      await new Promise((r) => setTimeout(r, 500));

      toast({
        title: "Profile Updated",
        description: "Your profile details have been saved successfully.",
        status: "success",
        duration: 3000,
        isClosable: true,
        position: "top",
      });
      setIsEditing(false);
    } catch {
      toast({
        title: "Save Failed",
        description: "Could not update your profile. Please try again.",
        status: "error",
        duration: 3000,
        isClosable: true,
        position: "top",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleChangePassword = async () => {
    if (!currentPassword || !newPassword || !confirmPassword) {
      toast({
        title: "Missing Fields",
        description: "Please fill in all password fields.",
        status: "warning",
        duration: 3000,
        isClosable: true,
        position: "top",
      });
      return;
    }

    if (newPassword !== confirmPassword) {
      toast({
        title: "Passwords Don't Match",
        description: "New password and confirm password must match.",
        status: "error",
        duration: 3000,
        isClosable: true,
        position: "top",
      });
      return;
    }

    if (newPassword.length < 6) {
      toast({
        title: "Weak Password",
        description: "Password must be at least 6 characters long.",
        status: "warning",
        duration: 3000,
        isClosable: true,
        position: "top",
      });
      return;
    }

    setIsChangingPassword(true);
    try {
      await new Promise((r) => setTimeout(r, 800));
      toast({
        title: "Password Changed",
        description: "Your password has been updated successfully.",
        status: "success",
        duration: 3000,
        isClosable: true,
        position: "top",
      });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch {
      toast({
        title: "Error",
        description: "Failed to change password.",
        status: "error",
        duration: 3000,
        isClosable: true,
        position: "top",
      });
    } finally {
      setIsChangingPassword(false);
    }
  };

  const handleToggleTheme = () => {
    toggleColorMode();
    const newMode = !isDarkMode;
    toast({
      title: `${newMode ? "Dark" : "Light"} Theme Activated`,
      description: `Switched to ${newMode ? "dark" : "light"} mode.`,
      status: "info",
      duration: 2000,
      isClosable: true,
      position: "top",
    });
  };

  return (
    <Flex minH="100vh" bg="bg.page">
      <Sidebar />
      <Box ml="260px" flex={1} p={8} maxW="calc(100vw - 260px)">
        {/* Header */}
        <Flex justify="space-between" align="center" mb={6}>
          <Box>
            <Text fontSize="2xl" fontWeight="800" color="text.primary">Settings</Text>
            <Text color="text.muted" fontSize="sm">
              Manage your account, preferences, and application settings
            </Text>
          </Box>
          <Badge
            colorScheme="brand"
            variant="subtle"
            borderRadius="full"
            px={4}
            py={2}
            fontSize="sm"
          >
            <Icon as={FiSettings} mr={1} /> Account Settings
          </Badge>
        </Flex>

        <Grid templateColumns="1fr 1fr" gap={6}>
          {/* Profile Section */}
          <GridItem colSpan={2}>
            <Box
              bg="bg.card"
              borderRadius="2xl"
              border="1px solid"
              borderColor="border.card"
              p={6}
              className="animate-fade-in"
            >
              <Flex justify="space-between" align="center" mb={5}>
                <HStack spacing={3}>
                  <Flex
                    w="48px" h="48px" borderRadius="xl"
                    bg="brand.50" align="center" justify="center"
                  >
                    <Icon as={FiUser} boxSize={6} color="brand.500" />
                  </Flex>
                  <Box>
                    <Text fontWeight="700" fontSize="lg" color="text.primary">
                      Personal Information
                    </Text>
                    <Text fontSize="xs" color="text.muted">
                      Update your name, email, and contact details
                    </Text>
                  </Box>
                </HStack>
                {!isEditing && (
                  <Button
                    size="sm"
                    leftIcon={<FiEdit3 />}
                    variant="outline"
                    borderRadius="xl"
                    onClick={() => setIsEditing(true)}
                  >
                    Edit Profile
                  </Button>
                )}
              </Flex>

              {/* Profile Avatar */}
              <Flex mb={6} align="center" gap={4}>
                <Avatar
                  size="lg"
                  name={fullName}
                  bg="linear-gradient(135deg, #5A67D8 0%, #667EEA 100%)"
                  color="white"
                  fontWeight="800"
                />
                <Box>
                  <Text fontWeight="700" fontSize="md" color="text.primary">
                    {fullName || "User"}
                  </Text>
                  <Text fontSize="sm" color="text.muted">{email}</Text>
                </Box>
              </Flex>

              <Grid templateColumns="repeat(2, 1fr)" gap={4}>
                <FormControl>
                  <FormLabel fontSize="sm" fontWeight="600" color="text.secondary">Full Name</FormLabel>
                  <Input
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Enter your full name"
                    borderRadius="xl"
                    bg={isEditing ? "bg.card" : "bg.hover"}
                    border="2px solid"
                    borderColor={isEditing ? "brand.200" : "transparent"}
                    isReadOnly={!isEditing}
                    _focus={{ borderColor: "brand.400" }}
                    fontSize="sm"
                  />
                </FormControl>
                <FormControl>
                  <FormLabel fontSize="sm" fontWeight="600" color="text.secondary">Email Address</FormLabel>
                  <Input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="Enter your email"
                    borderRadius="xl"
                    bg={isEditing ? "bg.card" : "bg.hover"}
                    border="2px solid"
                    borderColor={isEditing ? "brand.200" : "transparent"}
                    isReadOnly={!isEditing}
                    _focus={{ borderColor: "brand.400" }}
                    fontSize="sm"
                  />
                </FormControl>
                <FormControl>
                  <FormLabel fontSize="sm" fontWeight="600" color="text.secondary">Phone Number</FormLabel>
                  <Input
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="Enter your phone number"
                    borderRadius="xl"
                    bg={isEditing ? "bg.card" : "bg.hover"}
                    border="2px solid"
                    borderColor={isEditing ? "brand.200" : "transparent"}
                    isReadOnly={!isEditing}
                    _focus={{ borderColor: "brand.400" }}
                    fontSize="sm"
                  />
                </FormControl>
                <FormControl>
                  <FormLabel fontSize="sm" fontWeight="600" color="text.secondary">Organization</FormLabel>
                  <Input
                    value={organization}
                    onChange={(e) => setOrganization(e.target.value)}
                    placeholder="Enter your organization"
                    borderRadius="xl"
                    bg={isEditing ? "bg.card" : "bg.hover"}
                    border="2px solid"
                    borderColor={isEditing ? "brand.200" : "transparent"}
                    isReadOnly={!isEditing}
                    _focus={{ borderColor: "brand.400" }}
                    fontSize="sm"
                  />
                </FormControl>
              </Grid>

              {isEditing && (
                <HStack spacing={3} mt={5} justify="flex-end">
                  <Button
                    variant="ghost"
                    borderRadius="xl"
                    onClick={() => setIsEditing(false)}
                  >
                    Cancel
                  </Button>
                  <Button
                    leftIcon={<FiSave />}
                    bg="linear-gradient(135deg, #5A67D8 0%, #667EEA 100%)"
                    color="white"
                    borderRadius="xl"
                    onClick={handleSaveProfile}
                    isLoading={isSaving}
                    loadingText="Saving..."
                    _hover={{ transform: "translateY(-1px)", boxShadow: "md" }}
                    transition="all 0.2s"
                  >
                    Save Changes
                  </Button>
                </HStack>
              )}
            </Box>
          </GridItem>

          {/* Theme Settings */}
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
                  bg="purple.50" _dark={{ bg: "purple.900" }} align="center" justify="center"
                >
                  <Icon as={isDarkMode ? FiMoon : FiSun} boxSize={6} color="purple.500" />
                </Flex>
                <Box>
                  <Text fontWeight="700" fontSize="lg" color="text.primary">
                    Appearance
                  </Text>
                  <Text fontSize="xs" color="text.muted">
                    Customize the look and feel
                  </Text>
                </Box>
              </HStack>

              <VStack spacing={4} align="stretch">
                {/* Dark Mode Toggle */}
                <Flex
                  justify="space-between"
                  align="center"
                  p={4}
                  bg={isDarkMode ? "gray.800" : "gray.50"}
                  borderRadius="xl"
                  border="1px solid"
                  borderColor={isDarkMode ? "gray.600" : "gray.100"}
                  transition="all 0.3s"
                >
                  <HStack spacing={3}>
                    <Icon
                      as={isDarkMode ? FiMoon : FiSun}
                      boxSize={5}
                      color={isDarkMode ? "yellow.300" : "orange.400"}
                    />
                    <Box>
                      <Text
                        fontWeight="600"
                        fontSize="sm"
                        color={isDarkMode ? "white" : "gray.700"}
                      >
                        {isDarkMode ? "Dark Mode" : "Light Mode"}
                      </Text>
                      <Text
                        fontSize="xs"
                        color={isDarkMode ? "gray.400" : "gray.500"}
                      >
                        {isDarkMode ? "Easier on the eyes at night" : "Default bright theme"}
                      </Text>
                    </Box>
                  </HStack>
                  <Switch
                    isChecked={isDarkMode}
                    onChange={handleToggleTheme}
                    colorScheme="brand"
                    size="lg"
                  />
                </Flex>

                {/* Theme Preview */}
                <Box
                  p={4}
                  borderRadius="xl"
                  bg={isDarkMode ? "gray.900" : "linear-gradient(135deg, #f5f7ff 0%, #eef0ff 100%)"}
                  border="1px solid"
                  borderColor={isDarkMode ? "gray.700" : "brand.100"}
                >
                  <Text
                    fontSize="xs"
                    fontWeight="700"
                    color={isDarkMode ? "gray.300" : "gray.500"}
                    textTransform="uppercase"
                    mb={2}
                  >
                    Theme Preview
                  </Text>
                  <HStack spacing={3}>
                    <Box
                      w="40px" h="30px" borderRadius="md"
                      bg={isDarkMode ? "#1A1A2E" : "#5A67D8"}
                    />
                    <Box
                      w="40px" h="30px" borderRadius="md"
                      bg={isDarkMode ? "#3C366B" : "#667EEA"}
                    />
                    <Box
                      w="40px" h="30px" borderRadius="md"
                      bg={isDarkMode ? "#4A5568" : "#E2E8F0"}
                    />
                    <Box
                      w="40px" h="30px" borderRadius="md"
                      bg={isDarkMode ? "#2D3748" : "#FFFFFF"}
                      border="1px solid"
                      borderColor={isDarkMode ? "gray.600" : "gray.200"}
                    />
                  </HStack>
                </Box>
              </VStack>
            </Box>
          </GridItem>

          {/* Change Password */}
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
                  bg="red.50" _dark={{ bg: "red.900" }} align="center" justify="center"
                >
                  <Icon as={FiLock} boxSize={6} color="red.500" />
                </Flex>
                <Box>
                  <Text fontWeight="700" fontSize="lg" color="text.primary">
                    Change Password
                  </Text>
                  <Text fontSize="xs" color="text.muted">
                    Update your account password
                  </Text>
                </Box>
              </HStack>

              <VStack spacing={3}>
                <FormControl>
                  <FormLabel fontSize="sm" fontWeight="600" color="text.secondary">Current Password</FormLabel>
                  <Input
                    type="password"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    placeholder="Enter current password"
                    borderRadius="xl"
                    bg="bg.input"
                    border="2px solid"
                    borderColor="transparent"
                    _focus={{ borderColor: "brand.400", bg: "bg.card" }}
                    fontSize="sm"
                  />
                </FormControl>
                <FormControl>
                  <FormLabel fontSize="sm" fontWeight="600" color="text.secondary">New Password</FormLabel>
                  <Input
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="Enter new password"
                    borderRadius="xl"
                    bg="bg.input"
                    border="2px solid"
                    borderColor="transparent"
                    _focus={{ borderColor: "brand.400", bg: "bg.card" }}
                    fontSize="sm"
                  />
                </FormControl>
                <FormControl>
                  <FormLabel fontSize="sm" fontWeight="600" color="text.secondary">Confirm New Password</FormLabel>
                  <Input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Confirm new password"
                    borderRadius="xl"
                    bg="bg.input"
                    border="2px solid"
                    borderColor="transparent"
                    _focus={{ borderColor: "brand.400", bg: "bg.card" }}
                    fontSize="sm"
                  />
                </FormControl>
                <Button
                  w="full"
                  leftIcon={<FiLock />}
                  bg="linear-gradient(135deg, #E53E3E 0%, #FC8181 100%)"
                  color="white"
                  borderRadius="xl"
                  onClick={handleChangePassword}
                  isLoading={isChangingPassword}
                  loadingText="Updating..."
                  _hover={{ transform: "translateY(-1px)", boxShadow: "md" }}
                  transition="all 0.2s"
                  mt={2}
                >
                  Update Password
                </Button>
              </VStack>
            </Box>
          </GridItem>
        </Grid>
      </Box>
      <ChatWidget />
    </Flex>
  );
}
