"use client";

import { extendTheme, type ThemeConfig } from "@chakra-ui/react";
import { mode, type StyleFunctionProps } from "@chakra-ui/theme-tools";

const config: ThemeConfig = {
  initialColorMode: "light",
  useSystemColorMode: false,
};

const theme = extendTheme({
  config,
  colors: {
    brand: {
      50: "#EBF4FF",
      100: "#C3DAFE",
      200: "#A3BFFA",
      300: "#7F9CF5",
      400: "#667EEA",
      500: "#5A67D8",
      600: "#4C51BF",
      700: "#434190",
      800: "#3C366B",
      900: "#1A1A2E",
    },
    accent: {
      50: "#FFF5F5",
      100: "#FED7D7",
      200: "#FEB2B2",
      300: "#FC8181",
      400: "#F56565",
      500: "#E53E3E",
    },
    success: {
      50: "#F0FFF4",
      100: "#C6F6D5",
      400: "#48BB78",
      500: "#38A169",
    },
    warning: {
      50: "#FFFBEB",
      100: "#FEF3C7",
      400: "#F6AD55",
      500: "#ED8936",
    },
    surface: {
      50: "#FAFBFF",
      100: "#F4F6FC",
      200: "#EDF0F7",
      300: "#E2E8F0",
    },
    // Dark mode surface colors
    dark: {
      bg: "#0F1117",
      card: "#1A1B2E",
      sidebar: "#12131F",
      input: "#1E1F33",
      hover: "#252640",
      elevated: "#222338",
    },
  },
  semanticTokens: {
    colors: {
      // Page backgrounds
      "bg.page":      { default: "surface.50",  _dark: "#0F1117" },
      "bg.card":      { default: "white",       _dark: "#1A1B2E" },
      "bg.sidebar":   { default: "white",       _dark: "#12131F" },
      "bg.input":     { default: "surface.100", _dark: "#1E1F33" },
      "bg.hover":     { default: "gray.50",     _dark: "#252640" },
      "bg.elevated":  { default: "white",       _dark: "#222338" },
      "bg.accent":    { default: "brand.50",    _dark: "brand.900" },
      "bg.accentHover": { default: "brand.50",  _dark: "brand.800" },

      // Text colors
      "text.primary":   { default: "gray.800", _dark: "gray.100" },
      "text.secondary": { default: "gray.600", _dark: "gray.300" },
      "text.muted":     { default: "gray.500", _dark: "gray.400" },
      "text.dimmed":    { default: "gray.400", _dark: "gray.500" },

      // Border colors
      "border.card":    { default: "gray.100", _dark: "gray.700" },
      "border.input":   { default: "gray.200", _dark: "gray.600" },
      "border.subtle":  { default: "gray.50",  _dark: "gray.800" },

      // Sidebar
      "sidebar.activeBg":   { default: "brand.50",  _dark: "brand.900" },
      "sidebar.activeText":  { default: "brand.600", _dark: "brand.200" },
      "sidebar.hoverBg":    { default: "gray.50",   _dark: "#252640" },
      "sidebar.hoverText":  { default: "gray.800",  _dark: "gray.100" },

      // Component specific
      "statsCard.bg":       { default: "white",       _dark: "#1A1B2E" },
      "statsCard.overlay":  { default: "brand.50",    _dark: "brand.900" },
      "chat.bg":            { default: "white",       _dark: "#1A1B2E" },
      "chat.inputBg":       { default: "surface.100", _dark: "#1E1F33" },
    },
  },
  fonts: {
    heading: `'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif`,
    body: `'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif`,
  },
  styles: {
    global: (props: StyleFunctionProps) => ({
      "html, body": {
        bg: mode("surface.50", "#0F1117")(props),
        color: mode("gray.800", "gray.100")(props),
        lineHeight: "tall",
      },
      "*::placeholder": {
        color: mode("gray.400", "gray.500")(props),
      },
      "::selection": {
        bg: mode("brand.100", "brand.800")(props),
        color: mode("brand.800", "brand.100")(props),
      },
    }),
  },
  components: {
    Button: {
      baseStyle: {
        fontWeight: "600",
        borderRadius: "xl",
        transition: "all 0.2s ease-in-out",
      },
      variants: {
        primary: () => ({
          bg: "brand.500",
          color: "white",
          _hover: {
            bg: "brand.600",
            transform: "translateY(-1px)",
            boxShadow: "lg",
          },
          _active: {
            bg: "brand.700",
            transform: "translateY(0)",
          },
        }),
        secondary: (props: StyleFunctionProps) => ({
          bg: mode("white", "#1A1B2E")(props),
          color: "brand.600",
          border: "2px solid",
          borderColor: mode("brand.200", "brand.700")(props),
          _hover: {
            bg: mode("brand.50", "brand.900")(props),
            borderColor: "brand.400",
            transform: "translateY(-1px)",
          },
        }),
        ghost: (props: StyleFunctionProps) => ({
          color: mode("gray.600", "gray.300")(props),
          _hover: {
            bg: mode("brand.50", "brand.900")(props),
            color: mode("brand.600", "brand.200")(props),
          },
        }),
      },
      defaultProps: {
        variant: "primary",
      },
    },
    Card: {
      baseStyle: (props: StyleFunctionProps) => ({
        container: {
          bg: mode("white", "#1A1B2E")(props),
          borderRadius: "2xl",
          boxShadow: "0 1px 3px 0 rgba(0, 0, 0, 0.04), 0 1px 2px -1px rgba(0, 0, 0, 0.04)",
          border: "1px solid",
          borderColor: mode("gray.100", "gray.700")(props),
          transition: "all 0.2s ease-in-out",
          _hover: {
            boxShadow: "0 4px 12px 0 rgba(90, 103, 216, 0.08)",
            borderColor: mode("brand.100", "brand.700")(props),
          },
        },
      }),
    },
    Badge: {
      variants: {
        subtle: {
          borderRadius: "full",
          px: 3,
          py: 1,
          fontWeight: "600",
          fontSize: "xs",
        },
      },
    },
    Input: {
      baseStyle: (props: StyleFunctionProps) => ({
        field: {
          color: mode("gray.800", "gray.100")(props),
        },
      }),
      variants: {
        filled: (props: StyleFunctionProps) => ({
          field: {
            bg: mode("surface.100", "#1E1F33")(props),
            color: mode("gray.800", "gray.100")(props),
            borderRadius: "xl",
            border: "2px solid",
            borderColor: "transparent",
            _hover: {
              bg: mode("surface.200", "#252640")(props),
            },
            _focus: {
              bg: mode("white", "#1A1B2E")(props),
              borderColor: "brand.400",
            },
            _placeholder: {
              color: mode("gray.400", "gray.500")(props),
            },
          },
        }),
      },
      defaultProps: {
        variant: "filled",
      },
    },
    Textarea: {
      variants: {
        filled: (props: StyleFunctionProps) => ({
          bg: mode("surface.100", "#1E1F33")(props),
          color: mode("gray.800", "gray.100")(props),
          borderRadius: "xl",
          border: "2px solid",
          borderColor: "transparent",
          _hover: {
            bg: mode("surface.200", "#252640")(props),
          },
          _focus: {
            bg: mode("white", "#1A1B2E")(props),
            borderColor: "brand.400",
          },
          _placeholder: {
            color: mode("gray.400", "gray.500")(props),
          },
        }),
      },
    },
    Table: {
      variants: {
        simple: (props: StyleFunctionProps) => ({
          th: {
            color: mode("gray.500", "gray.400")(props),
            borderColor: mode("gray.100", "gray.700")(props),
          },
          td: {
            borderColor: mode("gray.100", "gray.700")(props),
          },
          tr: {
            _hover: {
              bg: mode("gray.50", "#252640")(props),
            },
          },
        }),
      },
    },
    Divider: {
      baseStyle: (props: StyleFunctionProps) => ({
        borderColor: mode("gray.100", "gray.700")(props),
      }),
    },
    Modal: {
      baseStyle: (props: StyleFunctionProps) => ({
        dialog: {
          bg: mode("white", "#1A1B2E")(props),
        },
      }),
    },
    Accordion: {
      baseStyle: (props: StyleFunctionProps) => ({
        button: {
          _hover: {
            bg: mode("brand.50", "brand.900")(props),
          },
        },
      }),
    },
  },
  shadows: {
    brand: "0 4px 14px 0 rgba(90, 103, 216, 0.25)",
    card: "0 1px 3px 0 rgba(0, 0, 0, 0.04), 0 1px 2px -1px rgba(0, 0, 0, 0.04)",
    cardHover: "0 4px 12px 0 rgba(90, 103, 216, 0.1)",
  },
  radii: {
    card: "1rem",
  },
});

export default theme;
