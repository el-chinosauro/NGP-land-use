"""
author: lorenzo
date: 09/06/2025
project: philippines-ngp-landuse
script: TEST extract EU TMF data accounting for plantations
"""

# Load libraries
import ee

# 1. Initialize Earth Engine
ee.Initialize(project='philippines-ngp')

# 2. How many villages for the smoke-test? Change to 50, 100, etc.
N_TEST = 50

# 3. Load and subset villages
villages_all  = ee.FeatureCollection('projects/philippines-ngp/assets/barangays')
villages      = villages_all.limit(N_TEST)
test_area     = villages.geometry()

# 4. Load plantations and filter to those overlapping the test villages
plantations_all = ee.FeatureCollection('projects/philippines-ngp/assets/NGP_valid')
plantations     = plantations_all.filterBounds(test_area)

# 5. TMF annual‐change dataset and class mapping
tmf = ee.ImageCollection('projects/JRC/TMF/v1_2023/AnnualChanges')
class_names = {
    1: "share_undisturbed_tmf",
    2: "share_degraded_tmf",
    3: "share_deforested_tmf",
    4: "share_regrowth_tmf",
    5: "share_water_tmf",
    6: "share_other_tmf"
}

def year_stats(year):
    band = f'Dec{year}'
    # a) pick that year’s classification band
    clas = tmf.select(band).first()
    
    # b) one binary band per class
    binaries = [
        clas.eq(cls).rename(prop).toFloat()
        for cls, prop in class_names.items()
    ]
    
    # c) pixel counter
    pixel = ee.Image.constant(1).rename('pixel')
    
    # d) build plantation mask (cumulative YEAR ≤ current year) and splits
    if year >= 2011:
        pl_mask = (
            plantations
              .filter(ee.Filter.lte('YEAR', year))
              .reduceToImage([], ee.Reducer.constant(1))
              .unmask(0)
              .rename('in_pl')
              .toFloat()
        )
        in_bands  = [b.multiply(pl_mask).rename(f"{n}_in")
                     for b,n in zip(binaries, class_names.values())]
        out_bands = [b.multiply(pl_mask.Not()).rename(f"{n}_out")
                     for b,n in zip(binaries, class_names.values())]
        img = pixel.addBands(binaries + in_bands + out_bands)
    else:
        img = pixel.addBands(binaries)

    # e) sum over the test villages
    sums = img.reduceRegions(
        collection=villages,
        reducer=ee.Reducer.sum(),
        scale=30
    )
    
    # f) convert sums into shares
    def to_shares(f):
        props     = {'year': year}
        total_pix = ee.Number(f.get('pixel_sum'))
        # full‐village shares
        for name in class_names.values():
            cnt = ee.Number(f.get(f"{name}_sum"))
            props[name] = cnt.divide(total_pix)
        # in/out shares for ≥2011
        if year >= 2011:
            for name in class_names.values():
                cin = ee.Number(f.get(f"{name}_in_sum"))
                cout = ee.Number(f.get(f"{name}_out_sum"))
                props[f"{name}_in"]  = cin.divide(total_pix)
                props[f"{name}_out"] = cout.divide(total_pix)
        return f.set(props)
    
    return sums.map(to_shares)

# 6. Run for 2000–2023 and merge all years
years = list(range(2000, 2024))
test_col = ee.FeatureCollection([year_stats(y) for y in years]).flatten()

# 7. Export as GeoJSON
task = ee.batch.Export.table.toDrive(
    collection       = test_col,
    description      = f'TEST_{N_TEST}Villages_TMF_2000_2023',
    folder           = 'philippines-ngp-landuse-test',
    fileNamePrefix   = f'test_{N_TEST}_barangays_TMF_2000_2023',
    fileFormat       = 'GeoJSON'
)
task.start()
print("Test export started; task ID =", task.id)
