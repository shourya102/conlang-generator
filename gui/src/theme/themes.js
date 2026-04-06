import { alpha, createTheme } from '@mui/material/styles';

export const themeCatalog = [
  {
    id: 'ember-editorial',
    name: 'Ember Editorial',
    palette: {
      mode: 'dark',
      primary: { main: '#d8834f' },
      secondary: { main: '#9e8f7f' },
      background: { default: '#141110', paper: '#1b1715' },
      text: { primary: '#f2ece6', secondary: '#b2a79c' },
      divider: 'rgba(216, 131, 79, 0.18)',
    },
    surface: {
      elevated: '#211c19',
      side: '#171412',
    },
  },
  {
    id: 'charcoal-ink',
    name: 'Charcoal Ink',
    palette: {
      mode: 'dark',
      primary: { main: '#c9784a' },
      secondary: { main: '#8b8278' },
      background: { default: '#101012', paper: '#17181c' },
      text: { primary: '#ece9e4', secondary: '#aca8a0' },
      divider: 'rgba(201, 120, 74, 0.18)',
    },
    surface: {
      elevated: '#1c1e22',
      side: '#15161a',
    },
  },
  {
    id: 'cocoa-night',
    name: 'Cocoa Night',
    palette: {
      mode: 'dark',
      primary: { main: '#d8834f' },
      secondary: { main: '#9b8b78' },
      background: { default: '#171311', paper: '#221a16' },
      text: { primary: '#f1e9e1', secondary: '#b8aa9e' },
      divider: 'rgba(216, 131, 79, 0.18)',
    },
    surface: {
      elevated: '#2a211c',
      side: '#1b1512',
    },
  },
  {
    id: 'dawn-ash',
    name: 'Dawn Ash',
    palette: {
      mode: 'dark',
      primary: { main: '#cf7d4b' },
      secondary: { main: '#968877' },
      background: { default: '#161212', paper: '#1f1a1a' },
      text: { primary: '#f2e8e2', secondary: '#b6a8a2' },
      divider: 'rgba(207, 125, 75, 0.18)',
    },
    surface: {
      elevated: '#272020',
      side: '#1a1515',
    },
  },
  {
    id: 'olive-manuscript',
    name: 'Olive Manuscript',
    palette: {
      mode: 'dark',
      primary: { main: '#cf8050' },
      secondary: { main: '#9b927f' },
      background: { default: '#121310', paper: '#191b16' },
      text: { primary: '#ecece5', secondary: '#acb0a0' },
      divider: 'rgba(207, 128, 80, 0.18)',
    },
    surface: {
      elevated: '#20231d',
      side: '#171914',
    },
  },
];

