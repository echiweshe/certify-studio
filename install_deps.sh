#!/bin/bash
# Install missing langchain dependencies

echo "Installing missing langchain dependencies..."

# Install the required packages
uv add langchain-anthropic langchain-openai langchain-core langchain-community anthropic

echo "Dependencies installed successfully!"
