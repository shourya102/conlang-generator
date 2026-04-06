import { useEffect, useMemo, useState } from 'react';
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import CircularProgress from '@mui/material/CircularProgress';
import Divider from '@mui/material/Divider';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import Grid from '@mui/material/Grid';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';

import ThinScrollbar from './ThinScrollbar';
import { runBridgeAction } from '../lib/bridge';

function stringifySafe(value) {
  try {
    return JSON.stringify(value, null, 2);
  } catch (_error) {
    return String(value);
  }
}

function parsePayload(payload) {
  if (!payload) {
    return null;
  }
  if (typeof payload === 'object') {
    return payload;
  }
  if (typeof payload === 'string') {
    try {
      return JSON.parse(payload);
    } catch (_error) {
      return {
        ok: true,
        result: payload,
      };
    }
  }
  return { ok: true, result: payload };
}

function deriveHeroResult(data, title) {
  if (!data) {
    return {
      label: title || 'Result',
      text: 'Run an action to see output here.',
      status: 'idle',
    };
  }

  if (data.ok === false) {
    return {
      label: title || 'Result',
      text: data.error || 'Operation failed.',
      status: 'error',
    };
  }

  const result = data.result;

  if (result && typeof result === 'object') {
    if (typeof result.translated === 'string' && result.translated.trim()) {
      return { label: 'Translated Result', text: result.translated, status: 'success' };
    }

    if (Array.isArray(result.results)) {
      const values = result.results
        .map((item) => {
          if (item && typeof item === 'object' && 'value' in item) {
            return item.value;
          }
          return item;
        })
        .filter((item) => item !== null && item !== undefined && String(item).trim() !== '')
        .map((item) => String(item));

      if (values.length) {
        return {
          label: title || 'Generated Result',
          text: values.join('\n'),
          status: 'success',
        };
      }
    }

    if (typeof result.name === 'string' && result.name.trim()) {
      return {
        label: title || 'Result',
        text: result.name,
        status: 'success',
      };
    }

    if (typeof result.path === 'string' && result.path.trim()) {
      return {
        label: title || 'Result',
        text: result.path,
        status: 'success',
      };
    }

    if (typeof result.accepted === 'number' && typeof result.total === 'number') {
      return {
        label: title || 'Result',
        text: `${result.accepted}/${result.total} accepted`,
        status: 'success',
      };
    }
  }

  return {
    label: title || 'Result',
    text: typeof result === 'string' ? result : stringifySafe(result ?? data),
    status: 'success',
  };
}

function deriveMetadata(data, title) {
  const rows = [];
  rows.push({ label: 'Status', value: data?.ok === false ? 'Failed' : 'Completed' });
  if (title) {
    rows.push({ label: 'Action', value: title });
  }

  const result = data?.result;
  if (result && typeof result === 'object') {
    if (result.path) {
      rows.push({ label: 'Path', value: String(result.path) });
    }
    if (result.style) {
      rows.push({ label: 'Style', value: String(result.style) });
    }
    if (result.template) {
      rows.push({ label: 'Template', value: String(result.template) });
    }
    if (typeof result.total === 'number') {
      rows.push({ label: 'Total', value: String(result.total) });
    }
    if (typeof result.accepted === 'number') {
      rows.push({ label: 'Accepted', value: String(result.accepted) });
    }
  }

  return rows;
}

function deriveLogs(data) {
  const segments = [];
  if (data?.logs) {
    segments.push(String(data.logs));
  }
  if (data?.stderr) {
    segments.push(`stderr:\n${String(data.stderr)}`);
  }
  if (data?.traceback) {
    segments.push(`traceback:\n${String(data.traceback)}`);
  }
  segments.push(`payload:\n${stringifySafe(data)}`);
  return segments.join('\n\n').trim();
}

function deriveTranslationRows(data) {
  const rows = data?.result?.breakdown;
  if (!Array.isArray(rows)) {
    return [];
  }
  return rows;
}

