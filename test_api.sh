#!/bin/bash

# Test Newsletter API Server
# This script tests the newsletter API endpoint

API_KEY="3xWLv7AIHA8T6XFlbWc7ShJYRMaberle19a4GUy1mII"
API_URL="http://localhost:8765"

echo "Testing Newsletter API..."
echo

# Test 1: Health Check
echo "1. Testing health endpoint..."
curl -s "$API_URL/health"
echo
echo

# Test 2: Submit newsletter content
echo "2. Submitting test newsletter content..."
curl -X POST "$API_URL/newsletter/submit" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "AI Safety Research Update\n\nRecent developments in AI safety research have shown promising results:\n\n1. Constitutional AI: Anthropic has developed methods for training AI systems to be helpful, harmless, and honest through constitutional principles.\n\n2. Mechanistic Interpretability: Researchers are making progress in understanding how neural networks make decisions by analyzing their internal representations.\n\n3. Red Teaming: Systematic testing of AI systems for potential harmful outputs has become a standard practice in AI development.\n\n4. Alignment Research: New techniques for aligning AI systems with human values are being explored, including reinforcement learning from human feedback (RLHF).\n\n5. Safety Benchmarks: Industry-wide benchmarks for evaluating AI safety are being developed and adopted.\n\nThese advances suggest that the field is taking AI safety seriously and making concrete progress toward building more reliable and trustworthy AI systems."
  }'
echo
echo

echo "Test complete!"
