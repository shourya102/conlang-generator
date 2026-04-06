import { useEffect, useMemo, useState } from 'react';
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import FormControlLabel from '@mui/material/FormControlLabel';
import Grid from '@mui/material/Grid';
import MenuItem from '@mui/material/MenuItem';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import Switch from '@mui/material/Switch';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

export default function OperationsPanel({ templates, languages, soundPresets, onRun }) {
  const [storageDir, setStorageDir] = useState('src/languages');
  const [languageRef, setLanguageRef] = useState('');

  const [translationText, setTranslationText] = useState('The emperor commands the legions at dawn.');
  const [useGrammar, setUseGrammar] = useState(true);

  const [genKind, setGenKind] = useState('word');
  const [genCount, setGenCount] = useState('12');
  const [genCategory, setGenCategory] = useState('person');
  const [genGender, setGenGender] = useState('neutral');
  const [genNumber, setGenNumber] = useState('singular');
  const [genCase, setGenCase] = useState('core');
  const [genMinSyl, setGenMinSyl] = useState('1');
  const [genMaxSyl, setGenMaxSyl] = useState('4');
  const [genMinScore, setGenMinScore] = useState('58');

  const [derivePreset, setDerivePreset] = useState('lenition');
  const [deriveName, setDeriveName] = useState('');

  const [switchStyle, setSwitchStyle] = useState('balanced');
  const [regenerateLexicon, setRegenerateLexicon] = useState(false);

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

  useEffect(() => {
    if (!soundPresets.length) {
      return;
    }
    if (!soundPresets.includes(derivePreset)) {
      setDerivePreset(soundPresets[0]);
    }
  }, [derivePreset, soundPresets]);

  const runTranslate = async () => {
    await onRun('Translate text', 'translate', {
      storageDir,
      language: languageRef,
      text: translationText,
      useGrammar,
      autosave: true,
    });
  };

  const runGenerate = async () => {
    await onRun('Generate items', 'generate', {
      storageDir,
      language: languageRef,
      kind: genKind,
      count: Number(genCount || 10),
      category: genCategory,
      gender: genGender === 'none' ? null : genGender,
      number: genNumber,
      grammaticalCase: genCase,
      minSyllables: Number(genMinSyl || 1),
      maxSyllables: Number(genMaxSyl || 4),
      minScore: Number(genMinScore || 58),
      autosave: true,
      meaningPrefix: 'gui-generated-',
    });
  };

  const runDerive = async () => {
    await onRun('Derive daughter language', 'derive', {
      storageDir,
      language: languageRef,
      preset: derivePreset,
      name: deriveName || undefined,
    }, { refreshLanguages: true });
  };

  const runStyleSwitch = async () => {
    await onRun('Switch style', 'style_switch', {
      storageDir,
      language: languageRef,
      style: switchStyle,
      regenerateLexicon,
      noBootstrap: false,
    }, { refreshLanguages: true });
  };

  return (
    <Paper sx={{ p: 2.25 }}>
      <Stack spacing={2}>
        <Box>
          <Typography variant="h6">Language Operations</Typography>
          <Typography variant="body2" color="text.secondary">
            Translate, generate words or nouns, derive daughter languages, and style-switch existing languages.
          </Typography>
        </Box>

        <Grid container spacing={2}>
          <Grid item xs={12} md={8}>
            <TextField fullWidth select label="Active Language" value={languageRef} onChange={(event) => setLanguageRef(event.target.value)}>
              {languageOptions.map((item) => (
                <MenuItem key={item.value} value={item.value}>{item.label}</MenuItem>
              ))}
            </TextField>
          </Grid>
          <Grid item xs={12} md={4}>
            <TextField fullWidth label="Storage Directory" value={storageDir} onChange={(event) => setStorageDir(event.target.value)} />
          </Grid>
        </Grid>

        <Accordion defaultExpanded>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}><Typography variant="subtitle2">Translate</Typography></AccordionSummary>
          <AccordionDetails>
            <Stack spacing={1.5}>
              <TextField fullWidth multiline minRows={2} label="English Text" value={translationText} onChange={(event) => setTranslationText(event.target.value)} />
              <FormControlLabel control={<Switch checked={useGrammar} onChange={(event) => setUseGrammar(event.target.checked)} />} label="Use grammar engine" />
              <Stack direction="row" spacing={1.5}><Button variant="contained" onClick={runTranslate} disabled={!languageRef}>Translate</Button></Stack>
            </Stack>
          </AccordionDetails>
        </Accordion>

        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}><Typography variant="subtitle2">Generate Words / Nouns / Names</Typography></AccordionSummary>
          <AccordionDetails>
            <Grid container spacing={1.5}>
              <Grid item xs={12} md={4}><TextField fullWidth select label="Kind" value={genKind} onChange={(event) => setGenKind(event.target.value)}><MenuItem value="word">word</MenuItem><MenuItem value="noun">noun</MenuItem><MenuItem value="proper-noun">proper-noun</MenuItem><MenuItem value="name">name</MenuItem></TextField></Grid>
              <Grid item xs={12} md={4}><TextField fullWidth label="Count" value={genCount} onChange={(event) => setGenCount(event.target.value)} /></Grid>
              <Grid item xs={12} md={4}><TextField fullWidth label="Min Score" value={genMinScore} onChange={(event) => setGenMinScore(event.target.value)} /></Grid>
              <Grid item xs={12} md={3}><TextField fullWidth select label="Category" value={genCategory} onChange={(event) => setGenCategory(event.target.value)}><MenuItem value="person">person</MenuItem><MenuItem value="place">place</MenuItem><MenuItem value="thing">thing</MenuItem></TextField></Grid>
              <Grid item xs={12} md={3}><TextField fullWidth select label="Gender" value={genGender} onChange={(event) => setGenGender(event.target.value)}><MenuItem value="none">none</MenuItem><MenuItem value="male">male</MenuItem><MenuItem value="female">female</MenuItem><MenuItem value="neutral">neutral</MenuItem></TextField></Grid>
              <Grid item xs={12} md={3}><TextField fullWidth select label="Number" value={genNumber} onChange={(event) => setGenNumber(event.target.value)}><MenuItem value="singular">singular</MenuItem><MenuItem value="plural">plural</MenuItem></TextField></Grid>
              <Grid item xs={12} md={3}><TextField fullWidth select label="Case" value={genCase} onChange={(event) => setGenCase(event.target.value)}><MenuItem value="core">core</MenuItem><MenuItem value="accusative">accusative</MenuItem><MenuItem value="genitive">genitive</MenuItem></TextField></Grid>
              <Grid item xs={12} md={6}><TextField fullWidth label="Min Syllables" value={genMinSyl} onChange={(event) => setGenMinSyl(event.target.value)} /></Grid>
              <Grid item xs={12} md={6}><TextField fullWidth label="Max Syllables" value={genMaxSyl} onChange={(event) => setGenMaxSyl(event.target.value)} /></Grid>
            </Grid>
            <Stack direction="row" spacing={1.5} sx={{ mt: 1.5 }}><Button variant="outlined" onClick={runGenerate} disabled={!languageRef}>Generate</Button></Stack>
          </AccordionDetails>
        </Accordion>

        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}><Typography variant="subtitle2">Derive Daughter Language</Typography></AccordionSummary>
          <AccordionDetails>
            <Grid container spacing={1.5}>
              <Grid item xs={12} md={6}><TextField fullWidth select label="Sound-Change Preset" value={derivePreset} onChange={(event) => setDerivePreset(event.target.value)}>{soundPresets.map((item) => (<MenuItem key={item} value={item}>{item}</MenuItem>))}</TextField></Grid>
              <Grid item xs={12} md={6}><TextField fullWidth label="Derived Name (optional)" value={deriveName} onChange={(event) => setDeriveName(event.target.value)} /></Grid>
            </Grid>
            <Stack direction="row" spacing={1.5} sx={{ mt: 1.5 }}><Button variant="outlined" onClick={runDerive} disabled={!languageRef}>Derive</Button></Stack>
          </AccordionDetails>
        </Accordion>

        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}><Typography variant="subtitle2">Switch Style Preset</Typography></AccordionSummary>
          <AccordionDetails>
            <Grid container spacing={1.5}>
              <Grid item xs={12} md={8}><TextField fullWidth select label="Target Style" value={switchStyle} onChange={(event) => setSwitchStyle(event.target.value)}>{templates.map((item) => (<MenuItem key={item} value={item}>{item}</MenuItem>))}</TextField></Grid>
              <Grid item xs={12} md={4}><FormControlLabel control={<Switch checked={regenerateLexicon} onChange={(event) => setRegenerateLexicon(event.target.checked)} />} label="Regenerate Lexicon" /></Grid>
            </Grid>
            <Stack direction="row" spacing={1.5} sx={{ mt: 1.5 }}><Button variant="text" onClick={runStyleSwitch} disabled={!languageRef}>Switch Style</Button></Stack>
          </AccordionDetails>
        </Accordion>
      </Stack>
    </Paper>
  );
}
