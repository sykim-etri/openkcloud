# kcloud-manage
# AI_SW_IDE

Dashboard application for GPU resource monitoring and management.


## Project Structure

```
AI_SW_IDE/
├── backend/           # FastAPI backend server
├── frontend/          # React frontend application
├── data_observer/     # NFS data monitoring servic
├── helm-chart/        # Helm chart for Kubernetes deployment
└── deploy.sh          # Legacy deployment script
```

## Components

### Backend (`backend/`)
- **Tech Stack**: FastAPI, Python
- **Features**: GPU resource monitoring API, database integration
- **Port**: 8000

### Frontend (`frontend/`)
- **Tech Stack**: React, Vite, TailwindCSS
- **Features**: Web-based dashboard UI
- **Port**: 80 (Nginx)

### Data Observer (`data_observer/`)
- **Tech Stack**: FastAPI, Python
- **Features**: NFS volume data monitoring and filesystem analysis
- **Port**: 8000

## Prerequisites
- DCGM Exporter
- Prometheus

## Kubernetes deployment

### using Helm Chart (Recommended)

To deploy to a Kubernetes cluster, use the `helm-chart/` folder:

```bash
cd helm-chart
./quick-start.sh
```

For more details, refer to [helm-chart/README.md](helm-chart/README.md).

### Key Features
- **Subchart Structure**: Backend, Frontend, and Data Observer are independent subcharts
- **PostgreSQL Integration**: Automatic installation of Bitnami PostgreSQL chart
- **NFS Volume Support**: Automatic NFS mounting for Data Observer
- **Ingress Support**: Ingress configuration for external access
- **Centralized Configuration**: All settings managed from the top-level values.yaml

## Local Development

### Backend Development
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Data Observer Development
```bash
cd data_observer
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### API Documentation

Each service provides auto-generated FastAPI documentation:

- Backend API: `http://localhost:8000/docs`
- Data Observer API: `http://localhost:8001/docs`

# Environment Configuration

Each component is configured via environment variables:

### Backend
- `DATABASE_URL`: PostgreSQL connection URL
- `REDIS_URL`: Redis connection URL (optional)

### Frontend
- `REACT_APP_API_URL`: Backend API URL
- `REACT_APP_DATA_OBSERVER_URL`: Data Observer URL

### Data Observer
- `NFS_ROOT`: NFS mount path (default: `/home/jovyan`)

## License

This project follows Apache 2.0 license