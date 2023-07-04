# Finding the Optimal Design

## First and Foremost
[src_python/run_lookup_table.py](src_python/run_lookup_table.py)
Create lookup tables needed for creating and analysing designs.

## Designs

[src_python/run_bsp.py](src_python/run_bsp.py)
get BSP design with Python.
Check docstring for use.

[src_r/run_comined_eclair.R](src_r/run_comined_eclair.R)
get CoMinED and adaptive SCMC designs with R.

## Analysis

[src_python/run_fill_distance.py](src_python/run_fill_distance.py)
get filldistance analysis data.

## Figures

[src_python/analyse_figure_maximin.py](src_python/analyse_figure_maximin.py)
compare maximin desings

[src_python/analyse_figure_maxpro.py](src_python/analyse_figure_maxpro.py)
compare maxpro desings

[src_python/analyse_figure_filldistance.py](src_python/analyse_figure_filldistance.py)
filldistances for each design with both maximin and maxpro measures

[src_python/analyse_figure_distribution.py](src_python/analyse_figure_distribution.py)
compare density distribution of source vs designs with both maximin and maxpro measures.

## Testing

[src_python/test_bsp.py](src_python/test_bsp.py)
test bsp with a small number of points.

[src_python/test_sample_set_for_duplicates.py](src_python/test_sample_set_for_duplicates.py)
find out how many duplicates there is in the source dataset.

[src_python/test_source_for_constraints.py](src_python/test_source_for_constraints.py)
test if the source is valid conserning the constraints.

## Not in use in PhD


### Designs

[src_python/run_ga.py](src_python/run_ga.py)
maximin design with genetic algorithm.

[src_python/run_lhs.py](src_python/run_lhs.py)
get a latin hypercube design that meets the constraints.

### Figures

[src_python/analyse_figure_source_vs_sample_vs_design.py](src_python/analyse_figure_source_vs_sample_vs_design.py)
test how source, sampled source and design compare to each other.

### Tests

[src_python/run_hypercube_source_constraints_met.py](src_python/run_hypercube_source_constraints_met.py)
???