"""
SQLite compatibility fix for ChromaDB.

Import this module BEFORE any other imports to fix SQLite version compatibility issues.
Example:
    import sqlite_fix  # noqa
    
    # Continue with regular imports
    import streamlit as st
    ...
"""

import sqlite3
import sys
import os

def fix_sqlite():
    """
    Try to fix SQLite compatibility issues by using pysqlite3 if available,
    or by displaying helpful error information if not.
    """
    print(f"Current SQLite version: {sqlite3.sqlite_version}")
    
    try:
        # Try to import pysqlite3 and use it instead of sqlite3
        import pysqlite3
        sys.modules['sqlite3'] = pysqlite3
        print(f"Successfully patched SQLite. New version: {sqlite3.sqlite_version}")
        return True
    except ImportError:
        # If pysqlite3 is not available, provide instructions
        print("pysqlite3 not available. Cannot automatically fix SQLite version.")
        print("If you're using ChromaDB and encountering SQLite version errors, try installing pysqlite3:")
        print("pip install pysqlite3-binary")
        print("For container deployments, you might need to install SQLite >= 3.35.0 in your container.")
        return False

if __name__ == "__main__":
    # Run as standalone to test SQLite version
    print(f"Python version: {sys.version}")
    fixed = fix_sqlite()
    print(f"Fix applied: {fixed}")
    print(f"Final SQLite version: {sqlite3.sqlite_version}") 