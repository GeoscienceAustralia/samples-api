#!/usr/bin/env bash

sudo kill `ps aux | grep samples-api | grep -v "grep" | head -3 | awk '{print \$2}'`