#!/bin/bash

echo 'deb [trusted=yes] https://thinedgeio.jfrog.io/artifactory/stable stable main' > /etc/apt/sources.list.d/tedge.list
apt-get update
apt-get install -y mosquitto
apt-get install -y tedge-full