export function createAppTheme(themeId) {
  const selected = themeCatalog.find((theme) => theme.id === themeId) ?? themeCatalog[0];
  const dividerStrong = alpha(selected.palette.text.primary, 0.14);
  const dividerSoft = alpha(selected.palette.text.primary, 0.08);
  const focusSoft = alpha(selected.palette.primary.main, 0.42);

  return createTheme({
    palette: {
      ...selected.palette,
      surface: selected.surface,
    },
    shape: {
      borderRadius: 10,
    },
    typography: {
      fontFamily: '"Segoe UI Variable", "Segoe UI", "Noto Sans", sans-serif',
      h5: { fontWeight: 600, letterSpacing: 0.2 },
      h6: { fontWeight: 600, letterSpacing: 0.18 },
      subtitle1: { fontWeight: 600, letterSpacing: 0.14 },
      subtitle2: { fontWeight: 600, letterSpacing: 0.12 },
      body1: { lineHeight: 1.55 },
      body2: { lineHeight: 1.55 },
      button: { textTransform: 'none', fontWeight: 600, letterSpacing: 0.2 },
    },
    components: {
      MuiCssBaseline: {
        styleOverrides: {
          body: {
            backgroundColor: selected.palette.background.default,
          },
          '::selection': {
            backgroundColor: alpha(selected.palette.primary.main, 0.28),
          },
        },
      },
      MuiButtonBase: {
        defaultProps: {
          disableRipple: true,
          disableTouchRipple: true,
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            boxShadow: `0 1px 0 ${dividerSoft}`,
            border: 'none',
            backgroundImage: 'none',
          },
        },
      },
      MuiDivider: {
        styleOverrides: {
          root: {
            borderColor: dividerSoft,
          },
        },
      },
      MuiTab: {
        styleOverrides: {
          root: {
            minHeight: 42,
            padding: '0 18px',
            color: alpha(selected.palette.text.secondary, 0.82),
            fontWeight: 500,
            transition: 'color 120ms ease, opacity 120ms ease',
            '&.Mui-selected': {
              color: selected.palette.text.primary,
            },
          },
        },
      },
      MuiButton: {
        styleOverrides: {
          root: {
            borderRadius: 9,
            boxShadow: 'none',
            transition: 'background-color 120ms ease, border-color 120ms ease, opacity 120ms ease',
            '&:focus-visible': {
              outline: `1px solid ${focusSoft}`,
              outlineOffset: 1,
            },
          },
          contained: {
            backgroundColor: selected.palette.primary.main,
            color: selected.palette.background.default,
            '&:hover': {
              backgroundColor: alpha(selected.palette.primary.main, 0.9),
            },
            '&:active': {
              opacity: 0.92,
            },
          },
          outlined: {
            borderColor: dividerStrong,
            color: selected.palette.text.secondary,
            '&:hover': {
              borderColor: alpha(selected.palette.text.primary, 0.26),
              backgroundColor: alpha(selected.palette.text.primary, 0.04),
            },
          },
          text: {
            color: selected.palette.text.secondary,
            '&:hover': {
              backgroundColor: alpha(selected.palette.text.primary, 0.06),
            },
          },
        },
      },
      MuiTabs: {
        styleOverrides: {
          root: {
            minHeight: 42,
            borderBottom: `1px solid ${dividerSoft}`,
          },
          indicator: {
            height: 2,
            borderRadius: 999,
            backgroundColor: selected.palette.primary.main,
          },
          scrollButtons: {
            color: selected.palette.text.secondary,
            '&.Mui-disabled': {
              opacity: 0.24,
            },
          },
        },
      },
      MuiAccordion: {
        styleOverrides: {
          root: {
            border: 'none',
            boxShadow: 'none',
            backgroundColor: selected.surface.elevated,
            '&::before': {
              display: 'none',
            },
            '&.Mui-expanded': {
              margin: 0,
            },
            '& + &': {
              marginTop: 10,
            },
          },
        },
      },
      MuiAccordionSummary: {
        styleOverrides: {
          root: {
            minHeight: 56,
            paddingLeft: 18,
            paddingRight: 12,
            '&.Mui-expanded': {
              minHeight: 56,
            },
          },
          content: {
            marginTop: 14,
            marginBottom: 14,
            '&.Mui-expanded': {
              marginTop: 14,
              marginBottom: 14,
            },
            '& .MuiTypography-root': {
              fontWeight: 600,
            },
          },
        },
      },
      MuiAccordionDetails: {
        styleOverrides: {
          root: {
            padding: '4px 18px 18px',
          },
        },
      },
      MuiOutlinedInput: {
        styleOverrides: {
          root: {
            backgroundColor: alpha(selected.palette.background.default, 0.36),
            '& .MuiOutlinedInput-notchedOutline': {
              borderColor: dividerStrong,
            },
            '&:hover .MuiOutlinedInput-notchedOutline': {
              borderColor: alpha(selected.palette.text.primary, 0.3),
            },
            '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
              borderColor: focusSoft,
              borderWidth: 1,
            },
          },
          input: {
            '&::placeholder': {
              color: alpha(selected.palette.text.secondary, 0.7),
            },
          },
        },
      },
      MuiTextField: {
        defaultProps: {
          size: 'small',
          variant: 'outlined',
        },
      },
      MuiMenu: {
        styleOverrides: {
          paper: {
            backgroundColor: selected.surface.elevated,
            border: `1px solid ${dividerSoft}`,
          },
        },
      },
      MuiChip: {
        styleOverrides: {
          root: {
            borderColor: dividerStrong,
          },
        },
      },
    },
  });
}
