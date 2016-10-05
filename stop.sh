#!/usr/bin/env bash

sudo kill `ps aux | grep igsn-ld-api | grep -v "grep" | head -3 | awk '{print \$2}'`