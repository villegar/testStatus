
<!-- README.md is generated from README.Rmd. Please edit that file -->

<a href='https://datashield.org'><img src='https://i0.wp.com/datashield.org/wp-content/uploads/2024/07/DS-logo-A4.png' alt='DataSHIELD logo' align='right' height=70px/></a>

# DataSHIELD packages tests’ status

<!-- badges: start -->

[![`dsbase` test
suite](https://github.com/villegar/dsBase/actions/workflows/dsBase_test_suite.yaml/badge.svg)](https://github.com/villegar/dsBase/actions/workflows/dsBase_test_suite.yaml)
<!-- badges: end -->

This repository contains scripts to aggregate
([source/parse_test_report.R](%22source/parse_test_report.R%22)) results
from [`{testthat}`](https://cran.r-project.org/package=testthat) and
[`{covr}`](https://cran.r-project.org/package=covr) packages (see the
workflow: <https://github.com/datashield/.github>). There is a script to
render ([source/render_docs.R](%22source/render_docs.R%22)) the results
committed by the pipeline to the [logs/](logs/) directory. Also, a
template for a Quarto report
([source/test_report.qmd](source/test_report.qmd)) to present the
results of the tests in a dashboard.

The workflow follows the following stream:

`Repository with unit tests` \>\>\> `Repository with results` \>\>\>
`GitHub pages`
