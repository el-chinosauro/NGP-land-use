###################################
# author: lorenzo
# date: 24/04/2025
# project: NGP-land-use
# script: shapefiles inspection
###################################

# import libraries
library(here)
library(sf)
sf_use_s2(F)

# relative paths
raw_data = here("data/raw-data")
constructed_data = here("data/constructed-data")
figures = here("figures")

# import NGP shapes
ngp_shapes = st_read(here(raw_data, "ngp-shapefiles", "valid_NGP_shapefiles.gpkg"))

# mapview to inspect
mapview::mapview(ngp_shapes)