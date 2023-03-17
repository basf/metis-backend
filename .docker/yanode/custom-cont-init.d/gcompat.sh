#!/usr/bin/env sh

apk list -I | grep gcompat- || apk add gcompat
