import Box from '@mui/material/Box';

export default function ThinScrollbar({ children, sx, className = '' }) {
  return (
    <Box className={`thin-scrollbar ${className}`.trim()} sx={{ minHeight: 0, minWidth: 0, overflow: 'auto', ...sx }}>
      {children}
    </Box>
  );
}
