#!/bin/bash

NAMESPACE=sudoku2
minikube -n $NAMESPACE service --url orchestrator
