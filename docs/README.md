# Feecc Print Server

## Overview

Feecc Print Server is a microservice, designed to handle printing labels using a Brother QL-series label printer.

It provides a simple REST API interface to print and annotate images. It also handles user authentication.

Feecc Print Server comes as a part of the Feecc QA system - a Web3 enabled quality control system.

Print Server is a microservice that is written in asynchronous Python using FastAPI framework and relies on Pillow 
to annotate images.

## Deployment

The app is supposed to be run in a Docker container and can be configured by setting several environment variables.

> Note, that we assume a Linux host in this guide, however you can also run Print Server on any other OS,
> but be warned: timezone is defined by mounting host `/etc/timezone` and `/etc/localtime` files inside the container,
> which are not present on Windows machines, so you might end up with UTC time inside your container.

Start by cloning the git repository onto your machine: 
`git clone https://github.com/Multi-Agent-io/feecc-print-server.git`

Enter the app directory and modify the `docker-compose.yml` file to your needs by changing the environment variables
(discussed in the configuration part).

```
cd feecc-print-server
vim docker-compose.yml
```

When you are done configuring your installation, build and start the container using docker-compose:
`sudo docker-compose up --build`

Verify your deployment by going to http://127.0.0.1:8083/docs in your browser. You should see the SwaggerUI API
specification page. Continue from there.

## Configuration

To configure your Print Server deployment edit the environment variables, provided in `docker-compose.yml` file.

### Environment variables

- `MONGODB_URI` - Your MongoDB connection URI ending with `/db-name`
- `PRODUCTION_ENVIRONMENT` - Leave null if you want testing credentials to work, otherwise set it to `true`
- `PAPER_WIDTH` - Paper width in mm (string)
- `PRINTER_MODEL` - Label printer model name
- `RED` - Whether the black and red paper is loaded or not (boolean)
