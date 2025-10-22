#!/usr/bin/env python3

import os
import sys
import logging
sys.path.append('/Users/alexkamer/mmaWebsite')

from mma_website.services.mma_query_service_agno import mma_query_service

# Set up logging to see debug output
logging.basicConfig(level=logging.INFO)

def test_tom_aspinall_query():
    print("Testing Tom Aspinall recent fights query...")
    
    # Test the actual service
    result = mma_query_service.process_query("Tom Aspinall recent fights")
    
    print("\n=== RESULT ===")
    print(f"Success: {result.get('success')}")
    print(f"Error: {result.get('error', 'None')}")
    print(f"Row count: {result.get('row_count', 0)}")
    print(f"Classification: {result.get('classification')}")
    print(f"SQL Query: {result.get('sql_query')}")
    print(f"Data: {result.get('data', [])}")
    
if __name__ == "__main__":
    test_tom_aspinall_query()