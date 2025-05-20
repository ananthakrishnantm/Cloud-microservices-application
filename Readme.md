# Cloud Microservices Application

This project demonstrates a cloud-native microservices architecture deployed using Docker and Kubernetes. The system includes multiple services communicating via REST and gRPC, and uses asynchronous messaging, monitoring, and container orchestration.

## 🧩 Project Architecture

- **Client** – Frontend to view student and course data.
- **ServerA** – Manages student information (runs on port `5000`).
- **ServerB** – Manages course information (runs on port `5001`).
- **Grpc** – Fetches data from ServerA and ServerB, returns analytics.
- **APIGateway** – Routes external requests to microservices (runs on port `8080`).
- **RabbitMQ** – Message broker for asynchronous data communication.
- **Seq** – Centralized logging.
- **Prometheus** – Health and uptime monitoring.

All services are containerized and run in a bridge network for local development and as Kubernetes pods in production.

---

## 🚀 Features

- ✅ MVC structure with separate Client, API Gateway, and Servers
- ✅ Asynchronous event-driven communication using RabbitMQ
- ✅ gRPC integration for combined analytics
- ✅ Centralized logging with Seq
- ✅ Health monitoring using Prometheus
- ✅ Docker Compose for local development
- ✅ Kubernetes manifests for production deployment

---

## 🛠️ Technologies Used

- Docker & Docker Compose  
- Kubernetes (Kompose for conversion)  
- RabbitMQ  
- gRPC  
- Prometheus  
- Seq  
- SQL Server  
- .NET Core / Node.js *(update this based on your actual stack)*

---

## 📦 Getting Started

### Run with Docker Compose
```bash
docker-compose up --build
```

### Access Services
- Client: `http://localhost:<client-port>`
- APIGateway: `http://localhost:8080`
- RabbitMQ: `http://localhost:15672`
- Seq: `http://localhost:5341`
- Prometheus: `http://localhost:9090`

---

## ☸️ Kubernetes Deployment

1. Convert `docker-compose.yml` to Kubernetes YAML using Kompose:
```bash
kompose convert
```

2. Apply the files to your Kubernetes cluster:
```bash
kubectl apply -f .
```

3. Monitor namespace and pods:
```bash
kubectl get pods -n lab-namespace
```

---

## 🗃️ Container Registry

All Docker images were pushed to a private container registry and deployed using Kubernetes. The cluster pulls images from this registry.

---

## 📈 Result

A fully containerized and orchestrated MVC application capable of handling REST, gRPC, and asynchronous messaging, deployed in a scalable Kubernetes environment.

---

## 📄 Author

**Ananthakrishnan Thuruthel Murali**  
Project under supervision of **Assoc. Prof. Naujokaitis Darius**  
*Kaunas University of Technology*
