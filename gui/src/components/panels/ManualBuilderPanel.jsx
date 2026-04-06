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

function splitCsv(value) {
  return String(value || '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
}

export default function ManualBuilderPanel({ templates, onRun }) {
  const [name, setName] = useState('custom-language');
  const [template, setTemplate] = useState('');
  const [bootstrap, setBootstrap] = useState(true);
  const [storageDir, setStorageDir] = useState('src/languages');

  const [enabled, setEnabled] = useState({
    phonology: true,
    morphology: true,
    grammar: true,
    wordgen: true,
    namegen: true,
    quality: true,
    soundRules: false,
  });

  const [phonology, setPhonology] = useState({
    consonants: 'p,t,k,b,d,g,m,n,l,r,s,f,v,h,y,w',
    vowels: 'a,e,i,o,u,ae,ai,ei,io',
    syllable_structures: 'CV,CVC,V,VC',
    onsets: 'p,t,k,b,d,g,m,n,l,r,s,f,v,h,y,w,pr,tr,kr,st,',
    codas: 'n,r,l,s,m,t,k,',
    max_consonant_cluster: '2',
  });

  const [morphology, setMorphology] = useState({
    num_roots: '420',
    num_prefixes: '50',
    num_suffixes: '90',
    root_min_syl: '1',
    root_max_syl: '2',
    affix_max_syl: '1',
  });

  const [grammar, setGrammar] = useState({
    word_order: 'SVO',
    adjective_position: 'after',
    adposition_order: 'preposition',
    adverb_position: 'before',
    drop_articles: true,
    drop_redundant_auxiliaries: true,
    enable_case_marking: true,
    case_marking_style: 'suffix',
    case_mark_pronouns: false,
    plural_suffix: 'i',
    accusative_suffix: 'm',
    genitive_suffix: 'n',
    nominative_particle: '',
    accusative_particle: 'ko',
    genitive_particle: 'no',
    past_prefix: 'ta',
    future_prefix: 'sa',
    progressive_suffix: 'ri',
    perfect_suffix: 'na',
    enable_subject_agreement: true,
    agreement_style: 'suffix',
    agreement_1sg: 'm',
    agreement_2sg: 't',
    agreement_3sg: '',
    agreement_1pl: 'me',
    agreement_2pl: 'te',
    agreement_3pl: 'n',
    negation_particle: 'na',
    negation_position: 'before_verb',
    replace_lexical_negation: true,
    question_particle: 'ka',
    question_particle_position: 'clause_final',
  });

  const [wordgen, setWordgen] = useState({
    prefix_prob: '0.14',
    suffix_prob: '0.30',
    max_gen_attempts: '120',
  });

  const [namegen, setNamegen] = useState({
    person_min_syl: '2',
    person_max_syl: '3',
    place_min_syl: '2',
    place_max_syl: '4',
    thing_min_syl: '1',
    thing_max_syl: '3',
    person_male_suffixes: 'us,or,an,ius',
    person_female_suffixes: 'a,ia,ina,illa',
    person_neutral_suffixes: 'is,en,o,um',
    place_suffixes: 'ia,um,os,ana,polis,burg',
    thing_suffixes: 'ex,or,mentum,io',
    person_suffix_prob: '0.58',
    place_suffix_prob: '0.50',
    thing_suffix_prob: '0.24',
    max_attempts: '120',
  });

  const [quality, setQuality] = useState({
    min_pronounceability_score: '58',
  });

  const [soundRules, setSoundRules] = useState('[\n  {"pattern": "p", "replacement": "f", "probability": 0.2}\n]');

  useEffect(() => {
    if (!templates.length || !template) {
      return;
    }
    if (!templates.includes(template)) {
      setTemplate('');
    }
  }, [template, templates]);

  const sectionSummary = useMemo(() => {
    const active = Object.keys(enabled).filter((key) => enabled[key]);
    return `${active.length} active section${active.length === 1 ? '' : 's'}`;
  }, [enabled]);

  const buildOverrides = () => {
    const overrides = {};

    if (enabled.phonology) {
      overrides.phonology = {
        consonants: splitCsv(phonology.consonants),
        vowels: splitCsv(phonology.vowels),
        syllable_structures: splitCsv(phonology.syllable_structures),
        onsets: splitCsv(phonology.onsets),
        codas: splitCsv(phonology.codas),
        max_consonant_cluster: Number(phonology.max_consonant_cluster || 2),
      };
    }

    if (enabled.morphology) {
      overrides.morphology = {
        num_roots: Number(morphology.num_roots || 420),
        num_prefixes: Number(morphology.num_prefixes || 50),
        num_suffixes: Number(morphology.num_suffixes || 90),
        root_min_syl: Number(morphology.root_min_syl || 1),
        root_max_syl: Number(morphology.root_max_syl || 2),
        affix_max_syl: Number(morphology.affix_max_syl || 1),
      };
    }

    if (enabled.grammar) {
      overrides.grammar = {
        word_order: grammar.word_order,
        adjective_position: grammar.adjective_position,
        adposition_order: grammar.adposition_order,
        adverb_position: grammar.adverb_position,
        drop_articles: Boolean(grammar.drop_articles),
        drop_redundant_auxiliaries: Boolean(grammar.drop_redundant_auxiliaries),
        enable_case_marking: Boolean(grammar.enable_case_marking),
        case_marking_style: grammar.case_marking_style,
        case_mark_pronouns: Boolean(grammar.case_mark_pronouns),
        plural_suffix: grammar.plural_suffix,
        accusative_suffix: grammar.accusative_suffix,
        genitive_suffix: grammar.genitive_suffix,
        nominative_particle: grammar.nominative_particle,
        accusative_particle: grammar.accusative_particle,
        genitive_particle: grammar.genitive_particle,
        past_prefix: grammar.past_prefix,
        future_prefix: grammar.future_prefix,
        progressive_suffix: grammar.progressive_suffix,
        perfect_suffix: grammar.perfect_suffix,
        enable_subject_agreement: Boolean(grammar.enable_subject_agreement),
        agreement_style: grammar.agreement_style,
        agreement_markers: {
          '1sg': grammar.agreement_1sg,
          '2sg': grammar.agreement_2sg,
          '3sg': grammar.agreement_3sg,
          '1pl': grammar.agreement_1pl,
          '2pl': grammar.agreement_2pl,
          '3pl': grammar.agreement_3pl,
        },
        negation_particle: grammar.negation_particle,
        negation_position: grammar.negation_position,
        replace_lexical_negation: Boolean(grammar.replace_lexical_negation),
        question_particle: grammar.question_particle,
        question_particle_position: grammar.question_particle_position,
      };
    }

    if (enabled.wordgen) {
      overrides.word_generator_params = {
        prefix_prob: Number(wordgen.prefix_prob || 0.14),
        suffix_prob: Number(wordgen.suffix_prob || 0.30),
        max_gen_attempts: Number(wordgen.max_gen_attempts || 120),
      };
    }

    if (enabled.namegen) {
      overrides.name_generator_params = {
        person_min_syl: Number(namegen.person_min_syl || 2),
        person_max_syl: Number(namegen.person_max_syl || 3),
        place_min_syl: Number(namegen.place_min_syl || 2),
        place_max_syl: Number(namegen.place_max_syl || 4),
        thing_min_syl: Number(namegen.thing_min_syl || 1),
        thing_max_syl: Number(namegen.thing_max_syl || 3),
        person_male_suffixes: splitCsv(namegen.person_male_suffixes),
        person_female_suffixes: splitCsv(namegen.person_female_suffixes),
        person_neutral_suffixes: splitCsv(namegen.person_neutral_suffixes),
        place_suffixes: splitCsv(namegen.place_suffixes),
        thing_suffixes: splitCsv(namegen.thing_suffixes),
        person_suffix_prob: Number(namegen.person_suffix_prob || 0.58),
        place_suffix_prob: Number(namegen.place_suffix_prob || 0.50),
        thing_suffix_prob: Number(namegen.thing_suffix_prob || 0.24),
        max_attempts: Number(namegen.max_attempts || 120),
      };
    }

    if (enabled.quality) {
      overrides.generation_quality = {
        min_pronounceability_score: Number(quality.min_pronounceability_score || 58),
      };
    }

    if (enabled.soundRules) {
      overrides.sound_change_rules = JSON.parse(soundRules || '[]');
    }

    return overrides;
  };

  const handleGenerate = async () => {
    const payload = {
      name,
      template: template || undefined,
      bootstrap,
      storageDir,
      overrides: buildOverrides(),
    };

    await onRun('Manual build language', 'create_language', payload, { refreshLanguages: true });
  };

  const handleToggle = (sectionKey) => (event) => {
    setEnabled((previous) => ({ ...previous, [sectionKey]: event.target.checked }));
  };

  return (
    <Paper sx={{ p: 2.25 }}>
      <Stack spacing={2}>
        <Box>
          <Typography variant="h6">Manual Builder</Typography>
          <Typography variant="body2" color="text.secondary">
            Customize every system fully. You can disable any section to skip it and still generate directly.
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {sectionSummary}
          </Typography>
        </Box>

        <Grid container spacing={2}>
          <Grid item xs={12} md={4}>
            <TextField fullWidth label="Language Name" value={name} onChange={(event) => setName(event.target.value)} />
          </Grid>
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              select
              label="Base Template (optional)"
              value={template}
              onChange={(event) => setTemplate(event.target.value)}
            >
              <MenuItem value="">None (from raw defaults)</MenuItem>
              {templates.map((item) => (
                <MenuItem key={item} value={item}>
                  {item}
                </MenuItem>
              ))}
            </TextField>
          </Grid>
          <Grid item xs={12} md={4}>
            <TextField fullWidth label="Storage Directory" value={storageDir} onChange={(event) => setStorageDir(event.target.value)} />
          </Grid>
        </Grid>

        <FormControlLabel
          control={<Switch checked={bootstrap} onChange={(event) => setBootstrap(event.target.checked)} />}
          label="Bootstrap core lexicon"
        />

        <Accordion defaultExpanded>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <FormControlLabel
              onClick={(event) => event.stopPropagation()}
              onFocus={(event) => event.stopPropagation()}
              control={<Switch checked={enabled.phonology} onChange={handleToggle('phonology')} />}
              label="Phonology"
            />
          </AccordionSummary>
          <AccordionDetails>
            <Grid container spacing={1.5}>
              <Grid item xs={12}><TextField fullWidth label="Consonants (csv)" value={phonology.consonants} onChange={(event) => setPhonology((prev) => ({ ...prev, consonants: event.target.value }))} /></Grid>
              <Grid item xs={12}><TextField fullWidth label="Vowels (csv)" value={phonology.vowels} onChange={(event) => setPhonology((prev) => ({ ...prev, vowels: event.target.value }))} /></Grid>
              <Grid item xs={12} md={6}><TextField fullWidth label="Syllable Structures (csv)" value={phonology.syllable_structures} onChange={(event) => setPhonology((prev) => ({ ...prev, syllable_structures: event.target.value }))} /></Grid>
              <Grid item xs={12} md={6}><TextField fullWidth label="Max Consonant Cluster" value={phonology.max_consonant_cluster} onChange={(event) => setPhonology((prev) => ({ ...prev, max_consonant_cluster: event.target.value }))} /></Grid>
              <Grid item xs={12} md={6}><TextField fullWidth label="Onsets (csv)" value={phonology.onsets} onChange={(event) => setPhonology((prev) => ({ ...prev, onsets: event.target.value }))} /></Grid>
              <Grid item xs={12} md={6}><TextField fullWidth label="Codas (csv)" value={phonology.codas} onChange={(event) => setPhonology((prev) => ({ ...prev, codas: event.target.value }))} /></Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>

        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <FormControlLabel
              onClick={(event) => event.stopPropagation()}
              onFocus={(event) => event.stopPropagation()}
              control={<Switch checked={enabled.morphology} onChange={handleToggle('morphology')} />}
              label="Morphology"
            />
          </AccordionSummary>
          <AccordionDetails>
            <Grid container spacing={1.5}>
              <Grid item xs={12} md={4}><TextField fullWidth label="Roots" value={morphology.num_roots} onChange={(event) => setMorphology((prev) => ({ ...prev, num_roots: event.target.value }))} /></Grid>
              <Grid item xs={12} md={4}><TextField fullWidth label="Prefixes" value={morphology.num_prefixes} onChange={(event) => setMorphology((prev) => ({ ...prev, num_prefixes: event.target.value }))} /></Grid>
              <Grid item xs={12} md={4}><TextField fullWidth label="Suffixes" value={morphology.num_suffixes} onChange={(event) => setMorphology((prev) => ({ ...prev, num_suffixes: event.target.value }))} /></Grid>
              <Grid item xs={12} md={4}><TextField fullWidth label="Root Min Syllables" value={morphology.root_min_syl} onChange={(event) => setMorphology((prev) => ({ ...prev, root_min_syl: event.target.value }))} /></Grid>
              <Grid item xs={12} md={4}><TextField fullWidth label="Root Max Syllables" value={morphology.root_max_syl} onChange={(event) => setMorphology((prev) => ({ ...prev, root_max_syl: event.target.value }))} /></Grid>
              <Grid item xs={12} md={4}><TextField fullWidth label="Affix Max Syllables" value={morphology.affix_max_syl} onChange={(event) => setMorphology((prev) => ({ ...prev, affix_max_syl: event.target.value }))} /></Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>

        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <FormControlLabel
              onClick={(event) => event.stopPropagation()}
              onFocus={(event) => event.stopPropagation()}
              control={<Switch checked={enabled.grammar} onChange={handleToggle('grammar')} />}
              label="Grammar"
            />
          </AccordionSummary>
          <AccordionDetails>
            <Grid container spacing={1.5}>
              <Grid item xs={12} md={3}>
                <TextField
                  fullWidth
                  select
                  label="Word Order"
                  value={grammar.word_order}
                  onChange={(event) => setGrammar((prev) => ({ ...prev, word_order: event.target.value }))}
                >
                  <MenuItem value="SVO">SVO</MenuItem>
                  <MenuItem value="SOV">SOV</MenuItem>
                  <MenuItem value="VSO">VSO</MenuItem>
                  <MenuItem value="VOS">VOS</MenuItem>
                  <MenuItem value="OSV">OSV</MenuItem>
                  <MenuItem value="OVS">OVS</MenuItem>
                </TextField>
              </Grid>
              <Grid item xs={12} md={3}>
                <TextField
                  fullWidth
                  select
                  label="Adjective Position"
                  value={grammar.adjective_position}
                  onChange={(event) => setGrammar((prev) => ({ ...prev, adjective_position: event.target.value }))}
                >
                  <MenuItem value="before">before</MenuItem>
                  <MenuItem value="after">after</MenuItem>
                </TextField>
              </Grid>
              <Grid item xs={12} md={3}>
                <TextField
                  fullWidth
                  select
                  label="Adposition Order"
                  value={grammar.adposition_order}
                  onChange={(event) => setGrammar((prev) => ({ ...prev, adposition_order: event.target.value }))}
                >
                  <MenuItem value="preposition">preposition</MenuItem>
                  <MenuItem value="postposition">postposition</MenuItem>
                </TextField>
              </Grid>
              <Grid item xs={12} md={3}>
                <TextField
                  fullWidth
                  select
                  label="Adverb Placement"
                  value={grammar.adverb_position}
                  onChange={(event) => setGrammar((prev) => ({ ...prev, adverb_position: event.target.value }))}
                >
                  <MenuItem value="before">before verb</MenuItem>
                  <MenuItem value="after">after verb</MenuItem>
                </TextField>
              </Grid>

              <Grid item xs={12} md={6}>
                <FormControlLabel
                  control={<Switch checked={grammar.drop_articles} onChange={(event) => setGrammar((prev) => ({ ...prev, drop_articles: event.target.checked }))} />}
                  label="Drop Articles (a/an/the)"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControlLabel
                  control={<Switch checked={grammar.drop_redundant_auxiliaries} onChange={(event) => setGrammar((prev) => ({ ...prev, drop_redundant_auxiliaries: event.target.checked }))} />}
                  label="Drop Redundant Auxiliaries"
                />
              </Grid>

              <Grid item xs={12} md={4}>
                <FormControlLabel
                  control={<Switch checked={grammar.enable_case_marking} onChange={(event) => setGrammar((prev) => ({ ...prev, enable_case_marking: event.target.checked }))} />}
                  label="Enable Case Marking"
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  select
                  label="Case Style"
                  value={grammar.case_marking_style}
                  onChange={(event) => setGrammar((prev) => ({ ...prev, case_marking_style: event.target.value }))}
                >
                  <MenuItem value="suffix">suffixes</MenuItem>
                  <MenuItem value="particle">particles</MenuItem>
                </TextField>
              </Grid>
              <Grid item xs={12} md={4}>
                <FormControlLabel
                  control={<Switch checked={grammar.case_mark_pronouns} onChange={(event) => setGrammar((prev) => ({ ...prev, case_mark_pronouns: event.target.checked }))} />}
                  label="Case-Mark Pronouns"
                />
              </Grid>
              <Grid item xs={12} md={2}><TextField fullWidth label="Plural Suffix" value={grammar.plural_suffix} onChange={(event) => setGrammar((prev) => ({ ...prev, plural_suffix: event.target.value }))} /></Grid>
              <Grid item xs={12} md={2}><TextField fullWidth label="Accusative Suffix" value={grammar.accusative_suffix} onChange={(event) => setGrammar((prev) => ({ ...prev, accusative_suffix: event.target.value }))} /></Grid>
              <Grid item xs={12} md={2}><TextField fullWidth label="Genitive Suffix" value={grammar.genitive_suffix} onChange={(event) => setGrammar((prev) => ({ ...prev, genitive_suffix: event.target.value }))} /></Grid>
              <Grid item xs={12} md={2}><TextField fullWidth label="Nom. Particle" value={grammar.nominative_particle} onChange={(event) => setGrammar((prev) => ({ ...prev, nominative_particle: event.target.value }))} /></Grid>
              <Grid item xs={12} md={2}><TextField fullWidth label="Acc. Particle" value={grammar.accusative_particle} onChange={(event) => setGrammar((prev) => ({ ...prev, accusative_particle: event.target.value }))} /></Grid>
              <Grid item xs={12} md={2}><TextField fullWidth label="Gen. Particle" value={grammar.genitive_particle} onChange={(event) => setGrammar((prev) => ({ ...prev, genitive_particle: event.target.value }))} /></Grid>

              <Grid item xs={12} md={3}><TextField fullWidth label="Past Prefix" value={grammar.past_prefix} onChange={(event) => setGrammar((prev) => ({ ...prev, past_prefix: event.target.value }))} /></Grid>
              <Grid item xs={12} md={3}><TextField fullWidth label="Future Prefix" value={grammar.future_prefix} onChange={(event) => setGrammar((prev) => ({ ...prev, future_prefix: event.target.value }))} /></Grid>
              <Grid item xs={12} md={3}><TextField fullWidth label="Progressive Suffix" value={grammar.progressive_suffix} onChange={(event) => setGrammar((prev) => ({ ...prev, progressive_suffix: event.target.value }))} /></Grid>
              <Grid item xs={12} md={3}><TextField fullWidth label="Perfect Suffix" value={grammar.perfect_suffix} onChange={(event) => setGrammar((prev) => ({ ...prev, perfect_suffix: event.target.value }))} /></Grid>

              <Grid item xs={12} md={4}>
                <FormControlLabel
                  control={<Switch checked={grammar.enable_subject_agreement} onChange={(event) => setGrammar((prev) => ({ ...prev, enable_subject_agreement: event.target.checked }))} />}
                  label="Enable Subject Agreement"
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  select
                  label="Agreement Affix Side"
                  value={grammar.agreement_style}
                  onChange={(event) => setGrammar((prev) => ({ ...prev, agreement_style: event.target.value }))}
                >
                  <MenuItem value="suffix">suffix</MenuItem>
                  <MenuItem value="prefix">prefix</MenuItem>
                </TextField>
              </Grid>
              <Grid item xs={12} md={2}><TextField fullWidth label="1sg" value={grammar.agreement_1sg} onChange={(event) => setGrammar((prev) => ({ ...prev, agreement_1sg: event.target.value }))} /></Grid>
              <Grid item xs={12} md={2}><TextField fullWidth label="2sg" value={grammar.agreement_2sg} onChange={(event) => setGrammar((prev) => ({ ...prev, agreement_2sg: event.target.value }))} /></Grid>
              <Grid item xs={12} md={2}><TextField fullWidth label="3sg" value={grammar.agreement_3sg} onChange={(event) => setGrammar((prev) => ({ ...prev, agreement_3sg: event.target.value }))} /></Grid>
              <Grid item xs={12} md={2}><TextField fullWidth label="1pl" value={grammar.agreement_1pl} onChange={(event) => setGrammar((prev) => ({ ...prev, agreement_1pl: event.target.value }))} /></Grid>
              <Grid item xs={12} md={2}><TextField fullWidth label="2pl" value={grammar.agreement_2pl} onChange={(event) => setGrammar((prev) => ({ ...prev, agreement_2pl: event.target.value }))} /></Grid>
              <Grid item xs={12} md={2}><TextField fullWidth label="3pl" value={grammar.agreement_3pl} onChange={(event) => setGrammar((prev) => ({ ...prev, agreement_3pl: event.target.value }))} /></Grid>

              <Grid item xs={12} md={4}><TextField fullWidth label="Negation Particle" value={grammar.negation_particle} onChange={(event) => setGrammar((prev) => ({ ...prev, negation_particle: event.target.value }))} /></Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  select
                  label="Negation Position"
                  value={grammar.negation_position}
                  onChange={(event) => setGrammar((prev) => ({ ...prev, negation_position: event.target.value }))}
                >
                  <MenuItem value="before_verb">before verb</MenuItem>
                  <MenuItem value="after_verb">after verb</MenuItem>
                  <MenuItem value="clause_final">clause final</MenuItem>
                </TextField>
              </Grid>
              <Grid item xs={12} md={4}>
                <FormControlLabel
                  control={<Switch checked={grammar.replace_lexical_negation} onChange={(event) => setGrammar((prev) => ({ ...prev, replace_lexical_negation: event.target.checked }))} />}
                  label="Replace Lexical Negation"
                />
              </Grid>

              <Grid item xs={12} md={6}><TextField fullWidth label="Question Particle" value={grammar.question_particle} onChange={(event) => setGrammar((prev) => ({ ...prev, question_particle: event.target.value }))} /></Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  select
                  label="Question Particle Position"
                  value={grammar.question_particle_position}
                  onChange={(event) => setGrammar((prev) => ({ ...prev, question_particle_position: event.target.value }))}
                >
                  <MenuItem value="clause_initial">clause initial</MenuItem>
                  <MenuItem value="clause_final">clause final</MenuItem>
                </TextField>
              </Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>

        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <FormControlLabel onClick={(event) => event.stopPropagation()} onFocus={(event) => event.stopPropagation()} control={<Switch checked={enabled.wordgen} onChange={handleToggle('wordgen')} />} label="Word Generator" />
          </AccordionSummary>
          <AccordionDetails>
            <Grid container spacing={1.5}>
              <Grid item xs={12} md={4}><TextField fullWidth label="Prefix Probability" value={wordgen.prefix_prob} onChange={(event) => setWordgen((prev) => ({ ...prev, prefix_prob: event.target.value }))} /></Grid>
              <Grid item xs={12} md={4}><TextField fullWidth label="Suffix Probability" value={wordgen.suffix_prob} onChange={(event) => setWordgen((prev) => ({ ...prev, suffix_prob: event.target.value }))} /></Grid>
              <Grid item xs={12} md={4}><TextField fullWidth label="Max Attempts" value={wordgen.max_gen_attempts} onChange={(event) => setWordgen((prev) => ({ ...prev, max_gen_attempts: event.target.value }))} /></Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>

        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <FormControlLabel onClick={(event) => event.stopPropagation()} onFocus={(event) => event.stopPropagation()} control={<Switch checked={enabled.namegen} onChange={handleToggle('namegen')} />} label="Name Generator" />
          </AccordionSummary>
          <AccordionDetails>
            <Grid container spacing={1.5}>
              <Grid item xs={12} md={4}><TextField fullWidth label="Person Min Syllables" value={namegen.person_min_syl} onChange={(event) => setNamegen((prev) => ({ ...prev, person_min_syl: event.target.value }))} /></Grid>
              <Grid item xs={12} md={4}><TextField fullWidth label="Person Max Syllables" value={namegen.person_max_syl} onChange={(event) => setNamegen((prev) => ({ ...prev, person_max_syl: event.target.value }))} /></Grid>
              <Grid item xs={12} md={4}><TextField fullWidth label="Place Min Syllables" value={namegen.place_min_syl} onChange={(event) => setNamegen((prev) => ({ ...prev, place_min_syl: event.target.value }))} /></Grid>
              <Grid item xs={12} md={4}><TextField fullWidth label="Place Max Syllables" value={namegen.place_max_syl} onChange={(event) => setNamegen((prev) => ({ ...prev, place_max_syl: event.target.value }))} /></Grid>
              <Grid item xs={12} md={4}><TextField fullWidth label="Thing Min Syllables" value={namegen.thing_min_syl} onChange={(event) => setNamegen((prev) => ({ ...prev, thing_min_syl: event.target.value }))} /></Grid>
              <Grid item xs={12} md={4}><TextField fullWidth label="Thing Max Syllables" value={namegen.thing_max_syl} onChange={(event) => setNamegen((prev) => ({ ...prev, thing_max_syl: event.target.value }))} /></Grid>
              <Grid item xs={12}><TextField fullWidth label="Male Suffixes (csv)" value={namegen.person_male_suffixes} onChange={(event) => setNamegen((prev) => ({ ...prev, person_male_suffixes: event.target.value }))} /></Grid>
              <Grid item xs={12}><TextField fullWidth label="Female Suffixes (csv)" value={namegen.person_female_suffixes} onChange={(event) => setNamegen((prev) => ({ ...prev, person_female_suffixes: event.target.value }))} /></Grid>
              <Grid item xs={12}><TextField fullWidth label="Neutral Suffixes (csv)" value={namegen.person_neutral_suffixes} onChange={(event) => setNamegen((prev) => ({ ...prev, person_neutral_suffixes: event.target.value }))} /></Grid>
              <Grid item xs={12}><TextField fullWidth label="Place Suffixes (csv)" value={namegen.place_suffixes} onChange={(event) => setNamegen((prev) => ({ ...prev, place_suffixes: event.target.value }))} /></Grid>
              <Grid item xs={12}><TextField fullWidth label="Thing Suffixes (csv)" value={namegen.thing_suffixes} onChange={(event) => setNamegen((prev) => ({ ...prev, thing_suffixes: event.target.value }))} /></Grid>
              <Grid item xs={12} md={3}><TextField fullWidth label="Person Suffix Prob" value={namegen.person_suffix_prob} onChange={(event) => setNamegen((prev) => ({ ...prev, person_suffix_prob: event.target.value }))} /></Grid>
              <Grid item xs={12} md={3}><TextField fullWidth label="Place Suffix Prob" value={namegen.place_suffix_prob} onChange={(event) => setNamegen((prev) => ({ ...prev, place_suffix_prob: event.target.value }))} /></Grid>
              <Grid item xs={12} md={3}><TextField fullWidth label="Thing Suffix Prob" value={namegen.thing_suffix_prob} onChange={(event) => setNamegen((prev) => ({ ...prev, thing_suffix_prob: event.target.value }))} /></Grid>
              <Grid item xs={12} md={3}><TextField fullWidth label="Max Attempts" value={namegen.max_attempts} onChange={(event) => setNamegen((prev) => ({ ...prev, max_attempts: event.target.value }))} /></Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>

        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <FormControlLabel onClick={(event) => event.stopPropagation()} onFocus={(event) => event.stopPropagation()} control={<Switch checked={enabled.quality} onChange={handleToggle('quality')} />} label="Quality + Evaluator" />
          </AccordionSummary>
          <AccordionDetails>
            <TextField fullWidth label="Min Pronounceability Score" value={quality.min_pronounceability_score} onChange={(event) => setQuality((prev) => ({ ...prev, min_pronounceability_score: event.target.value }))} />
          </AccordionDetails>
        </Accordion>

        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <FormControlLabel onClick={(event) => event.stopPropagation()} onFocus={(event) => event.stopPropagation()} control={<Switch checked={enabled.soundRules} onChange={handleToggle('soundRules')} />} label="Custom Sound-Change Rules (JSON)" />
          </AccordionSummary>
          <AccordionDetails>
            <TextField fullWidth multiline minRows={5} label="JSON Rules Array" value={soundRules} onChange={(event) => setSoundRules(event.target.value)} />
          </AccordionDetails>
        </Accordion>

        <Stack direction="row" spacing={1.5}>
          <Button variant="contained" onClick={handleGenerate}>Generate With Selected Sections</Button>
        </Stack>
      </Stack>
    </Paper>
  );
}
