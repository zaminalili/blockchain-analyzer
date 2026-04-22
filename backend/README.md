# AZ Blockchain Analyzer — FastAPI Backend

Azərbaycan hüquq-mühafizə orqanları üçün blockchain kriminalistik API prototipi.  
Diplom işi: *"Kriptovalyuta ilə cinayətlərdə blokçeyn texnologiyalarının tətbiqi"*

---

## Quraşdırma

```bash
pip install -r requirements.txt
```

## Serveri işə salma

```bash
uvicorn api:app --reload --port 8000
```

Swagger UI: http://localhost:8000/docs  
ReDoc:       http://localhost:8000/redoc

---

## API Endpointləri

### `GET /health`
Server statusu.

### `GET /demo`
API key olmadan offline demo analiz.

### `POST /analyze`
Tək ünvan tam analizi.
```json
{
  "address": "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",
  "chain":   "BTC",
  "limit":   20
}
```

### `POST /analyze/batch`
Çox ünvana eyni vaxtda sorğu (max 10). Risk skoru üzrə sıralanmış cavab.

### `GET /address/{chain}/{address}`
Sürətli lookup — yalnız risk xülasəsi.  
Nümunə: `GET /address/BTC/1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2`

### `GET /graph/{chain}/{address}`
D3.js Force Graph üçün node + link data.

---

## Risk qiymətləndirmə məntiqi

| Skor   | Səviyyə | Tövsiyə                        |
|--------|---------|--------------------------------|
| 0–39   | Aşağı     | Adi monitorinq                 |
| 40–69  | Orta  | Əlavə araşdırma                |
| 70–100 | Yüksək    | Dərhal istintaq açılması       |

### Aşkarlanan qanunauyğunluqlar

| Qanunauyğunluq        | Ağırlıq | Açıqlama                              |
|----------------|---------|---------------------------------------|
| `FAN_OUT`      | 25      | 1 input → 5+ output (mixing əlaməti) |
| `LARGE_CLUSTER`| 30      | 3+ ünvan eyni sahibə aid              |
| `ROUND_NUMBER` | 10      | Tam ədəd köçürmə                      |
| `MIXER_ADDRESS`| 50      | Bilinən mixer ünvanı                  |

---

## Fayl strukturu

```
blockchain_analyzer/
├── api.py          ← FastAPI app
├── fetcher.py      ← BTC + ETH API çağırışları
├── graph.py        ← NetworkX analiz + risk scoring
├── models.py       ← Pydantic sxemləri
├── main.py         ← Terminal CLI
└── requirements.txt
```

