"""
author: lorenzo
date: 09/06/2025
project: philippines-ngp-landuse
script: EU TMF onto barangays (2000–2010) and plantation×village (2011–2023)
"""

import ee
import time

# 1. Initialize EE
ee.Initialize(project='philippines-ngp')

# 2. Load collections
villages    = ee.FeatureCollection('projects/philippines-ngp/assets/barangays')
plantations = (
    ee.FeatureCollection('projects/philippines-ngp/assets/NGP_valid')
      .map(lambda f: f.set('YEAR', ee.Number.parse(f.get('YEAR'))))
)

# 3. TMF dataset and bands
tmf_dataset = ee.ImageCollection('projects/JRC/TMF/v1_2023/AnnualChanges')
band_names  = tmf_dataset.first().bandNames().getInfo()
print("TMF band names:", band_names)

# 4. TMF class → property mapping
class_names = {
    1: "share_undisturbed_tmf",
    2: "share_degraded_tmf",
    3: "share_deforested_tmf",
    4: "share_regrowth_tmf",
    5: "share_water_tmf",
    6: "share_other_tmf"
}

# 5. Core extractor: takes any feature (village or clipped piece) + year
def extract_data(feat, year):
    band = f"Dec{year}"
    # mosaic all continent-tiles so PH is covered
    image = tmf_dataset.select(band).mean()
    geom  = feat.geometry()

    # total pixels
    tot_dict   = ee.Image.constant(1).rename("one") \
                    .reduceRegion(ee.Reducer.sum(), geom, 30, 1e13)
    total_pix  = ee.Number(ee.Algorithms.If(tot_dict.get("one"),
                                            tot_dict.get("one"),
                                            0))
    stats = {}
    # per-class counts → safe shares
    for cls, prop in class_names.items():
        cls_dict = image.eq(cls).rename("bin") \
                       .reduceRegion(ee.Reducer.sum(), geom, 30, 1e13)
        cls_cnt  = ee.Number(ee.Algorithms.If(cls_dict.get("bin"),
                                             cls_dict.get("bin"),
                                             0))
        share    = ee.Algorithms.If(total_pix.gt(0),
                                   cls_cnt.divide(total_pix),
                                   0)
        stats[prop] = share

    return feat.set(stats).set("year", year)


# 6. Helper: split plantations into pieces clipped by village
def splitPlantByVillage(pl):
    touch = villages.filterBounds(pl.geometry())
    def clipFn(v):
        v = ee.Feature(v)
        geom_clip = pl.geometry().intersection(v.geometry(), 1)
        return ee.Feature(geom_clip) \
                 .set({
                   'plantation_id': pl.get('system:index'),
                   'village_id':    v.get('system:index'),
                   'YEAR':          pl.get('YEAR')
                 })
    return touch.map(clipFn)


# 7. Loop years and dispatch two modes:
tasks = []
for band in band_names:
    year = int(band.replace("Dec", ""))
    # ——— 2000–2010: village-only run ———
    if 2000 <= year < 2011:
        print(f"Running village-only TMF for {year}…")
        out_fc = villages.map(lambda f: extract_data(f, year)
                                       .set('village_id', f.get('system:index')))
        props  = ['village_id','year'] + list(class_names.values())
        out_fc = out_fc.select(props)

        task = ee.batch.Export.table.toDrive(
            collection     = out_fc,
            description    = f'villages_TMF_{year}',
            folder         = 'philippines-ngp-landuse/eu-tmf-village',
            fileNamePrefix = f'villages_TMF_{year}',
            fileFormat     = 'GeoJSON'
        )
        task.start()
        tasks.append(task)

    # ——— 2011–2023: plantation×village run ———
    elif year >= 2011:
        print(f"Running plantation×village TMF for {year}…")
        # a) keep all plantations established up to this year
        pl_up     = plantations.filter(ee.Filter.lte('YEAR', year))
        # b) clip each to villages
        pieces_fc = ee.FeatureCollection(pl_up.map(splitPlantByVillage)).flatten()
        # c) extract TMF shares on each piece
        stats_fc  = pieces_fc.map(lambda f: extract_data(f, year))
        # d) select key props
        props     = ['plantation_id','village_id','year'] + list(class_names.values())
        stats_fc  = stats_fc.select(props)

        task = ee.batch.Export.table.toDrive(
            collection     = stats_fc,
            description    = f'plantations_vill_TMF_{year}',
            folder         = 'philippines-ngp-landuse/eu-tmf-plant',
            fileNamePrefix = f'plantations_villages_TMF_{year}',
            fileFormat     = 'GeoJSON'
        )
        task.start()
        tasks.append(task)

print("Submitted", len(tasks), "tasks. IDs:", [t.id for t in tasks])
