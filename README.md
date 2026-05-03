# AZ Blockchain Analyzer

Bitcoin və Ethereum şəbəkələrində cüzdan ünvanlarını analiz edən veb tətbiq. Tranzaksiya tarixçəsini çəkir, ünvanlar arasındakı əlaqələri qraf şəklində göstərir, klasterləşmə aparır və risk qiymətləndirməsi verir.

Layihəyə baxmaq üçün: [blockchainanalyzer.com.az](https://blockchainanalyzer.com.az/)

---

## Proses

- İstifadəçi Bitcoin və ya Ethereum ünvanı daxil edir
- Backend həmin ünvanın tranzaksiya tarixçəsini BlockCypher (BTC) və Etherscan (ETH) API-lərindən çəkir
- Tranzaksiyalar əsasında yönlü qraf qurulur (ünvanlar düyünlər, tranzaksiyalar isə kənar xətlərdir)
- Çoxlu Giriş (CIO) evristikası ilə eyni sahibə aid ola biləcək ünvanlar klasterləşdirilir
- Çoxçıxışlı bölünmə (fan-out), tam ədəd köçürmələr, böyük klasterlər kimi şübhəli qanunauyğunluqlar aşkar olunur
- Tapılmış qanunauyğunluqlar əsasında 0-100 arası risk qiyməti hesablanır
- Frontend-də D3.js ilə interaktiv qraf qurulur
- Analiz nəticələri əsasında PDF hesabat yaradıla bilər

## Texnologiyalar

### Backend
- **Python**, **FastAPI** — REST API
- **NetworkX** — qraf analizi, klasterləşmə, statistika
- **ReportLab** — PDF hesabat yaradılması
- **Pydantic** — data təsdiqləməsi
- **aiohttp / requests** — blockchain API sorğuları

### Frontend
- **React 19** + **Vite**
- **D3.js** — tranzaksiya qrafının vizualizasiyası

### İnfrastruktur
- **Docker** + **Docker Compose** — konteynerləşmə
- **Nginx** — frontend üçün statik faylların paylanması

## Layihə strukturu

```
blockchain-analyzer/
├── backend/
│   ├── api.py              # FastAPI endpointlər
│   ├── fetcher.py          # BlockCypher/Etherscan-dan data çəkmə
│   ├── graph.py            # Qraf qurma, klasterləşmə, risk hesablama
│   ├── models.py           # Pydantic request/response modelləri
│   ├── report.py           # PDF hesabat yaradılması
│   ├── main.py             # CLI rejimi
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── dashboard.jsx   # Əsas analitika + D3 qraf
│   │   ├── index.css       # Stillər
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   ├── nginx.conf
│   └── Dockerfile
└── docker-compose.yml
```

## Quraşdırma

### Lokal işə salma

Backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn api:app --reload --port 8000
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

Frontend susmaya görə `http://localhost:8000` ünvanında backend axtarır. Dəyişmək lazımdırsa `VITE_API_URL` environment dəyişənini təyin edin.

### Docker ilə

```bash
docker compose up --build
```

Backend `localhost:8000`, frontend `localhost:3000` ünvanında qalxacaq.


## CLI rejimi

Backend-i API olmadan da terminal üzərindən istifadə etmək mümkündür:

```bash
cd backend
python main.py --btc 1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2
python main.py --eth 0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe
python main.py --demo
```

## Qeydlər

- BlockCypher və Etherscan-ın pulsuz API planlarının sorğu limiti var. Limit aşıldıqda interfeysdə bildiriş göstərilir.
- API əlçatmaz olduqda sistem avtomatik demo dataya keçir.
- Risk qiymətləndirməsi  evristik xarakter daşıyır, hüquqi sənəd qüvvəsi yoxdur.
- Layihə prototip mərhələsindədir.
