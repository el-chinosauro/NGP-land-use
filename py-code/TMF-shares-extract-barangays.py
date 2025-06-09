"""
author: lorenzo
date: 09/06/2025
project: philippines-ngp-landuse
script: extract EU TMF data accounting for plantations
"""

# Load libraries
import ee

# 1. Initialize Earth Engine
ee.Initialize(project='philippines-ngp')

# 2. Assets
villages    = ee.FeatureCollection('projects/philippines-ngp/assets/barangays')
plantations = ee.FeatureCollection('projects/philippines-ngp/assets/NGP_valid')

# 3. TMF annual‐change dataset
tmf      = ee.ImageCollection('projects/JRC/TMF/v1_2023/AnnualChanges')
# Map TMF class → property name
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
    
    # b) make one binary band per class
    binaries = []
    for cls, prop in class_names.items():
        binaries.append(
            clas.eq(cls)
               .rename(prop)
               .toFloat()
        )
    
    # c) base image: total‐pixel counter
    pixel = ee.Image.constant(1).rename('pixel')
    
    # d) if year >=2011, build plantation mask
    if year >= 2011:
        pl_mask = (plantations
          .filter(ee.Filter.lte('YEAR', year)) #keeps year <= current year
          .reduceToImage([], ee.Reducer.constant(1))
          .unmask(0)
          .rename('in_pl')
          .toFloat()
        )
        # inside‐plant and outside‐plant binary bands
        in_bands  = [b.multiply(pl_mask).rename(f"{n}_in")  for b,n in zip(binaries, class_names.values())]
        out_bands = [b.multiply(pl_mask.Not()).rename(f"{n}_out") for b,n in zip(binaries, class_names.values())]
        img = pixel.addBands(binaries).addBands(in_bands).addBands(out_bands)
    else:
        # pre‐2011: we only need the total class shares
        img = pixel.addBands(binaries)

    # e) reduce over villages
    sums = img.reduceRegions(
        collection=villages,
        reducer=ee.Reducer.sum(),
        scale=30
    )
    
    # f) turn counts into shares
    def to_shares(f):
        out = ee.Dictionary({'year': year})
        total_pix = ee.Number(f.get('pixel_sum'))
        # always add full‐village shares
        for prop in class_names.values():
            cnt = ee.Number(f.get(f'{prop}_sum'))
            out = out.set(prop, cnt.divide(total_pix))
        # if year>=2011, add the in/out shares
        if year >= 2011:
            for prop in class_names.values():
                cnt_in  = ee.Number(f.get(f'{prop}_in_sum'))
                cnt_out = ee.Number(f.get(f'{prop}_out_sum'))
                out = out.set(f'{prop}_in',  cnt_in.divide(total_pix))
                out = out.set(f'{prop}_out', cnt_out.divide(total_pix))
        return f.set(out)
    
    return sums.map(to_shares)

# 4. Run for 2000–2023
years = list(range(2000, 2024))
col   = ee.FeatureCollection([year_stats(y) for y in years]).flatten()

# 5. Export to Drive as one CSV
task = ee.batch.Export.table.toDrive(
    collection=col,
    description='barangays_TMF_2000_2023',
    folder='philippines-ngp-landuse',
    fileNamePrefix='barangays_TMF_2000_2023',
    fileFormat='GeoJSON'
)
task.start()
print("Started export, task ID =", task.id)
