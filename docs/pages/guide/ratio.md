# Ratio panels

`ratio_figure` lays two panels out exactly as matplotlib's `GridSpec` would for the same
`height_ratios` and `hspace`; the test suite checks the domains against matplotlib itself.
The panels share the x axis, tick labels appear only below, and the lower panel has its
range, title and a dashed line at one.

```python
fig = php.ratio_figure("CMS", height_ratios=(3, 1), hspace=0.05, ratio_range=(0.5, 1.5), ratio_title="Data / MC")
php.histplot(fig, mc, bins, label="MC")
php.histplot(fig, data, bins, yerr=True, histtype="errorbar", color="black", label="Data")
php.ratioplot(fig, data, mc, bins, den_w2=mc)      # points with the numerator's errors, MC band around 1
```

`ratioplot(fig, num, den, bins, *, num_w2=None, den_w2=None, band=True, color="black", label=None)`
divides bin by bin (empty denominators become gaps), takes the numerator's Poisson error or
`num_w2`, and draws the denominator's relative statistical uncertainty as a band around one
when `den_w2` is given. Hover a ratio point for the numbers behind it.

Anything else goes into the lower panel with `row=2` on `histplot`, or with
`xaxis="x2", yaxis="y2"` on a trace of your own. `php.gridspec_domains(height_ratios, hspace)`
returns the vertical domains for more than two panels.
