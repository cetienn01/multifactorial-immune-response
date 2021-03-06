

# A Multifactorial Model of T Cell Expansion and Durable Clinical Benefit in Response to a PD-L1 Inhibitor
<img src='https://travis-ci.org/lrgr/multifactorial-immune-response.svg?branch=master'>

This repository contains the source code for reproducing the experiments and figures from Leiserson, et al. (bioRxiv, 2017). See the [references section](#references) below for more information on the paper.

We use continuous integration to automatically regenerate the figures whenever there is a push to the master branch. You can see the [current figures below](#figures). Note that, for runtime purposes, by default we do not run the permutation test, and thus the automatically generated Figure 1b will be different from the one in the paper.

### Setup

#### Dependencies
The methods and experiments are written in Python 3. We recommend using Conda to manage dependencies, which you can do directly using the provided `environment.yml` file:

    conda env create -f environment.yml
    source activate multifactorial-immune-response-env

### Usage

We use [`snakemake`](https://snakemake.readthedocs.io/en/latest/) to run a pipeline of commands to download and process data, run experiments, and create the figures. To run the entire pipeline, simply run:

    snakemake all

#### Configuration

Configuration for the entire pipeline is controlled by the variables in `configs/default.yml`. The following variables can be set:

| Variable name     | Choices                | Default    |  Value used in paper   |
|-------------------|------------------------|------------|------------------------|
| `model`           | `'en'`, `'rf'`         | `'en'`     | Both `'en'` and `'rf'` |
| `n_permutations`  | Positive int           | `0`        | `1000`                 |
| `max_iter`        | Positive int           | `1000000`  | `1000000`              |
| `tol`             | Positive real          | `1e-7`     | `1e-7`                 |
| `random_seed`     | Positive int           | `12345`    | `12345`                |
| `n_jobs`          | Positive int           | `1`        | `46`                   |
| `figure_format`   | Standard image formats | png        | png                    |

The configuration values used in the paper are stored for convenience in `configs/paper.yml`. To use that configuration, change the first line of the `Snakefile` accordingly.

### Support

Please report bugs and feature requests in the [Issues tab](https://github.com/lrgr/multifactorial-immune-response/issues) of this GitHub repository.

For further questions, please email [Max Leiserson](mailto:mdml@cs.umd.edu) and [Lester Mackey](mailto:lmackey@microsoft.com) directly.

### References

Mark DM Leiserson, Vasilis Syrgkanis, Amy Gilson, Miroslav Dudik, Dean F Bajorin, Jonathan Rosenberg, Samuel Funt, Alexandra Snyder, Lester Mackey. (2018) A Multifactorial Model of T Cell Expansion and Durable Clinical Benefit in Response to a PD-L1 Inhibitor. _In submission_ [[bioRxiv preprint]](https://www.biorxiv.org/content/early/2018/01/18/231316).

### Figures

<img src='http://multifactorial-immune-response.lrgr.io/fig1.png'>

**Figure 1**: (a) Predicted log TIL expansion versus ground-truth log TIL expansion for patients held out using LOOCV.  Predictions are formed using the elastic net. (b) Histogram of LOOCV error when patient responses are permuted uniformly at random 1000 times (for runtime purposes, we do not perform these permutations by default for these automatically generated figures).  The overlaid dotted line displays the LOOCV error obtained on the original dataset.

 <img src='http://multifactorial-immune-response.lrgr.io/fig2.png?raw=true'>

**Figure 2**: Learned elastic net coefficients and feature types.

<img src='http://multifactorial-immune-response.lrgr.io/fig3.png?raw=true'>

**Figure 3**: Distributions of biomarker values in patients with and without durable clinical benefit (DCB, defined as ≥ 6 months of progression-free survival): (a) predicted number of expanded TIL clones; (b) missense SNV count; (c) expressed neoantigen count; and, (d) percentage of tumor infiltrating immune cells found to be PD-L1-positive. When each biomarker alone is used for triage, the patients highlighted in red must be treated to ensure all DCB patients are treated.
