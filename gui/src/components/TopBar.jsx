import { useEffect, useMemo, useState } from 'react';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import Tooltip from '@mui/material/Tooltip';
import RemoveIcon from '@mui/icons-material/Remove';
import CropSquareIcon from '@mui/icons-material/CropSquare';
import FilterNoneIcon from '@mui/icons-material/FilterNone';
import CloseIcon from '@mui/icons-material/Close';
import PaletteIcon from '@mui/icons-material/Palette';

import { windowControls } from '../lib/bridge';

export default function TopBar({ themeId, onThemeChange, themes }) {
  const [isMaximized, setIsMaximized] = useState(false);

  useEffect(() => {
    let mounted = true;
    windowControls.isMaximized().then((value) => {
      if (mounted) {
        setIsMaximized(Boolean(value));
      }
    });
    return () => {
      mounted = false;
    };
  }, []);

  const maximizeIcon = useMemo(() => {
    if (isMaximized) {
      return <FilterNoneIcon fontSize="small" />;
    }
    return <CropSquareIcon fontSize="small" />;
  }, [isMaximized]);

  const handleToggleMaximize = async () => {
    const value = await windowControls.toggleMaximize();
    setIsMaximized(Boolean(value));
  };

  return (
    <Box className="title-bar" sx={{ px: 1.25, gap: 1, bgcolor: 'background.paper' }}>
      <Stack direction="row" spacing={1} alignItems="center" sx={{ flex: 1 }}>
        <Box sx={{ width: 10, height: 10, borderRadius: 999, bgcolor: 'primary.main', boxShadow: 1 }} />
        <Typography variant="subtitle2" sx={{ letterSpacing: 0.35 }}>
          Conlang Studio Desktop
        </Typography>
      </Stack>

      <Stack className="title-bar-no-drag" direction="row" spacing={1} alignItems="center">
        <PaletteIcon fontSize="small" sx={{ color: 'text.secondary' }} />
        <Select
          size="small"
          value={themeId}
          onChange={(event) => onThemeChange(event.target.value)}
          sx={{ minWidth: 168 }}
        >
          {themes.map((theme) => (
            <MenuItem key={theme.id} value={theme.id}>
              {theme.name}
            </MenuItem>
          ))}
        </Select>

        <Tooltip title="Minimize">
          <IconButton size="small" onClick={() => windowControls.minimize()}>
            <RemoveIcon fontSize="small" />
          </IconButton>
        </Tooltip>

        <Tooltip title={isMaximized ? 'Restore' : 'Maximize'}>
          <IconButton size="small" onClick={handleToggleMaximize}>
            {maximizeIcon}
          </IconButton>
        </Tooltip>

        <Tooltip title="Close">
          <IconButton size="small" color="error" onClick={() => windowControls.close()}>
            <CloseIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Stack>
    </Box>
  );
}
