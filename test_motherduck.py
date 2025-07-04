#!/usr/bin/env python3
"""
Test script for MotherDuck connection.
Use this to verify your MotherDuck configuration before running the main app.
"""

import duckdb
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MOTHERDUCK_DATABASE = os.getenv('MOTHERDUCK_DATABASE', 'md:cola_data')
MOTHERDUCK_TOKEN = os.getenv('MOTHERDUCK_TOKEN')

def test_motherduck_connection():
    print("Testing MotherDuck connection...")
    print(f"Database: {MOTHERDUCK_DATABASE}")
    print(f"Token: {'✓ Set' if MOTHERDUCK_TOKEN else '✗ Not set'}")
    
    if not MOTHERDUCK_TOKEN:
        print("\n❌ Error: MOTHERDUCK_TOKEN environment variable not set")
        print("Please set your MotherDuck token in the .env file or as an environment variable")
        return False
    
    try:
        # Connect to MotherDuck
        con = duckdb.connect(f"{MOTHERDUCK_DATABASE}?motherduck_token={MOTHERDUCK_TOKEN}")
        print("✓ Connected to MotherDuck successfully")
        
        # Test basic query
        result = con.execute("SELECT 1 as test").fetchone()
        print(f"✓ Basic query successful: {result}")
        
        # List tables
        print("\nTables in database:")
        tables = con.execute("SHOW TABLES").fetchall()
        for table in tables:
            print(f"  - {table[0]}")
        
        # Check for expected tables
        expected_tables = ['colas', 'cola_images', 'cola_image_analysis', 'image_analysis_items']
        table_names = [t[0] for t in tables]
        
        print("\nExpected tables check:")
        for table in expected_tables:
            if table in table_names:
                print(f"  ✓ {table}")
                # Get row count
                count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                print(f"    ({count:,} rows)")
            else:
                print(f"  ✗ {table} (missing)")
        
        con.close()
        print("\n✅ MotherDuck connection test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error connecting to MotherDuck: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Check your MOTHERDUCK_TOKEN is correct")
        print("2. Verify the MOTHERDUCK_DATABASE name")
        print("3. Ensure you have access to the database")
        print("4. Check your internet connection")
        return False

if __name__ == "__main__":
    test_motherduck_connection()
