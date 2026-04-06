import { useEffect, useMemo, useState } from 'react';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import CssBaseline from '@mui/material/CssBaseline';
import LinearProgress from '@mui/material/LinearProgress';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import Tab from '@mui/material/Tab';
import Tabs from '@mui/material/Tabs';
import ThemeProvider from '@mui/material/styles/ThemeProvider';
import Typography from '@mui/material/Typography';

import OutputPanel from './components/OutputPanel';
import ThinScrollbar from './components/ThinScrollbar';
import TopBar from './components/TopBar';
import EvaluatorPanel from './components/panels/EvaluatorPanel';
import LanguageManagerPanel from './components/panels/LanguageManagerPanel';
import ManualBuilderPanel from './components/panels/ManualBuilderPanel';
import OperationsPanel from './components/panels/OperationsPanel';
import QuickGeneratePanel from './components/panels/QuickGeneratePanel';
import { runBridgeAction } from './lib/bridge';
import { createAppTheme, themeCatalog } from './theme/themes';

const panelTabs = [
  { id: 'quick', label: 'Quick Generate' },
  { id: 'manual', label: 'Manual Builder' },
  { id: 'ops', label: 'All Systems' },
  { id: 'langs', label: 'Languages' },
  { id: 'eval', label: 'Evaluator' },
];

