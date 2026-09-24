# Changelog

## 0.1.0 — 2026-09-24

First tagged version.

- CMS and ATLAS templates derived from mplhep's rcParams; `style.use`, `figure` (with proportional scaling to any size), `template_json`, `export-templates` CLI.
- `histplot` (step, fill, errorbar; errors, stacking, density, multiple histograms) and `hist2dplot`, each bin with hover.
- `exp_text` / `exp_label` with mplhep's five `loc` positions; `cms` and `atlas` namespaces; `set_xlabel` / `set_ylabel`.
- `ratio_figure` / `ratioplot` / `gridspec_domains` on matplotlib GridSpec geometry.
- `html.script_tag` / `html.embed`: frozen figures with an edit chip, persisted edits, page-level theme.
- `convert.from_mpl` / `convert.to_mpl`.
- `root_template` and the ROOT tutorial rebuilds in the gallery.
- Test suite in mplhep's layout with image baselines; pixel harnesses against mplhep and ROOT.
