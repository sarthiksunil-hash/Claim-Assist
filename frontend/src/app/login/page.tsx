"use client";

import { useState, useEffect, Suspense } from "react";
import {
  Box,
  Flex,
  Text,
  Input,
  Button,
  VStack,
  HStack,
  Icon,
  InputGroup,
  InputLeftElement,
  InputRightElement,
  FormControl,
  FormLabel,
  FormErrorMessage,
  useToast,

  PinInput,
  PinInputField,
} from "@chakra-ui/react";
import {
  FiMail,
  FiLock,
  FiUser,
  FiEye,
  FiEyeOff,
  FiShield,
  FiArrowRight,
  FiCheck,
  FiRefreshCw,
} from "react-icons/fi";
import { useRouter } from "next/navigation";
import { useSearchParams } from "next/navigation";
import { signupUser, loginUser, verifyOtp, resendOtp, forgotPassword, resetPassword } from "@/lib/api";

type AuthView = "login" | "signup" | "otp" | "forgot" | "reset";

function LoginPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const toast = useToast();

  // ──── State ────────────────────────────────────────────────────
  const [view, setView] = useState<AuthView>("login");
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // Form fields
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [otpValue, setOtpValue] = useState("");
  const [resetToken, setResetToken] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmNewPassword, setConfirmNewPassword] = useState("");
  const [forgotEmail, setForgotEmail] = useState("");

  // Validation
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [resendCooldown, setResendCooldown] = useState(0);

  // Countdown timer for OTP resend
  useEffect(() => {
    if (resendCooldown > 0) {
      const timer = setTimeout(() => setResendCooldown(resendCooldown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [resendCooldown]);

  // Check for reset_token in URL params
  useEffect(() => {
    const token = searchParams.get("reset_token");
    if (token) {
      setResetToken(token);
      setView("reset");
    }
  }, [searchParams]);

  // ──── Validation ───────────────────────────────────────────────
  const validateLogin = () => {
    const newErrors: Record<string, string> = {};
    if (!email) newErrors.email = "Email is required";
    else if (!/\S+@\S+\.\S+/.test(email)) newErrors.email = "Enter a valid email";
    if (!password) newErrors.password = "Password is required";
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const validateSignup = () => {
    const newErrors: Record<string, string> = {};
    if (!fullName.trim()) newErrors.fullName = "Full name is required";
    if (!email) newErrors.email = "Email is required";
    else if (!/\S+@\S+\.\S+/.test(email)) newErrors.email = "Enter a valid email";
    if (!password) newErrors.password = "Password is required";
    else if (password.length < 6) newErrors.password = "Minimum 6 characters required";
    if (password !== confirmPassword) newErrors.confirmPassword = "Passwords do not match";
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // ──── Handlers ─────────────────────────────────────────────────
  const handleLogin = async () => {
    if (!validateLogin()) return;
    setIsLoading(true);
    try {
      const response = await loginUser({ email, password });
      const data = response.data;

      if (data.requires_otp) {
        // User email not verified — show OTP screen
        setView("otp");
        setResendCooldown(30);
        toast({
          title: "Verification Required",
          description: data.message,
          status: "warning",
          duration: 5000,
          isClosable: true,
          position: "top",
        });
      } else if (data.success) {
        // Store user and JWT token in localStorage and mark session as active
        localStorage.setItem("claimassist_user", JSON.stringify(data.user));
        if (data.token) {
          localStorage.setItem("claimassist_token", data.token);
        }
        sessionStorage.setItem("claimassist_session_active", "true");
        toast({
          title: "Welcome back!",
          description: data.message,
          status: "success",
          duration: 3000,
          isClosable: true,
          position: "top",
        });
        router.push("/");
      }
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      const msg =
        err.response?.data?.detail || "Login failed. Please try again.";
      toast({
        title: "Login Error",
        description: msg,
        status: "error",
        duration: 4000,
        isClosable: true,
        position: "top",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSignup = async () => {
    if (!validateSignup()) return;
    setIsLoading(true);
    try {
      const response = await signupUser({
        email,
        password,
        full_name: fullName,
      });
      const data = response.data;

      if (data.requires_otp) {
        setView("otp");
        setResendCooldown(30);
        toast({
          title: "Account Created!",
          description: data.message,
          status: "success",
          duration: 5000,
          isClosable: true,
          position: "top",
        });
      }
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      const msg =
        err.response?.data?.detail || "Signup failed. Please try again.";
      toast({
        title: "Signup Error",
        description: msg,
        status: "error",
        duration: 4000,
        isClosable: true,
        position: "top",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyOtp = async () => {
    if (otpValue.length !== 6) {
      toast({
        title: "Invalid OTP",
        description: "Please enter the complete 6-digit OTP.",
        status: "warning",
        duration: 3000,
        isClosable: true,
        position: "top",
      });
      return;
    }
    setIsLoading(true);
    try {
      const response = await verifyOtp({ email, otp: otpValue });
      const data = response.data;

      if (data.success) {
        // Store token if provided (user is now verified)
        if (data.token) {
          localStorage.setItem("claimassist_token", data.token);
        }
        if (data.user) {
          localStorage.setItem("claimassist_user", JSON.stringify(data.user));
        }
        toast({
          title: "Verified!",
          description: data.message,
          status: "success",
          duration: 3000,
          isClosable: true,
          position: "top",
        });
        // Go to login
        setView("login");
        setPassword("");
        setOtpValue("");
      }
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      const msg =
        err.response?.data?.detail || "OTP verification failed.";
      toast({
        title: "Verification Error",
        description: msg,
        status: "error",
        duration: 4000,
        isClosable: true,
        position: "top",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendOtp = async () => {
    if (resendCooldown > 0) return;
    setIsLoading(true);
    try {
      const response = await resendOtp({ email });
      const data = response.data;
      setResendCooldown(30);
      toast({
        title: "OTP Resent",
        description: data.message,
        status: "info",
        duration: 3000,
        isClosable: true,
        position: "top",
      });
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      const msg = err.response?.data?.detail || "Failed to resend OTP.";
      toast({
        title: "Error",
        description: msg,
        status: "error",
        duration: 4000,
        isClosable: true,
        position: "top",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleForgotPassword = async () => {
    const emailToUse = forgotEmail || email;
    if (!emailToUse || !/\S+@\S+\.\S+/.test(emailToUse)) {
      setErrors({ forgotEmail: "Enter a valid email address" });
      return;
    }
    setIsLoading(true);
    try {
      const response = await forgotPassword({ email: emailToUse });
      toast({
        title: "Reset Link Sent",
        description: response.data.message,
        status: "success",
        duration: 5000,
        isClosable: true,
        position: "top",
      });
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      toast({
        title: "Error",
        description: err.response?.data?.detail || "Failed to send reset link.",
        status: "error",
        duration: 4000,
        isClosable: true,
        position: "top",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetPassword = async () => {
    const newErrors: Record<string, string> = {};
    if (!newPassword) newErrors.newPassword = "Password is required";
    else if (newPassword.length < 6) newErrors.newPassword = "Minimum 6 characters";
    if (newPassword !== confirmNewPassword) newErrors.confirmNewPassword = "Passwords do not match";
    setErrors(newErrors);
    if (Object.keys(newErrors).length > 0) return;

    setIsLoading(true);
    try {
      const response = await resetPassword({ token: resetToken, new_password: newPassword });
      toast({
        title: "Password Reset!",
        description: response.data.message,
        status: "success",
        duration: 5000,
        isClosable: true,
        position: "top",
      });
      // Clear URL params and go to login
      router.replace("/login");
      setView("login");
      setNewPassword("");
      setConfirmNewPassword("");
      setResetToken("");
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      toast({
        title: "Reset Failed",
        description: err.response?.data?.detail || "Password reset failed.",
        status: "error",
        duration: 4000,
        isClosable: true,
        position: "top",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const switchView = (newView: AuthView) => {
    setErrors({});
    setOtpValue("");
    setView(newView);
  };

  // ──── Render Helpers ───────────────────────────────────────────

  const renderLoginForm = () => (
    <VStack spacing={5} w="full">
      <FormControl isInvalid={!!errors.email}>
        <FormLabel fontSize="sm" fontWeight="600" color="text.primary">
          Email Address
        </FormLabel>
        <InputGroup size="lg">
          <InputLeftElement pointerEvents="none">
            <Icon as={FiMail} color="text.dimmed" />
          </InputLeftElement>
          <Input
            id="login-email"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            bg="bg.input"
            borderRadius="xl"
            border="2px solid"
            borderColor="transparent"
            _hover={{ bg: "bg.hover" }}
            _focus={{ bg: "bg.card", borderColor: "brand.400" }}
            fontSize="sm"
            pl="44px"
          />
        </InputGroup>
        <FormErrorMessage fontSize="xs">{errors.email}</FormErrorMessage>
      </FormControl>

      <FormControl isInvalid={!!errors.password}>
        <FormLabel fontSize="sm" fontWeight="600" color="text.primary">
          Password
        </FormLabel>
        <InputGroup size="lg">
          <InputLeftElement pointerEvents="none">
            <Icon as={FiLock} color="text.dimmed" />
          </InputLeftElement>
          <Input
            id="login-password"
            type={showPassword ? "text" : "password"}
            placeholder="Enter your password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            bg="bg.input"
            borderRadius="xl"
            border="2px solid"
            borderColor="transparent"
            _hover={{ bg: "bg.hover" }}
            _focus={{ bg: "bg.card", borderColor: "brand.400" }}
            fontSize="sm"
            pl="44px"
            onKeyDown={(e) => e.key === "Enter" && handleLogin()}
          />
          <InputRightElement cursor="pointer" onClick={() => setShowPassword(!showPassword)}>
            <Icon as={showPassword ? FiEyeOff : FiEye} color="text.dimmed" />
          </InputRightElement>
        </InputGroup>
        <FormErrorMessage fontSize="xs">{errors.password}</FormErrorMessage>
      </FormControl>

      <Button
        id="login-button"
        w="full"
        size="lg"
        bg="linear-gradient(135deg, #5A67D8 0%, #667EEA 100%)"
        color="white"
        fontWeight="700"
        borderRadius="xl"
        fontSize="md"
        _hover={{
          bg: "linear-gradient(135deg, #4C51BF 0%, #5A67D8 100%)",
          transform: "translateY(-2px)",
          boxShadow: "0 8px 25px rgba(90, 103, 216, 0.35)",
        }}
        _active={{ transform: "translateY(0)" }}
        transition="all 0.25s ease"
        onClick={handleLogin}
        isLoading={isLoading}
        loadingText="Signing in..."
        rightIcon={<FiArrowRight />}
      >
        Sign In
      </Button>

      <Flex justify="center">
        <Text
          fontSize="sm"
          color="brand.500"
          fontWeight="600"
          cursor="pointer"
          _hover={{ color: "brand.700", textDecoration: "underline" }}
          onClick={() => { setForgotEmail(email); switchView("forgot"); }}
        >
          Forgot Password?
        </Text>
      </Flex>

      <Text fontSize="sm" color="text.muted" textAlign="center">
        Don&apos;t have an account?{" "}
        <Text
          as="span"
          color="brand.500"
          fontWeight="600"
          cursor="pointer"
          _hover={{ color: "brand.700", textDecoration: "underline" }}
          onClick={() => switchView("signup")}
        >
          Create one
        </Text>
      </Text>
    </VStack>
  );

  const renderSignupForm = () => (
    <VStack spacing={4} w="full">
      <FormControl isInvalid={!!errors.fullName}>
        <FormLabel fontSize="sm" fontWeight="600" color="text.primary">
          Full Name
        </FormLabel>
        <InputGroup size="lg">
          <InputLeftElement pointerEvents="none">
            <Icon as={FiUser} color="text.dimmed" />
          </InputLeftElement>
          <Input
            id="signup-name"
            type="text"
            placeholder="Sunil Kumar"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            bg="bg.input"
            borderRadius="xl"
            border="2px solid"
            borderColor="transparent"
            _hover={{ bg: "bg.hover" }}
            _focus={{ bg: "bg.card", borderColor: "brand.400" }}
            fontSize="sm"
            pl="44px"
          />
        </InputGroup>
        <FormErrorMessage fontSize="xs">{errors.fullName}</FormErrorMessage>
      </FormControl>

      <FormControl isInvalid={!!errors.email}>
        <FormLabel fontSize="sm" fontWeight="600" color="text.primary">
          Email Address
        </FormLabel>
        <InputGroup size="lg">
          <InputLeftElement pointerEvents="none">
            <Icon as={FiMail} color="text.dimmed" />
          </InputLeftElement>
          <Input
            id="signup-email"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            bg="bg.input"
            borderRadius="xl"
            border="2px solid"
            borderColor="transparent"
            _hover={{ bg: "bg.hover" }}
            _focus={{ bg: "bg.card", borderColor: "brand.400" }}
            fontSize="sm"
            pl="44px"
          />
        </InputGroup>
        <FormErrorMessage fontSize="xs">{errors.email}</FormErrorMessage>
      </FormControl>

      <FormControl isInvalid={!!errors.password}>
        <FormLabel fontSize="sm" fontWeight="600" color="text.primary">
          Create Password
        </FormLabel>
        <InputGroup size="lg">
          <InputLeftElement pointerEvents="none">
            <Icon as={FiLock} color="text.dimmed" />
          </InputLeftElement>
          <Input
            id="signup-password"
            type={showPassword ? "text" : "password"}
            placeholder="Min. 6 characters"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            bg="bg.input"
            borderRadius="xl"
            border="2px solid"
            borderColor="transparent"
            _hover={{ bg: "bg.hover" }}
            _focus={{ bg: "bg.card", borderColor: "brand.400" }}
            fontSize="sm"
            pl="44px"
          />
          <InputRightElement cursor="pointer" onClick={() => setShowPassword(!showPassword)}>
            <Icon as={showPassword ? FiEyeOff : FiEye} color="text.dimmed" />
          </InputRightElement>
        </InputGroup>
        <FormErrorMessage fontSize="xs">{errors.password}</FormErrorMessage>
      </FormControl>

      <FormControl isInvalid={!!errors.confirmPassword}>
        <FormLabel fontSize="sm" fontWeight="600" color="text.primary">
          Confirm Password
        </FormLabel>
        <InputGroup size="lg">
          <InputLeftElement pointerEvents="none">
            <Icon as={FiLock} color="text.dimmed" />
          </InputLeftElement>
          <Input
            id="signup-confirm-password"
            type={showConfirmPassword ? "text" : "password"}
            placeholder="Re-enter your password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            bg="bg.input"
            borderRadius="xl"
            border="2px solid"
            borderColor="transparent"
            _hover={{ bg: "bg.hover" }}
            _focus={{ bg: "bg.card", borderColor: "brand.400" }}
            fontSize="sm"
            pl="44px"
            onKeyDown={(e) => e.key === "Enter" && handleSignup()}
          />
          <InputRightElement cursor="pointer" onClick={() => setShowConfirmPassword(!showConfirmPassword)}>
            <Icon as={showConfirmPassword ? FiEyeOff : FiEye} color="text.dimmed" />
          </InputRightElement>
        </InputGroup>
        <FormErrorMessage fontSize="xs">{errors.confirmPassword}</FormErrorMessage>
      </FormControl>

      <Button
        id="signup-button"
        w="full"
        size="lg"
        bg="linear-gradient(135deg, #5A67D8 0%, #667EEA 100%)"
        color="white"
        fontWeight="700"
        borderRadius="xl"
        fontSize="md"
        _hover={{
          bg: "linear-gradient(135deg, #4C51BF 0%, #5A67D8 100%)",
          transform: "translateY(-2px)",
          boxShadow: "0 8px 25px rgba(90, 103, 216, 0.35)",
        }}
        _active={{ transform: "translateY(0)" }}
        transition="all 0.25s ease"
        onClick={handleSignup}
        isLoading={isLoading}
        loadingText="Creating account..."
        rightIcon={<FiArrowRight />}
      >
        Create Account
      </Button>

      <Text fontSize="sm" color="text.muted" textAlign="center">
        Already have an account?{" "}
        <Text
          as="span"
          color="brand.500"
          fontWeight="600"
          cursor="pointer"
          _hover={{ color: "brand.700", textDecoration: "underline" }}
          onClick={() => switchView("login")}
        >
          Sign in
        </Text>
      </Text>
    </VStack>
  );

  const renderOtpForm = () => (
    <VStack spacing={6} w="full" textAlign="center">
      {/* OTP icon */}
      <Flex
        w="72px"
        h="72px"
        borderRadius="full"
        bg="brand.50"
        align="center"
        justify="center"
        mx="auto"
      >
        <Icon as={FiShield} boxSize={8} color="brand.500" />
      </Flex>

      <Box>
        <Text fontSize="lg" fontWeight="700" color="text.primary" mb={1}>
          Verify Your Email
        </Text>
        <Text fontSize="sm" color="text.muted">
          We&apos;ve sent a 6-digit code to
        </Text>
        <Text fontSize="sm" fontWeight="600" color="brand.600">
          {email}
        </Text>
      </Box>

      {/* Email Instruction */}
      <Box
        bg="blue.50"
        _dark={{ bg: "blue.900", borderColor: "blue.700" }}
        borderRadius="xl"
        px={4}
        py={4}
        border="1px solid"
        borderColor="blue.200"
        w="full"
      >
        <HStack spacing={3} mb={2}>
          <Flex
            w="32px"
            h="32px"
            borderRadius="lg"
            bg="blue.100"
            align="center"
            justify="center"
            flexShrink={0}
          >
            <Icon as={FiMail} color="blue.600" boxSize={4} />
          </Flex>
          <Text fontSize="sm" fontWeight="700" color="blue.800" _dark={{ color: "blue.200" }}>
            Check your email inbox
          </Text>
        </HStack>
        <Text fontSize="xs" color="blue.600" _dark={{ color: "blue.300" }} lineHeight="1.6" pl="44px">
          We&apos;ve sent a 6-digit verification code to your email.
          Please check your inbox (and spam/junk folder) and enter the code below.
        </Text>
      </Box>

      {/* OTP Input */}
      <HStack justify="center" spacing={3}>
        <PinInput
          size="lg"
          value={otpValue}
          onChange={(value) => setOtpValue(value)}
          otp
          manageFocus
        >
          <PinInputField
            bg="bg.input"
            border="2px solid"
            borderColor="border.input"
            borderRadius="xl"
            _focus={{ borderColor: "brand.400", bg: "bg.card" }}
            fontWeight="700"
            fontSize="xl"
            w="52px"
            h="56px"
          />
          <PinInputField
            bg="bg.input"
            border="2px solid"
            borderColor="border.input"
            borderRadius="xl"
            _focus={{ borderColor: "brand.400", bg: "bg.card" }}
            fontWeight="700"
            fontSize="xl"
            w="52px"
            h="56px"
          />
          <PinInputField
            bg="bg.input"
            border="2px solid"
            borderColor="border.input"
            borderRadius="xl"
            _focus={{ borderColor: "brand.400", bg: "bg.card" }}
            fontWeight="700"
            fontSize="xl"
            w="52px"
            h="56px"
          />
          <PinInputField
            bg="bg.input"
            border="2px solid"
            borderColor="border.input"
            borderRadius="xl"
            _focus={{ borderColor: "brand.400", bg: "bg.card" }}
            fontWeight="700"
            fontSize="xl"
            w="52px"
            h="56px"
          />
          <PinInputField
            bg="bg.input"
            border="2px solid"
            borderColor="border.input"
            borderRadius="xl"
            _focus={{ borderColor: "brand.400", bg: "bg.card" }}
            fontWeight="700"
            fontSize="xl"
            w="52px"
            h="56px"
          />
          <PinInputField
            bg="bg.input"
            border="2px solid"
            borderColor="border.input"
            borderRadius="xl"
            _focus={{ borderColor: "brand.400", bg: "bg.card" }}
            fontWeight="700"
            fontSize="xl"
            w="52px"
            h="56px"
          />
        </PinInput>
      </HStack>

      <Button
        id="verify-otp-button"
        w="full"
        size="lg"
        bg="linear-gradient(135deg, #5A67D8 0%, #667EEA 100%)"
        color="white"
        fontWeight="700"
        borderRadius="xl"
        fontSize="md"
        _hover={{
          bg: "linear-gradient(135deg, #4C51BF 0%, #5A67D8 100%)",
          transform: "translateY(-2px)",
          boxShadow: "0 8px 25px rgba(90, 103, 216, 0.35)",
        }}
        _active={{ transform: "translateY(0)" }}
        transition="all 0.25s ease"
        onClick={handleVerifyOtp}
        isLoading={isLoading}
        loadingText="Verifying..."
        rightIcon={<FiCheck />}
      >
        Verify & Continue
      </Button>

      <HStack spacing={1} justify="center">
        <Text fontSize="sm" color="text.muted">
          Didn&apos;t receive the code?
        </Text>
        {resendCooldown > 0 ? (
          <Text fontSize="sm" color="text.dimmed" fontWeight="500">
            Resend in {resendCooldown}s
          </Text>
        ) : (
          <Text
            as="button"
            fontSize="sm"
            color="brand.500"
            fontWeight="600"
            cursor="pointer"
            _hover={{ color: "brand.700", textDecoration: "underline" }}
            onClick={handleResendOtp}
            display="flex"
            alignItems="center"
            gap="4px"
          >
            <Icon as={FiRefreshCw} boxSize={3} /> Resend OTP
          </Text>
        )}
      </HStack>

      <Text
        fontSize="sm"
        color="brand.500"
        fontWeight="600"
        cursor="pointer"
        _hover={{ color: "brand.700", textDecoration: "underline" }}
        onClick={() => switchView("login")}
      >
        ← Back to Sign In
      </Text>
    </VStack>
  );

  const renderForgotForm = () => (
    <VStack spacing={5} w="full">
      <Flex
        w="72px"
        h="72px"
        borderRadius="full"
        bg="orange.50"
        align="center"
        justify="center"
        mx="auto"
      >
        <Icon as={FiMail} boxSize={8} color="orange.500" />
      </Flex>

      <Text fontSize="sm" color="text.muted" textAlign="center" lineHeight="1.6">
        Enter the email address associated with your account and we&apos;ll send you a link to reset your password.
      </Text>

      <FormControl isInvalid={!!errors.forgotEmail}>
        <FormLabel fontSize="sm" fontWeight="600" color="text.primary">
          Email Address
        </FormLabel>
        <InputGroup size="lg">
          <InputLeftElement pointerEvents="none">
            <Icon as={FiMail} color="text.dimmed" />
          </InputLeftElement>
          <Input
            id="forgot-email"
            type="email"
            placeholder="you@example.com"
            value={forgotEmail}
            onChange={(e) => setForgotEmail(e.target.value)}
            bg="bg.input"
            borderRadius="xl"
            border="2px solid"
            borderColor="transparent"
            _hover={{ bg: "bg.hover" }}
            _focus={{ bg: "bg.card", borderColor: "brand.400" }}
            fontSize="sm"
            pl="44px"
            onKeyDown={(e) => e.key === "Enter" && handleForgotPassword()}
          />
        </InputGroup>
        <FormErrorMessage fontSize="xs">{errors.forgotEmail}</FormErrorMessage>
      </FormControl>

      <Button
        id="forgot-password-button"
        w="full"
        size="lg"
        bg="linear-gradient(135deg, #5A67D8 0%, #667EEA 100%)"
        color="white"
        fontWeight="700"
        borderRadius="xl"
        fontSize="md"
        _hover={{
          bg: "linear-gradient(135deg, #4C51BF 0%, #5A67D8 100%)",
          transform: "translateY(-2px)",
          boxShadow: "0 8px 25px rgba(90, 103, 216, 0.35)",
        }}
        _active={{ transform: "translateY(0)" }}
        transition="all 0.25s ease"
        onClick={handleForgotPassword}
        isLoading={isLoading}
        loadingText="Sending..."
        rightIcon={<FiArrowRight />}
      >
        Send Reset Link
      </Button>

      <Text
        fontSize="sm"
        color="brand.500"
        fontWeight="600"
        cursor="pointer"
        _hover={{ color: "brand.700", textDecoration: "underline" }}
        onClick={() => switchView("login")}
      >
        ← Back to Sign In
      </Text>
    </VStack>
  );

  const renderResetForm = () => (
    <VStack spacing={5} w="full">
      <Flex
        w="72px"
        h="72px"
        borderRadius="full"
        bg="green.50"
        _dark={{ bg: "green.900" }}
        align="center"
        justify="center"
        mx="auto"
      >
        <Icon as={FiLock} boxSize={8} color="green.500" />
      </Flex>

      <Text fontSize="sm" color="text.muted" textAlign="center" lineHeight="1.6">
        Enter your new password below. Make sure it&apos;s at least 6 characters long.
      </Text>

      <FormControl isInvalid={!!errors.newPassword}>
        <FormLabel fontSize="sm" fontWeight="600" color="text.primary">
          New Password
        </FormLabel>
        <InputGroup size="lg">
          <InputLeftElement pointerEvents="none">
            <Icon as={FiLock} color="text.dimmed" />
          </InputLeftElement>
          <Input
            id="new-password"
            type={showPassword ? "text" : "password"}
            placeholder="Enter new password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            bg="bg.input"
            borderRadius="xl"
            border="2px solid"
            borderColor="transparent"
            _hover={{ bg: "bg.hover" }}
            _focus={{ bg: "bg.card", borderColor: "brand.400" }}
            fontSize="sm"
            pl="44px"
          />
          <InputRightElement cursor="pointer" onClick={() => setShowPassword(!showPassword)}>
            <Icon as={showPassword ? FiEyeOff : FiEye} color="text.dimmed" />
          </InputRightElement>
        </InputGroup>
        <FormErrorMessage fontSize="xs">{errors.newPassword}</FormErrorMessage>
      </FormControl>

      <FormControl isInvalid={!!errors.confirmNewPassword}>
        <FormLabel fontSize="sm" fontWeight="600" color="text.primary">
          Confirm New Password
        </FormLabel>
        <InputGroup size="lg">
          <InputLeftElement pointerEvents="none">
            <Icon as={FiLock} color="text.dimmed" />
          </InputLeftElement>
          <Input
            id="confirm-new-password"
            type={showConfirmPassword ? "text" : "password"}
            placeholder="Confirm new password"
            value={confirmNewPassword}
            onChange={(e) => setConfirmNewPassword(e.target.value)}
            bg="bg.input"
            borderRadius="xl"
            border="2px solid"
            borderColor="transparent"
            _hover={{ bg: "bg.hover" }}
            _focus={{ bg: "bg.card", borderColor: "brand.400" }}
            fontSize="sm"
            pl="44px"
            onKeyDown={(e) => e.key === "Enter" && handleResetPassword()}
          />
          <InputRightElement cursor="pointer" onClick={() => setShowConfirmPassword(!showConfirmPassword)}>
            <Icon as={showConfirmPassword ? FiEyeOff : FiEye} color="text.dimmed" />
          </InputRightElement>
        </InputGroup>
        <FormErrorMessage fontSize="xs">{errors.confirmNewPassword}</FormErrorMessage>
      </FormControl>

      <Button
        id="reset-password-button"
        w="full"
        size="lg"
        bg="linear-gradient(135deg, #38A169 0%, #48BB78 100%)"
        color="white"
        fontWeight="700"
        borderRadius="xl"
        fontSize="md"
        _hover={{
          bg: "linear-gradient(135deg, #2F855A 0%, #38A169 100%)",
          transform: "translateY(-2px)",
          boxShadow: "0 8px 25px rgba(56, 161, 105, 0.35)",
        }}
        _active={{ transform: "translateY(0)" }}
        transition="all 0.25s ease"
        onClick={handleResetPassword}
        isLoading={isLoading}
        loadingText="Resetting..."
        rightIcon={<FiCheck />}
      >
        Reset Password
      </Button>

      <Text
        fontSize="sm"
        color="brand.500"
        fontWeight="600"
        cursor="pointer"
        _hover={{ color: "brand.700", textDecoration: "underline" }}
        onClick={() => switchView("login")}
      >
        ← Back to Sign In
      </Text>
    </VStack>
  );

  // ──── Main Render ──────────────────────────────────────────────
  return (
    <Flex minH="100vh" bg="bg.page">
      {/* ── Left Panel · Brand Showcase ── */}
      <Flex
        display={{ base: "none", lg: "flex" }}
        w="50%"
        bg="linear-gradient(135deg, #1A1A2E 0%, #3C366B 35%, #5A67D8 100%)"
        position="relative"
        overflow="hidden"
        direction="column"
        justify="center"
        align="center"
        p={16}
      >
        {/* Floating decorative shapes */}
        <Box
          position="absolute"
          top="-80px"
          left="-60px"
          w="300px"
          h="300px"
          borderRadius="full"
          bg="whiteAlpha.50"
          style={{ animation: "float 8s ease-in-out infinite" }}
        />
        <Box
          position="absolute"
          bottom="-100px"
          right="-40px"
          w="350px"
          h="350px"
          borderRadius="full"
          bg="whiteAlpha.50"
          style={{ animation: "float 10s ease-in-out infinite reverse" }}
        />
        <Box
          position="absolute"
          top="40%"
          right="15%"
          w="120px"
          h="120px"
          borderRadius="2xl"
          bg="whiteAlpha.100"
          transform="rotate(45deg)"
          style={{ animation: "float 6s ease-in-out infinite" }}
        />
        {/* Grid pattern overlay */}
        <Box
          position="absolute"
          inset={0}
          backgroundImage="radial-gradient(circle at 1px 1px, rgba(255,255,255,0.05) 1px, transparent 0)"
          backgroundSize="40px 40px"
        />

        {/* Content */}
        <VStack spacing={8} zIndex={1} maxW="480px" textAlign="center">
          <Flex
            w="80px"
            h="80px"
            borderRadius="2xl"
            bg="whiteAlpha.200"
            backdropFilter="blur(12px)"
            align="center"
            justify="center"
            boxShadow="0 8px 32px rgba(0,0,0,0.2)"
          >
            <Icon as={FiShield} boxSize={10} color="white" />
          </Flex>

          <VStack spacing={3}>
            <Text
              fontSize="4xl"
              fontWeight="900"
              color="white"
              lineHeight="1.1"
              letterSpacing="-0.02em"
            >
              ClaimAssist AI
            </Text>
            <Text
              fontSize="lg"
              color="whiteAlpha.800"
              fontWeight="400"
              lineHeight="1.7"
            >
              Your AI-powered companion for automated health insurance claim
              appeal generation
            </Text>
          </VStack>
        </VStack>
      </Flex>

      {/* ── Right Panel · Auth Form ── */}
      <Flex
        w={{ base: "100%", lg: "50%" }}
        justify="center"
        align="center"
        p={{ base: 6, md: 12 }}
      >
        <Box
          w="full"
          maxW="440px"
          className="animate-fade-in-up"
        >
          {/* Mobile logo */}
          <Flex
            display={{ base: "flex", lg: "none" }}
            align="center"
            gap={3}
            mb={8}
            justify="center"
          >
            <Flex
              w="42px"
              h="42px"
              borderRadius="xl"
              bg="brand.500"
              align="center"
              justify="center"
              boxShadow="0 2px 8px rgba(90, 103, 216, 0.3)"
            >
              <Icon as={FiShield} color="white" boxSize={5} />
            </Flex>
            <Text fontSize="xl" fontWeight="800" color="brand.500">
              ClaimAssist AI
            </Text>
          </Flex>

          {/* Card */}
          <Box
            bg="bg.card"
            borderRadius="2xl"
            boxShadow="0 4px 24px rgba(0, 0, 0, 0.06)"
            border="1px solid"
            borderColor="border.card"
            p={{ base: 7, md: 10 }}
          >
            {/* Header */}
            <VStack spacing={2} mb={8}>
              <Text
                fontSize="2xl"
                fontWeight="800"
                color="text.primary"
                letterSpacing="-0.01em"
              >
                {view === "login"
                  ? "Welcome Back"
                  : view === "signup"
                  ? "Create Account"
                  : view === "forgot"
                  ? "Forgot Password"
                  : view === "reset"
                  ? "Reset Password"
                  : "Email Verification"}
              </Text>
              <Text fontSize="sm" color="text.muted" textAlign="center">
                {view === "login"
                  ? "Sign in to continue to your dashboard"
                  : view === "signup"
                  ? "Sign up to start managing your insurance claims"
                  : view === "forgot"
                  ? "Enter your email to receive a reset link"
                  : view === "reset"
                  ? "Set a new password for your account"
                  : "Enter the verification code to secure your account"}
              </Text>
            </VStack>

            {/* Forms */}
            {view === "login" && renderLoginForm()}
            {view === "signup" && renderSignupForm()}
            {view === "otp" && renderOtpForm()}
            {view === "forgot" && renderForgotForm()}
            {view === "reset" && renderResetForm()}
          </Box>

          {/* Footer */}
          <Text
            fontSize="xs"
            color="text.dimmed"
            textAlign="center"
            mt={6}
          >
            © 2026 ClaimAssist AI. Secured with end-to-end encryption.
          </Text>
        </Box>
      </Flex>

    </Flex>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <LoginPageContent />
    </Suspense>
  );
}
