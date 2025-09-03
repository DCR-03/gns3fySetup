To build the docker images:

```
docker build -t control_server ./control_server
docker build -t server_node ./server_node
docker build -t client_node ./client_node
docker build -t router ./router
docker build -t adversary ./adversary
```

When running the `router` and `adversary` docker images, run with the following flags:

```
docker run --cap-add=NET_ADMIN --cap-add=NET_RAW
```
