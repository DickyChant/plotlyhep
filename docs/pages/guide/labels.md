# Experiment labels

```python
php.cms.label(fig, "Preliminary", data=True, lumi=138, com=13.6)         # loc=0: above the axes
php.atlas.label(fig, "Internal", data=True, lumi=140, com=13.6, loc=4)   # ATLAS layout, lumi inside
php.exp_text(fig, "CMS", "Simulation", loc=2)                            # any experiment name
php.exp_label(fig, "CMS", data=False, com=13.6)                          # adds "Simulation" when data=False
```

The `loc` positions follow mplhep:

| loc | placement |
|---|---|
| 0 | above the axes: name and text on the left, lumi line on the right |
| 1 | inside the top-left corner, text beside the name |
| 2 | inside the top-left corner, text below the name |
| 3 | inside the top-left corner, text below, lumi line kept above the axes |
| 4 | the ATLAS layout: name, text and lumi line stacked inside |

Sizes keep mplhep's ratios: the experiment name is 1.3× the text, the lumi line 0.77×.
`rlabel=` replaces the generated lumi line with your own string, `year=` prepends the year,
`lumi_format="{0:.1f}"` controls the number, `com=None` drops the energy.

Every label is a Plotly annotation, so it stays draggable in the [editor](https://dickychant.github.io/plotlyhep/gallery/editor/)
and in [editable embeds](slides.md).
