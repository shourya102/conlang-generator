import { useEffect, useMemo, useState } from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Grid from '@mui/material/Grid';
import MenuItem from '@mui/material/MenuItem';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';

export default function EvaluatorPanel({ languages, onRun }) {
  const [storageDir, setStorageDir] = useState('src/languages');
  const [languageRef, setLanguageRef] = useState('');
  const [count, setCount] = useState('40');
  const [minScore, setMinScore] = useState('58');
  const [minSyllables, setMinSyllables] = useState('1');
  const [maxSyllables, setMaxSyllables] = useState('4');

  const languageOptions = useMemo(() => {
    return languages.map((item) => ({
      label: `${item.name} (${item.style})`,
      value: item.path,
    }));
  }, [languages]);

  useEffect(() => {
    if (!languageOptions.length) {
      setLanguageRef('');
      return;
    }

    const exists = languageOptions.some((item) => item.value === languageRef);
    if (!exists) {
      setLanguageRef(languageOptions[0].value);
    }
  }, [languageOptions, languageRef]);

  const runEvaluate = async () => {
    await onRun('Evaluate pronounceability', 'evaluate', {
      storageDir,
      language: languageRef,
      count: Number(count || 40),
      minScore: Number(minScore || 58),
      minSyllables: Number(minSyllables || 1),
      maxSyllables: Number(maxSyllables || 4),
    });
  };

  return (
    <Paper sx={{ p: 2.25 }}>
      <Stack spacing={2}>
        <Box>
          <Typography variant="h6">Evaluator</Typography>
          <Typography variant="body2" color="text.secondary">
            Score generated outputs for pronounceability and quickly inspect acceptance quality.
          </Typography>
        </Box>

        <Grid container spacing={2}>
          <Grid item xs={12} md={8}>
            <TextField fullWidth select label="Language" value={languageRef} onChange={(event) => setLanguageRef(event.target.value)}>
              {languageOptions.map((item) => (
                <MenuItem key={item.value} value={item.value}>{item.label}</MenuItem>
              ))}
            </TextField>
          </Grid>
          <Grid item xs={12} md={4}>
            <TextField fullWidth label="Storage Directory" value={storageDir} onChange={(event) => setStorageDir(event.target.value)} />
          </Grid>
          <Grid item xs={12} md={3}><TextField fullWidth label="Count" value={count} onChange={(event) => setCount(event.target.value)} /></Grid>
          <Grid item xs={12} md={3}><TextField fullWidth label="Min Score" value={minScore} onChange={(event) => setMinScore(event.target.value)} /></Grid>
          <Grid item xs={12} md={3}><TextField fullWidth label="Min Syllables" value={minSyllables} onChange={(event) => setMinSyllables(event.target.value)} /></Grid>
          <Grid item xs={12} md={3}><TextField fullWidth label="Max Syllables" value={maxSyllables} onChange={(event) => setMaxSyllables(event.target.value)} /></Grid>
        </Grid>

        <Stack direction="row" spacing={1.5}>
          <Button variant="contained" onClick={runEvaluate} disabled={!languageRef}>Run Evaluator</Button>
        </Stack>
      </Stack>
    </Paper>
  );
}
