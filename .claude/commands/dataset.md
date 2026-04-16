---
description: Generate large synthetic datasets — N documents x M photo variations. For OCR training, vision benchmarks, agentic test suites.
---

# Generate Dataset

Create large-scale synthetic datasets for training and benchmarking.

## Modes

### 1. Single document, many variations
Generate 1 document with all 8 photo presets + custom variations:

```bash
cd $(pwd)
GEMINI_API_KEY=$GEMINI_API_KEY python3 -c "
import asyncio
from penquify.models import Document, DocHeader, DocItem, PhotoVariation, Stain, PRESETS
from penquify.generators.pdf import generate_document_files
from penquify.generators.photo import generate_dataset

doc = Document(
    header=DocHeader(doc_type='guia_despacho', doc_number='DS001', date='16/04/2026',
                     emitter_name='PROVEEDOR TEST', oc_number='4500000316'),
    items=[DocItem(pos=1, code='T-01', description='TEST ITEM', qty=100, unit='KG', unit_price=1000, total=100000)],
)

async def run():
    files = await generate_document_files(doc, 'dataset/doc_001')

    # All 8 presets
    await generate_dataset(files['png'], output_dir='dataset/doc_001/photos')

    # Plus custom hard cases
    hard = [
        PhotoVariation(name='extreme_blur', motion_blur=True, blur_direction='diagonal', jpeg_compression='heavy'),
        PhotoVariation(name='grease_stain', stain=Stain(type='grease', location='center', text_obstruction='severe')),
        PhotoVariation(name='night_flash', camera='Samsung Galaxy A10', glare='strong', glare_location='center', uneven_lighting=True),
        PhotoVariation(name='rain_damage', stain=Stain(type='water', location='random', opacity='heavy'), wrinkles='heavy'),
    ]
    await generate_dataset(files['png'], variations=hard, output_dir='dataset/doc_001/photos_hard')

asyncio.run(run())
"
```

### 2. Many documents, standard variations
Generate N documents with different content, each with M photos:

```python
import asyncio
from penquify.models import Document, DocHeader, DocItem
from penquify.generators.pdf import generate_document_files
from penquify.generators.photo import generate_dataset

SUPPLIERS = ['COMERCIAL AGRO SUR', 'AVICOLA CENTRAL', 'DISTRIBUIDORA PACIFICO']
ITEMS_POOL = [
    ('FRUTILLA FRESCA', 'KG', 5990), ('PAPA PREFRITA', 'CJ', 15000),
    ('MOZZARELLA', 'KG', 4900), ('COCA COLA 350CC', 'UN', 890),
    ('POLLO PECHUGA', 'KG', 5890), ('SERVILLETA ESTANDAR', 'UN', 1500),
]

async def generate_batch(n_docs=10, presets=['full_picture', 'folded_skewed', 'blurry']):
    import random
    for i in range(n_docs):
        n_items = random.randint(3, 8)
        items = [DocItem(pos=j+1, code=f'X-{j:03d}',
                         description=it[0], qty=random.randint(1, 50),
                         unit=it[1], unit_price=it[2])
                 for j, it in enumerate(random.sample(ITEMS_POOL, min(n_items, len(ITEMS_POOL))))]

        doc = Document(
            header=DocHeader(doc_type='guia_despacho',
                             doc_number=f'{10000+i}',
                             date='16/04/2026',
                             emitter_name=random.choice(SUPPLIERS),
                             oc_number=f'450000{i:04d}'),
            items=items,
        )

        out = f'dataset/batch/doc_{i:04d}'
        files = await generate_document_files(doc, out)
        await generate_dataset(files['png'], output_dir=f'{out}/photos', preset_names=presets)
        print(f'[{i+1}/{n_docs}] {doc.header.doc_number}: {len(items)} items, {len(presets)} photos')

asyncio.run(generate_batch(n_docs=10))
```

### 3. Benchmark matrix
Generate every combination of document x variation for systematic testing:

```python
from penquify.models import PhotoVariation, Stain, PRESETS
from itertools import product

# Axes to vary
cameras = ['galaxy_s7', 'galaxy_a10', 'iphone_12']
angles = ['straight', 'slight oblique', '45 degree oblique']
damages = [None, Stain(type='coffee'), Stain(type='water')]
blurs = [False, True]

variations = []
for cam, angle, damage, blur in product(cameras, angles, damages, blurs):
    name = f'{cam}_{angle.replace(" ","_")}_{damage.type if damage else "clean"}_{\"blur\" if blur else \"sharp\"}'
    variations.append(PhotoVariation(
        name=name, camera=cam, angle=angle,
        stain=damage, motion_blur=blur,
    ))

print(f'{len(variations)} variations in matrix')
# → 54 variations (3 cameras x 3 angles x 3 damages x 2 blurs)
```

## Output structure
```
dataset/
  doc_0000/
    guia_despacho_10000.html
    guia_despacho_10000.png    ← ground truth clean
    guia_despacho_10000.pdf
    photos/
      photo_full_picture.png
      photo_folded_skewed.png
      photo_blurry.png
  doc_0001/
    ...
```

## Upload to S3
```python
from penquify.storage.s3 import upload_directory
upload_directory('dataset/', 'my-bucket', 'penquify/datasets/run_001/')
```
