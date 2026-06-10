"""Top-level package configuration for rsys_analyser."""

import polars as pl

# Apply a package-wide default for dataframe row display in repr/print output.
pl.Config.set_tbl_rows(100)
