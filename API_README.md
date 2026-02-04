# Valve Datasheet Automation API

REST API for generating valve datasheets from VDS numbers.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the API Server

```bash
python run_api.py
```

Or with custom options:

```bash
python run_api.py --host 0.0.0.0 --port 8000 --reload
```

### 3. Access the API

- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/health

## API Endpoints

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check with data loading status |

### VDS Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/vds/{vds_no}/decode` | Decode VDS number into components |
| GET | `/api/vds/{vds_no}/validate` | Validate VDS number format |

### Datasheet Generation

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/datasheet/{vds_no}` | Generate complete datasheet with traceability |
| GET | `/api/datasheet/{vds_no}/flat` | Generate flat datasheet (values only) |
| POST | `/api/datasheet/generate` | Generate datasheet (POST method) |
| POST | `/api/datasheet/batch` | Batch generate multiple datasheets |

### Metadata

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/metadata` | Get all metadata for form dropdowns |
| GET | `/api/metadata/valve-types` | List supported valve types |
| GET | `/api/metadata/piping-classes` | List available piping classes |
| GET | `/api/metadata/vds-numbers` | List indexed VDS numbers |
| GET | `/api/metadata/end-connections` | List end connection types |
| GET | `/api/metadata/bore-types` | List bore types |

## Example Usage

### Decode VDS Number

```bash
curl http://localhost:8000/api/vds/BSFA1R/decode
```

Response:
```json
{
  "raw_vds": "BSFA1R",
  "valve_type_prefix": "BS",
  "valve_type_name": "Ball Valve",
  "valve_type_full": "Ball Valve, Full Bore",
  "bore_type": "F",
  "bore_type_name": "Full Bore",
  "piping_class": "A1",
  "end_connection": "R",
  "end_connection_name": "RF",
  "is_nace_compliant": false,
  "is_low_temp": false,
  "is_metal_seated": false,
  "primary_standard": "API 6D"
}
```

### Generate Datasheet

```bash
curl http://localhost:8000/api/datasheet/BSFA1R
```

Response includes:
- `metadata`: Generation info, validation status, completion percentage
- `sections`: Fields organized by section (Header, Design, Material, etc.)

### Get Metadata for UI Forms

```bash
curl http://localhost:8000/api/metadata
```

Response:
```json
{
  "valve_types": [
    {"prefix": "BS", "name": "Ball Valve", "standards": ["API 6D", "ISO 17292"]}
  ],
  "piping_classes": ["A1", "A2", "B1", "B2", "C1"],
  "end_connections": [
    {"code": "R", "name": "RF"},
    {"code": "J", "name": "RTJ"}
  ],
  "bore_types": [
    {"code": "F", "name": "Full Bore"},
    {"code": "R", "name": "Reduced Bore"}
  ],
  "pressure_classes": ["150", "300", "600", "900", "1500", "2500"]
}
```

### Batch Generation

```bash
curl -X POST http://localhost:8000/api/datasheet/batch \
  -H "Content-Type: application/json" \
  -d '{"vds_numbers": ["BSFA1R", "BSFA2R", "GSFA1R"]}'
```

## Frontend Integration

### React Query Hooks

Import hooks from `@/hooks/use-datasheet-api`:

```tsx
import {
  useMetadata,
  useDatasheet,
  useDecodeVDS,
  useValidateVDS,
  useGenerateDatasheetMutation
} from "@/hooks/use-datasheet-api";

function MyComponent() {
  // Get metadata for dropdowns
  const { data: metadata } = useMetadata();

  // Generate datasheet
  const { data: datasheet, isLoading } = useDatasheet("BSFA1R");

  // Decode VDS on input
  const { data: decoded } = useDecodeVDS(vdsInput);

  return (
    // Use the data...
  );
}
```

### Direct API Calls

Import from `@/services/api`:

```tsx
import api from "@/services/api";

// Decode VDS
const decoded = await api.decodeVDS("BSFA1R");

// Generate datasheet
const datasheet = await api.generateDatasheet("BSFA1R");

// Get metadata
const metadata = await api.getMetadata();
```

## Environment Variables

### Frontend (.env)

```env
VITE_API_URL=http://localhost:8000/api
```

## CORS Configuration

The API allows requests from:
- `http://localhost:3000` (React dev server)
- `http://localhost:5173` (Vite dev server)
- `http://localhost:8080`

For production, update CORS settings in `valve_datasheet_automation/api/main.py`.