export default function App() {
  const [themeId, setThemeId] = useState(themeCatalog[0].id);
  const [activeTab, setActiveTab] = useState(0);

  const [templates, setTemplates] = useState([]);
  const [languages, setLanguages] = useState([]);
  const [soundPresets, setSoundPresets] = useState([]);

  const [busy, setBusy] = useState(false);
  const [statusMessage, setStatusMessage] = useState('Ready.');
  const [errorMessage, setErrorMessage] = useState('');

  const [outputTitle, setOutputTitle] = useState('Bridge Output');
  const [outputPayload, setOutputPayload] = useState({
    ok: true,
    result: {
      message: 'Waiting for command execution...',
    },
    logs: '',
  });

  const activeTheme = useMemo(() => createAppTheme(themeId), [themeId]);

  const refreshTemplates = async () => {
    const response = await runBridgeAction('list_templates', {});
    if (response.ok) {
      const templateList = (response.result?.templates || []).map((entry) => entry.name);
      setTemplates(templateList);
    }
    return response;
  };

  const refreshLanguages = async (storageDir = 'src/languages') => {
    const response = await runBridgeAction('list_languages', { storageDir });
    if (response.ok) {
      setLanguages(response.result?.languages || []);
    }
    return response;
  };

  const refreshSoundPresets = async () => {
    const response = await runBridgeAction('sound_change_presets', {});
    if (response.ok) {
      setSoundPresets(response.result?.presets || []);
    }
    return response;
  };

  const bootstrapApp = async () => {
    setBusy(true);
    setStatusMessage('Loading templates, languages, and presets...');
    setErrorMessage('');

    try {
      const [templatesRes, languagesRes, presetsRes] = await Promise.all([
        refreshTemplates(),
        refreshLanguages(),
        refreshSoundPresets(),
      ]);

      setOutputTitle('Startup Snapshot');
      setOutputPayload({
        ok: templatesRes.ok && languagesRes.ok && presetsRes.ok,
        result: {
          templates: templatesRes.result?.templates || [],
          languages: languagesRes.result?.languages || [],
          presets: presetsRes.result?.presets || [],
          templateCount: templatesRes.result?.templates?.length || 0,
          languageCount: languagesRes.result?.languages?.length || 0,
          presetCount: presetsRes.result?.presets?.length || 0,
        },
        logs: [templatesRes.logs, languagesRes.logs, presetsRes.logs].filter(Boolean).join('\n\n'),
      });
      setStatusMessage('Loaded bridge data successfully.');
    } catch (error) {
      setErrorMessage(String(error.message || error));
      setStatusMessage('Startup failed.');
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    bootstrapApp();
  }, []);

  const onRun = async (title, action, payload = {}, options = {}) => {
    setBusy(true);
    setErrorMessage('');
    setStatusMessage(`Running: ${title}`);

    try {
      const response = await runBridgeAction(action, payload);
      setOutputTitle(title);
      setOutputPayload(response);

      if (!response.ok) {
        setErrorMessage(response.error || 'Operation failed.');
        setStatusMessage(`Failed: ${title}`);
      } else {
        if (options.refreshLanguages) {
          await refreshLanguages(options.languagesStorageDir || 'src/languages');
        }
        if (options.refreshTemplates) {
          await refreshTemplates();
        }
        setStatusMessage(`Completed: ${title}`);
      }

      return response;
    } catch (error) {
      const message = String(error.message || error);
      setErrorMessage(message);
      setStatusMessage(`Error: ${title}`);
      setOutputTitle(title);
      setOutputPayload({ ok: false, error: message, logs: '' });
      return { ok: false, error: message };
    } finally {
      setBusy(false);
    }
  };

  let panelContent = null;
  if (activeTab === 0) {
    panelContent = <QuickGeneratePanel templates={templates} onRun={onRun} />;
  } else if (activeTab === 1) {
    panelContent = <ManualBuilderPanel templates={templates} onRun={onRun} />;
  } else if (activeTab === 2) {
    panelContent = (
      <OperationsPanel
        templates={templates}
        languages={languages}
        soundPresets={soundPresets}
        onRun={onRun}
      />
    );
  } else if (activeTab === 3) {
    panelContent = (
      <LanguageManagerPanel
        templates={templates}
        languages={languages}
        onRun={onRun}
      />
    );
  } else {
    panelContent = <EvaluatorPanel languages={languages} onRun={onRun} />;
  }

  return (
    <ThemeProvider theme={activeTheme}>
      <CssBaseline />
      <Box sx={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
        <TopBar themeId={themeId} onThemeChange={setThemeId} themes={themeCatalog} />

        {busy ? <LinearProgress /> : <Box sx={{ height: 4 }} />}

        <Box
          sx={{
            flex: 1,
            minHeight: 0,
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', md: 'minmax(0, 1fr) minmax(320px, 34vw)' },
            gridTemplateRows: { xs: 'minmax(0, 1fr) minmax(220px, 36vh)', md: 'minmax(0, 1fr)' },
            gap: 1.25,
            p: 1.25,
          }}
        >
          <Paper sx={{ minHeight: 0, minWidth: 0, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ px: 1.75, pt: 1.25 }}>
              <Stack direction="row" spacing={1} alignItems="center">
                <Typography variant="subtitle1">Conlang Studio GUI</Typography>
                <Chip size="small" label="Material UI" variant="outlined" />
                <Chip size="small" label="Electron" variant="outlined" />
              </Stack>
              <Typography variant="caption" color="text.secondary">{statusMessage}</Typography>
            </Stack>

            <Tabs
              value={activeTab}
              onChange={(_event, value) => setActiveTab(value)}
              variant="scrollable"
              scrollButtons="auto"
              sx={{ px: 1 }}
            >
              {panelTabs.map((tab) => (
                <Tab key={tab.id} label={tab.label} />
              ))}
            </Tabs>

            {errorMessage ? (
              <Box sx={{ px: 1.5, pb: 1 }}>
                <Alert severity="error">{errorMessage}</Alert>
              </Box>
            ) : null}

            <ThinScrollbar sx={{ flex: 1, px: 1.5, pb: 1.5 }}>
              {panelContent}
            </ThinScrollbar>
          </Paper>

          <Box
            sx={{
              minHeight: 0,
              minWidth: 0,
              borderLeft: { xs: 'none', md: '1px solid' },
              borderColor: 'divider',
              pl: { xs: 0, md: 1 },
            }}
          >
            <OutputPanel title={outputTitle} payload={outputPayload} />
          </Box>
        </Box>
      </Box>
    </ThemeProvider>
  );
}
