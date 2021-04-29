# Traefik

[Traefik](https://traefik.io/) is a modern HTTP reverse proxy and load balancer made to deploy
microservices with ease.

### Deploying Traefik

```bash
helm upgrade -i stable/traefik --name traefik --namespace kube-system -f values.yaml
```