function deriveDictionaryRows(data) {
  const rows = data?.result?.dictionary;
  if (!Array.isArray(rows)) {
    return [];
  }
  return rows;
}

function formatMorphology(entry) {
  if (!entry || typeof entry !== 'object') {
    return 'N/A';
  }
  return `${entry.prefix || ''}-${entry.root || ''}-${entry.suffix || ''}`.replace(/^[-]+|[-]+$/g, '') || 'N/A';
}

export default function OutputPanel({ title, payload }) {
  const [copied, setCopied] = useState(false);
  const [lookupWord, setLookupWord] = useState('');
  const [lookupBusy, setLookupBusy] = useState(false);
  const [lookupError, setLookupError] = useState('');
  const [lookupResult, setLookupResult] = useState(null);

  const parsed = useMemo(() => parsePayload(payload), [payload]);
  const hero = useMemo(() => deriveHeroResult(parsed, title), [parsed, title]);
  const metadataRows = useMemo(() => deriveMetadata(parsed, title), [parsed, title]);
  const logsText = useMemo(() => deriveLogs(parsed), [parsed]);
  const translationRows = useMemo(() => deriveTranslationRows(parsed), [parsed]);
  const dictionaryRows = useMemo(() => deriveDictionaryRows(parsed), [parsed]);
  const translatedWordCount = useMemo(
    () => translationRows.filter((row) => !row?.is_punctuation && !row?.is_number).length,
    [translationRows],
  );
  const canSaveToLexicon = Boolean(parsed?.ok && Array.isArray(parsed?.result?.results) && parsed?.result?.path);
  const lookupLanguageRef = parsed?.result?.path || '';

  useEffect(() => {
    setLookupError('');
    setLookupResult(null);
    if (translationRows.length) {
      const firstWord = translationRows.find((row) => !row?.is_punctuation && !row?.is_number && row?.translated_token);
      setLookupWord(firstWord?.translated_token || '');
    } else {
      setLookupWord('');
    }
  }, [translationRows, lookupLanguageRef]);

  const handleCopy = async () => {
    if (!hero.text) {
      return;
    }
    try {
      await navigator.clipboard.writeText(hero.text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1300);
    } catch (_error) {
      setCopied(false);
    }
  };

  const handleSaveToLexicon = async () => {
    if (!canSaveToLexicon) {
      return;
    }
    const resultText = `Generated items are already persisted to ${parsed.result.path}`;
    await navigator.clipboard.writeText(resultText);
    setCopied(true);
    setTimeout(() => setCopied(false), 1300);
  };

  const handleLookup = async (queryOverride = '') => {
    const query = String(queryOverride || lookupWord || '').trim();
    if (!query) {
      return;
    }

    if (!lookupLanguageRef) {
      setLookupError('Dictionary lookup requires a loaded language context.');
      setLookupResult(null);
      return;
    }

    setLookupBusy(true);
    setLookupError('');
    setLookupResult(null);

    try {
      const response = await runBridgeAction('dictionary_lookup', {
        storageDir: 'src/languages',
        language: lookupLanguageRef,
        query,
      });

      if (!response?.ok) {
        setLookupError(response?.error || 'Lookup failed.');
        return;
      }

      setLookupResult(response.result || null);
    } catch (error) {
      setLookupError(String(error.message || error));
    } finally {
      setLookupBusy(false);
    }
  };

  return (
    <Paper
      sx={{
        height: '100%',
        minHeight: 0,
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        bgcolor: (theme) => theme.palette.surface?.side || 'background.default',
      }}
    >
      <Stack direction="row" alignItems="center" spacing={1} sx={{ px: 2, py: 1.5 }}>
        <Typography variant="subtitle2">Output</Typography>
        {title ? (
          <Typography variant="caption" color="text.secondary">
            {title}
          </Typography>
        ) : null}
      </Stack>
      <Divider />

      <ThinScrollbar sx={{ px: 2, py: 1.5, flex: 1 }}>
        <Stack spacing={1.5}>
          <Box sx={{ p: 1.5, borderRadius: 1.5, bgcolor: 'background.paper' }}>
            <Typography variant="caption" color="text.secondary" sx={{ letterSpacing: 0.35, textTransform: 'uppercase' }}>
              {hero.label}
            </Typography>
            <Typography
              sx={{
                mt: 0.8,
                fontSize: 19,
                lineHeight: 1.45,
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
                color: hero.status === 'error' ? 'error.light' : 'text.primary',
              }}
            >
              {hero.text}
            </Typography>
            <Stack direction="row" spacing={1} sx={{ mt: 1.25 }}>
              <Button variant="outlined" size="small" onClick={handleCopy}>
                {copied ? 'Copied' : 'Copy'}
              </Button>
              <Button variant="text" size="small" onClick={handleSaveToLexicon} disabled={!canSaveToLexicon}>
                Save to Lexicon
              </Button>
            </Stack>
          </Box>

          <Box sx={{ p: 1.5, borderRadius: 1.5, bgcolor: 'background.paper' }}>
            <Typography variant="caption" color="text.secondary" sx={{ letterSpacing: 0.35, textTransform: 'uppercase' }}>
              Metadata
            </Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap sx={{ mt: 1 }}>
              {metadataRows.map((row) => (
                <Chip
                  key={`${row.label}:${row.value}`}
                  size="small"
                  variant="outlined"
                  label={`${row.label}: ${row.value}`}
                />
              ))}
            </Stack>
          </Box>

          {translationRows.length ? (
            <Box sx={{ p: 1.5, borderRadius: 1.5, bgcolor: 'background.paper' }}>
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} justifyContent="space-between" alignItems={{ xs: 'flex-start', sm: 'center' }}>
                <Typography variant="caption" color="text.secondary" sx={{ letterSpacing: 0.35, textTransform: 'uppercase' }}>
                  Translation Deconstruction
                </Typography>
                <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                  <Chip size="small" variant="outlined" label={`${translatedWordCount} translated token${translatedWordCount === 1 ? '' : 's'}`} />
                  <Chip size="small" variant="outlined" label={`${dictionaryRows.length} dictionary match${dictionaryRows.length === 1 ? '' : 'es'}`} />
                </Stack>
              </Stack>

              <Grid container spacing={1.25} sx={{ mt: 0.5 }}>
                <Grid item xs={12} md={12}>
                  <Paper sx={{ overflow: 'hidden' }}>
                    <ThinScrollbar sx={{ maxHeight: 300 }}>
                      <Table size="small" stickyHeader>
                        <TableHead>
                          <TableRow>
                            <TableCell>#</TableCell>
                            <TableCell>Source</TableCell>
                            <TableCell>Translated</TableCell>
                            <TableCell>Meaning</TableCell>
                            <TableCell>POS</TableCell>
                            <TableCell align="right">Lookup</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {translationRows.map((row, index) => {
                            const canLookup = !row?.is_punctuation && !row?.is_number && Boolean(row?.translated_token) && Boolean(lookupLanguageRef);
                            return (
                              <TableRow
                                key={`${row?.source_token || 'tok'}-${row?.translated_token || 'val'}-${index}`}
                                sx={{ opacity: row?.is_punctuation ? 0.75 : 1 }}
                              >
                                <TableCell>{index + 1}</TableCell>
                                <TableCell sx={{ fontFamily: 'Consolas, "Cascadia Mono", monospace' }}>{row?.source_token || ''}</TableCell>
                                <TableCell sx={{ fontFamily: 'Consolas, "Cascadia Mono", monospace' }}>{row?.translated_token || ''}</TableCell>
                                <TableCell>{row?.english_meaning || ''}</TableCell>
                                <TableCell>{row?.part_of_speech || ''}</TableCell>
                                <TableCell align="right">
                                  <Button
                                    variant="text"
                                    size="small"
                                    disabled={!canLookup || lookupBusy}
                                    onClick={() => handleLookup(row?.translated_token || '')}
                                  >
                                    Lookup
                                  </Button>
                                </TableCell>
                              </TableRow>
                            );
                          })}
                        </TableBody>
                      </Table>
                    </ThinScrollbar>
                  </Paper>
                </Grid>

                <Grid item xs={12} md={12}>
                  <Paper sx={{ p: 1.25, bgcolor: 'background.default' }}>
                    <Stack spacing={1.1}>
                      <Typography variant="subtitle2">Dictionary Inspector</Typography>
                      <Stack direction={{ xs: 'column', sm: 'row', md: 'column', lg: 'row' }} spacing={1}>
                        <TextField
                          fullWidth
                          size="small"
                          label="Dictionary Lookup"
                          value={lookupWord}
                          onChange={(event) => setLookupWord(event.target.value)}
                        />
                        <Button variant="outlined" size="small" onClick={() => handleLookup()} disabled={lookupBusy || !lookupWord.trim()}>
                          {lookupBusy ? <CircularProgress size={16} /> : 'Search'}
                        </Button>
                      </Stack>

                      {dictionaryRows.length ? (
                        <Box>
                          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.75 }}>
                            Quick picks from this translation
                          </Typography>
                          <Stack direction="row" spacing={0.75} useFlexGap flexWrap="wrap">
                            {dictionaryRows.slice(0, 14).map((entry) => (
                              <Chip
                                key={`${entry.word}-${entry.english_meaning || 'x'}`}
                                size="small"
                                variant="outlined"
                                label={entry.word || 'Unknown'}
                                onClick={() => handleLookup(entry.word || '')}
                              />
                            ))}
                          </Stack>
                        </Box>
                      ) : null}

                      {lookupError ? (
                        <Typography variant="caption" color="error">
                          {lookupError}
                        </Typography>
                      ) : null}

                      {lookupResult ? (
                        <Paper sx={{ p: 1.1 }}>
                          {lookupResult.found && lookupResult.entry ? (
                            <Stack spacing={0.55}>
                              <Stack direction="row" justifyContent="space-between" spacing={1}>
                                <Typography variant="subtitle2">{lookupResult.entry.word || lookupResult.query}</Typography>
                                <Chip size="small" variant="outlined" label={lookupResult.match || 'match'} />
                              </Stack>
                              <Typography variant="body2" color="text.secondary">
                                Meaning: {lookupResult.entry.english_meaning || 'N/A'}
                              </Typography>
                              <Typography variant="body2" color="text.secondary">
                                POS: {lookupResult.entry.part_of_speech || 'N/A'}
                              </Typography>
                              <Typography variant="body2" color="text.secondary">
                                Morphology: {formatMorphology(lookupResult.entry)}
                              </Typography>
                            </Stack>
                          ) : (
                            <Typography variant="body2" color="text.secondary">
                              No dictionary entry found for "{lookupResult.query || lookupWord}".
                            </Typography>
                          )}
                        </Paper>
                      ) : (
                        <Typography variant="caption" color="text.secondary">
                          Select a translated token or type a word to inspect its meaning.
                        </Typography>
                      )}
                    </Stack>
                  </Paper>
                </Grid>
              </Grid>
            </Box>
          ) : null}

          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle2">System Logs</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Typography
                component="pre"
                sx={{
                  mt: 0,
                  mb: 0,
                  fontFamily: 'Consolas, "Cascadia Mono", monospace',
                  fontSize: 12,
                  whiteSpace: 'pre-wrap',
                  lineHeight: 1.55,
                  color: 'text.secondary',
                }}
              >
                {logsText || 'No logs available.'}
              </Typography>
            </AccordionDetails>
          </Accordion>
        </Stack>
      </ThinScrollbar>
    </Paper>
  );
}
