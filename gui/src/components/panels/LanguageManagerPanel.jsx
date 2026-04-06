import { useEffect, useMemo, useState } from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import FormControlLabel from '@mui/material/FormControlLabel';
import Grid from '@mui/material/Grid';
import List from '@mui/material/List';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemText from '@mui/material/ListItemText';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import Switch from '@mui/material/Switch';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';

import ThinScrollbar from '../ThinScrollbar';

function fileNameFromPath(path) {
  const value = String(path || '');
  const parts = value.split(/[/\\]/);
  return parts[parts.length - 1] || value;
}

export default function LanguageManagerPanel({ templates, languages, onRun }) {
  const [storageDir, setStorageDir] = useState('src/languages');
  const [languageRef, setLanguageRef] = useState('');

  const [name, setName] = useState('');
  const [templateName, setTemplateName] = useState('');
  const [stylePreset, setStylePreset] = useState('');
  const [renameFile, setRenameFile] = useState(true);

  const [deleteConfirm, setDeleteConfirm] = useState('');

  const languageOptions = useMemo(() => {
    return languages.map((item) => ({
      value: item.path,
      name: item.name,
      style: item.style,
      template: item.template,
      path: item.path,
    }));
  }, [languages]);

  const selectedLanguage = useMemo(() => {
    return languageOptions.find((item) => item.value === languageRef) || null;
  }, [languageOptions, languageRef]);

  useEffect(() => {
    if (!languageOptions.length) {
      setLanguageRef('');
      setName('');
      setTemplateName('');
      setStylePreset('');
      setDeleteConfirm('');
      return;
    }

    const exists = languageOptions.some((item) => item.value === languageRef);
    const target = exists ? languageRef : languageOptions[0].value;
    const language = languageOptions.find((item) => item.value === target);

    if (target !== languageRef) {
      setLanguageRef(target);
    }

    if (language) {
      setName(language.name || '');
      setTemplateName(language.template || '');
      setStylePreset(language.style || '');
      setDeleteConfirm('');
    }
  }, [languageOptions, languageRef]);

  const handleSelectLanguage = (path) => {
    setLanguageRef(path);
    const language = languageOptions.find((item) => item.value === path);
    if (language) {
      setName(language.name || '');
      setTemplateName(language.template || '');
      setStylePreset(language.style || '');
      setDeleteConfirm('');
    }
  };

  const handleRefresh = async () => {
    await onRun(
      'Refresh language inventory',
      'list_languages',
      { storageDir },
      { refreshLanguages: true, languagesStorageDir: storageDir },
    );
  };

  const handleLoadDetails = async () => {
    if (!languageRef) {
      return;
    }
    await onRun('Load language details', 'load_language', { storageDir, language: languageRef });
  };

  const handleSaveChanges = async () => {
    if (!languageRef) {
      return;
    }

    await onRun(
      'Update language metadata',
      'update_language',
      {
        storageDir,
        language: languageRef,
        updates: {
          name,
          template_name: templateName,
          style_preset: stylePreset,
        },
        renameFile,
      },
      { refreshLanguages: true, languagesStorageDir: storageDir },
    );
  };

  const canDelete = Boolean(selectedLanguage && deleteConfirm.trim() === selectedLanguage.name);

  const handleDelete = async () => {
    if (!languageRef || !canDelete) {
      return;
    }

    await onRun(
      'Delete language',
      'delete_language',
      { storageDir, language: languageRef },
      { refreshLanguages: true, languagesStorageDir: storageDir },
    );

    setDeleteConfirm('');
  };

  return (
    <Paper sx={{ p: 2.25 }}>
      <Stack spacing={2}>
        <Box>
          <Typography variant="h6">Language Manager</Typography>
          <Typography variant="body2" color="text.secondary">
            Browse all saved languages, inspect details, edit metadata, and delete unwanted files.
          </Typography>
        </Box>

        <Grid container spacing={2}>
          <Grid item xs={12} md={8}>
            <TextField
              fullWidth
              label="Storage Directory"
              value={storageDir}
              onChange={(event) => setStorageDir(event.target.value)}
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <Stack direction="row" spacing={1}>
              <Button variant="outlined" onClick={handleRefresh}>Refresh</Button>
              <Button variant="text" onClick={handleLoadDetails} disabled={!languageRef}>Load Details</Button>
            </Stack>
          </Grid>
        </Grid>

        <Box>
          <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
            <Typography variant="subtitle2">Saved Languages</Typography>
            <Chip size="small" label={`${languageOptions.length} total`} variant="outlined" />
          </Stack>

          <Paper sx={{ p: 1, bgcolor: 'background.default' }}>
            <ThinScrollbar sx={{ maxHeight: 250 }}>
              <List dense disablePadding>
                {languageOptions.map((item) => (
                  <ListItemButton
                    key={item.value}
                    selected={item.value === languageRef}
                    onClick={() => handleSelectLanguage(item.value)}
                    sx={{ borderRadius: 1 }}
                  >
                    <ListItemText
                      primary={item.name}
                      secondary={`${item.style} • ${item.template}`}
                    />
                    <Chip size="small" variant="outlined" label={fileNameFromPath(item.path)} />
                  </ListItemButton>
                ))}
              </List>
            </ThinScrollbar>
          </Paper>
        </Box>

        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Display Name"
              value={name}
              onChange={(event) => setName(event.target.value)}
              disabled={!selectedLanguage}
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Language File"
              value={selectedLanguage ? fileNameFromPath(selectedLanguage.path) : ''}
              disabled
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Template Name"
              value={templateName}
              onChange={(event) => setTemplateName(event.target.value)}
              disabled={!selectedLanguage}
              helperText={templates.length ? `Known templates: ${templates.slice(0, 6).join(', ')}${templates.length > 6 ? '...' : ''}` : ''}
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Style Preset"
              value={stylePreset}
              onChange={(event) => setStylePreset(event.target.value)}
              disabled={!selectedLanguage}
            />
          </Grid>
          <Grid item xs={12}>
            <FormControlLabel
              control={<Switch checked={renameFile} onChange={(event) => setRenameFile(event.target.checked)} />}
              label="Rename file when display name changes"
            />
          </Grid>
        </Grid>

        <Stack direction="row" spacing={1.5}>
          <Button variant="outlined" onClick={handleSaveChanges} disabled={!selectedLanguage}>Save Changes</Button>
        </Stack>

        <Paper sx={{ p: 1.5, bgcolor: 'background.default' }}>
          <Stack spacing={1.25}>
            <Typography variant="subtitle2">Delete Language</Typography>
            <Typography variant="body2" color="text.secondary">
              Type the selected language name exactly to enable deletion.
            </Typography>
            <TextField
              fullWidth
              label="Confirm Name"
              value={deleteConfirm}
              onChange={(event) => setDeleteConfirm(event.target.value)}
              disabled={!selectedLanguage}
            />
            <Stack direction="row" spacing={1.5}>
              <Button variant="outlined" color="error" onClick={handleDelete} disabled={!canDelete}>
                Delete Language
              </Button>
            </Stack>
          </Stack>
        </Paper>
      </Stack>
    </Paper>
  );
}
