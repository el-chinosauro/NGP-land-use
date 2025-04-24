# NGP Land Use and Biodiversity

This repository contains the analysis code and documentation for the NGP-land-use project by J.Pagel, L. Sileci and C.Palmer. It is designed to be portable across machines using relative paths, ensuring reproducible workflows for all collaborators.

## Current project structure

```
NGP-land-use/
├── data/
│   ├── raw-data/
│   └── constructed-data/
├── figures/
├── NGP-land-use.Rproj
└── NGP-land-use-github/
    ├── r-code/
    └── py-code/
```

- **data/**: raw and processed datasets.
- **figures/**: output plots.
- **NGP-land-use.Rproj**: RStudio project file, sets project root automatically.
- **NGP-land-use-github/**: GitHub-synced code, with separate folders for R and Python scripts.

## Prerequisites

- **R** (>= 4.x) and optionally **RStudio**.
- **Python** (>= 3.x).
- R packages: `here` (optional), plus any others listed in `r-code/renv.lock` or `r-code/packages.R`.
- Python packages: `pandas`, `matplotlib`, and any others in `py-code/requirements.txt`.

## 1. Open the project

- **RStudio**: File → Open Project…, select `NGP-land-use.Rproj`.
- **Command line**: `cd /path/to/NGP-land-use` (ensure you’re at the project root).

## 2. Verify the working directory

- In R:
  ```r
  getwd()
  # Should point to the project root (where NGP-land-use.Rproj lives)
  ```
- In shell:
  ```bash
  pwd
  # Should print /path/to/NGP-land-use
  ```

*All relative paths in scripts assume the working directory is the project root.*

## 3. Reading and writing files

### A) R using base functions

```r
# Read raw data
infile <- file.path("data", "raw-data", "observations.csv")
df_raw <- read.csv(infile)

# Write cleaned data
outfile <- file.path("data", "constructed-data", "observations_clean.csv")
write.csv(df_raw, outfile, row.names = FALSE)

# Save a plot
plot_file <- file.path("figures", "exploratory", "scatter_raw.png")
png(plot_file)
plot(df_raw$x, df_raw$y)
dev.off()
```

### B) R using the **here** package (analogous)

```r
library(here)
# here() auto-detects project root via .Rproj or Git

df_raw <- read.csv(here("data", "raw-data", "observations.csv"))
write.csv(df_raw, here("data", "constructed-data", "observations_clean.csv"), row.names = FALSE)

ggsave(here("figures", "exploratory", "scatter_raw.png"), plot = last_plot())
```

### C) Python using **pathlib**

```python
from pathlib import Path
# PROJECT_ROOT = two levels up from this script's location
dir_path = Path(__file__).resolve().parents[2]

raw_csv = dir_path / "data" / "raw-data" / "observations.csv"
import pandas as pd
df = pd.read_csv(raw_csv)

# Save a figure
fig_path = dir_path / "figures" / "draft" / "my_plot.png"
# (plotting code...)
import matplotlib.pyplot as plt
plt.savefig(fig_path)
```

## 4. Tips for smooth collaboration

- **Never hardcode** absolute paths in code.
- Use `dir.create(file.path(...), recursive = TRUE, showWarnings = FALSE)` in R to create needed folders.
- Document new dependencies by updating `requirements.txt`, `environment.yml`, or `renv.lock`.
- Avoid committing large raw datasets to Git; sync data via Dropbox.
- Keep this README up to date with any additional instructions or folder changes.
- No whitespace in file names
- No Caps in file names

---
