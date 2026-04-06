import { useEffect, useState } from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import FormControlLabel from '@mui/material/FormControlLabel';
import MenuItem from '@mui/material/MenuItem';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import Switch from '@mui/material/Switch';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';

export default function QuickGeneratePanel({ templates, onRun }) {
  const [name, setName] = useState('imperial');
  const [template, setTemplate] = useState('balanced');
  const [bootstrap, setBootstrap] = useState(true);
  const [storageDir, setStorageDir] = useState('src/languages');

  useEffect(() => {
    if (!templates.length) {
      return;
    }
    if (!templates.includes(template)) {
      setTemplate(templates[0]);
    }
  }, [template, templates]);

  const handleCreate = async () => {
    await onRun('Quick generate language', 'create_language', {
      name,
      template,
      bootstrap,
      storageDir,
      overrides: {},
    }, { refreshLanguages: true });
  };

  return (
    <Paper sx={{ p: 2.25 }}>
      <Stack spacing={2}>
        <Box>
          <Typography variant="h6">Quick Generate</Typography>
          <Typography variant="body2" color="text.secondary">
            Pick a template and generate a complete language instantly. Skip customization sections and start creating.
          </Typography>
        </Box>

        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
          <TextField
            fullWidth
            label="Language Name"
            value={name}
            onChange={(event) => setName(event.target.value)}
          />
          <TextField
            fullWidth
            select
            label="Template"
            value={template}
            onChange={(event) => setTemplate(event.target.value)}
          >
            {templates.map((item) => (
              <MenuItem key={item} value={item}>
                {item}
              </MenuItem>
            ))}
          </TextField>
        </Stack>

        <TextField
          fullWidth
          label="Storage Directory"
          value={storageDir}
          onChange={(event) => setStorageDir(event.target.value)}
        />

        <FormControlLabel
          control={<Switch checked={bootstrap} onChange={(event) => setBootstrap(event.target.checked)} />}
          label="Bootstrap core lexicon"
        />

        <Stack direction="row" spacing={1.5}>
          <Button variant="contained" onClick={handleCreate}>
            Generate Language
          </Button>
        </Stack>
      </Stack>
    </Paper>
  );
}
