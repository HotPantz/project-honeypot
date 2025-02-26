#!/usr/bin/env python3
"""
Honeypot Data Analysis Script
This script generates visualizations from a MySQL dump of a honeypot database.
"""

import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from collections import Counter
import os
from datetime import datetime
import sys
import json

# Create output directory if it doesn't exist
output_dir = "honeypot_analysis_output"
os.makedirs(output_dir, exist_ok=True)

def print_debug(message):
    print(f"[DEBUG] {message}")

def extract_raw_insert_statements(content, table_name):
    print_debug(f"Extracting raw INSERT statements for table: {table_name}")
    # Find all INSERT statements for the specified table
    pattern = re.compile(rf"INSERT INTO\s+[`'\"]?{table_name}[`'\"]?\s+VALUES\s*\((.+?)\);", re.DOTALL | re.MULTILINE | re.IGNORECASE)
    matches = pattern.findall(content)
    print_debug(f"Found {len(matches)} INSERT statements for {table_name}")
    
    if not matches:
        # Try an alternate pattern with column names
        pattern = re.compile(rf"INSERT INTO\s+[`'\"]?{table_name}[`'\"]?\s*\([^)]+\)\s*VALUES\s*\((.+?)\);", re.DOTALL | re.MULTILINE | re.IGNORECASE)
        matches = pattern.findall(content)
        print_debug(f"Found {len(matches)} INSERT statements with column names for {table_name}")
    
    return matches

def parse_raw_values(raw_values):
    # This is a simplified approach to parse the raw values
    values = []
    raw_values = raw_values.strip()
    
    # For multiple value sets like (1,2,3),(4,5,6)
    if raw_values.endswith('),') and '(' in raw_values:
        chunks = raw_values.split('),(')
        for chunk in chunks:
            chunk = chunk.strip('(),')
            values.append(parse_csv_with_quotes(chunk))
    else:
        values.append(parse_csv_with_quotes(raw_values))
    
    return values

def parse_csv_with_quotes(line):
    """Parse a CSV line properly handling quoted values with commas inside"""
    values = []
    current = ""
    in_quotes = False
    quote_char = None
    
    for char in line:
        if char in ['"', "'"] and (quote_char is None or char == quote_char):
            in_quotes = not in_quotes
            if in_quotes:
                quote_char = char
            else:
                quote_char = None
            current += char
        elif char == ',' and not in_quotes:
            values.append(current.strip())
            current = ""
        else:
            current += char
    
    if current:
        values.append(current.strip())
    
    # Clean values (remove quotes)
    cleaned = []
    for val in values:
        if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
            cleaned.append(val[1:-1])
        elif val.lower() == 'null':
            cleaned.append(None)
        else:
            cleaned.append(val)
    
    return cleaned

def get_table_schemas(content):
    """Extract table schemas from CREATE TABLE statements"""
    schemas = {}
    
    # Pattern to find CREATE TABLE statements
    create_pattern = re.compile(r"CREATE TABLE\s+[`'\"]?(\w+)[`'\"]?\s*\((.*?)\)\s*ENGINE", re.DOTALL | re.MULTILINE)
    matches = create_pattern.findall(content)
    
    for table_name, schema_text in matches:
        # Split schema text into lines and clean them
        columns = []
        column_pattern = re.compile(r"`(\w+)`\s+(\w+)(?:\(\d+\))?")
        for column_match in column_pattern.finditer(schema_text):
            columns.append((column_match.group(1), column_match.group(2).lower()))
        
        schemas[table_name] = columns
        print_debug(f"Schema for {table_name}: {columns}")
    
    return schemas

def direct_extract_data(content, table_name):
    """A more direct approach to extract data from INSERT statements"""
    print_debug(f"Direct extraction for table: {table_name}")
    
    # Single row pattern
    pattern = re.compile(rf"INSERT INTO\s+[`'\"]?{table_name}[`'\"]?\s*(?:\([^)]+\))?\s*VALUES\s*\(([^;]+?)\);", re.IGNORECASE)
    matches = pattern.findall(content)
    
    # Multiple rows pattern
    multi_pattern = re.compile(rf"INSERT INTO\s+[`'\"]?{table_name}[`'\"]?\s*(?:\([^)]+\))?\s*VALUES\s*(\([^;]+\)[,;])", re.IGNORECASE)
    multi_matches = multi_pattern.findall(content)
    
    all_rows = []
    
    # Process single row matches
    for match in matches:
        try:
            row = parse_csv_with_quotes(match)
            all_rows.append(row)
        except Exception as e:
            print_debug(f"Error parsing row: {str(e)}")
    
    # Process multi-row matches
    for multi_match in multi_matches:
        # Split into individual rows
        rows = re.findall(r'\(([^()]+)\)', multi_match)
        for row in rows:
            try:
                parsed_row = parse_csv_with_quotes(row)
                all_rows.append(parsed_row)
            except Exception as e:
                print_debug(f"Error parsing multi-row: {str(e)}")
    
    print_debug(f"Directly extracted {len(all_rows)} rows for table {table_name}")
    return all_rows

def parse_mysql_dump_simplified(dump_file):
    """A more direct approach to parse the MySQL dump file"""
    try:
        # Read file
        with open(dump_file, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read()
            print_debug(f"Read {len(content)} bytes from {dump_file}")
        
        # Get all tables
        tables = re.findall(r"CREATE TABLE `(\w+)`", content)
        print_debug(f"Found tables: {tables}")
        
        # Get schemas
        schemas = get_table_schemas(content)
        
        # Initialize empty DataFrames
        data = {}
        
        # Extract data for each table
        for table in tables:
            rows = direct_extract_data(content, table)
            
            if rows:
                # Convert to DataFrame with schema info if available
                if table in schemas:
                    column_names = [col[0] for col in schemas[table]]
                    # Make sure we have enough column names
                    if len(column_names) < len(rows[0]):
                        print_debug(f"Warning: Schema column count mismatch for {table}")
                        # Add generic column names
                        column_names += [f"col{i}" for i in range(len(column_names), len(rows[0]))]
                    # Truncate rows if too long
                    processed_rows = []
                    for row in rows:
                        if len(row) > len(column_names):
                            processed_rows.append(row[:len(column_names)])
                        else:
                            # Extend row if too short
                            processed_rows.append(row + [None] * (len(column_names) - len(row)))
                    
                    df = pd.DataFrame(processed_rows, columns=column_names)
                else:
                    # Create generic column names
                    if rows:
                        max_cols = max(len(row) for row in rows)
                        column_names = [f"col{i}" for i in range(max_cols)]
                        df = pd.DataFrame(rows, columns=column_names)
                    else:
                        df = pd.DataFrame()
                
                data[table] = df
                print_debug(f"Created DataFrame for {table} with {len(df)} rows and {df.shape[1]} columns")
            else:
                data[table] = pd.DataFrame()
                print_debug(f"No data found for {table}")
        
        return data
    
    except Exception as e:
        print(f"Error parsing dump file: {str(e)}")
        import traceback
        traceback.print_exc()
        return {}

# Main execution
dump_file = "../honeypot_db_dump.sql"  # Default path
if len(sys.argv) > 1:
    dump_file = sys.argv[1]

print(f"Parsing MySQL dump file: {dump_file}")
data_dict = parse_mysql_dump_simplified(dump_file)

# Check which tables we have
available_tables = [table for table, df in data_dict.items() if not df.empty]
print(f"Available tables with data: {available_tables}")

# Print row counts
for table, df in data_dict.items():
    print(f"Table {table}: {len(df)} rows")

# Set table references for clarity
login_df = data_dict.get('login_attempts', pd.DataFrame())
connection_df = data_dict.get('connections', pd.DataFrame())
geo_df = data_dict.get('ip_geolocations', pd.DataFrame())
command_df = data_dict.get('user_commands', pd.DataFrame())

# Check if we have any data to visualize
if all(df.empty for df in [login_df, connection_df, geo_df, command_df]):
    print("No data was parsed from any table. Please check the format of your SQL dump.")
    sys.exit(1)

# Preprocessing of dataframes
def preprocess_dataframes():
    # Convert id columns to int where applicable
    for df in [login_df, connection_df, command_df]:
        if not df.empty and 'id' in df.columns:
            df['id'] = pd.to_numeric(df['id'], errors='coerce')
    
    # Process login_df
    if not login_df.empty:
        if 'success' in login_df.columns:
            login_df['success'] = login_df['success'].astype(str).str.lower().isin(['1', 'true', 'yes'])
        if 'timestamp' in login_df.columns:
            login_df['timestamp'] = pd.to_datetime(login_df['timestamp'], errors='coerce')
    
    # Process connection_df
    if not connection_df.empty:
        if 'start_time' in connection_df.columns:
            connection_df['start_time'] = pd.to_datetime(connection_df['start_time'], errors='coerce')
        if 'end_time' in connection_df.columns:
            connection_df['end_time'] = pd.to_datetime(connection_df['end_time'], errors='coerce')
    
    # Process command_df
    if not command_df.empty and 'timestamp' in command_df.columns:
        command_df['timestamp'] = pd.to_datetime(command_df['timestamp'], errors='coerce')

try:
    preprocess_dataframes()
except Exception as e:
    print(f"Error preprocessing dataframes: {str(e)}")

# Function to safely create visualizations with error handling
def create_visualization(func, title):
    try:
        func()
        print(f"Generated {title}")
    except Exception as e:
        print(f"Error generating {title}: {str(e)}")
        import traceback
        traceback.print_exc()

# Define each visualization as a separate function
def username_chart():
    if login_df.empty or 'username' not in login_df.columns:
        print("No username data available")
        return
    
    plt.figure(figsize=(10, 8))
    username_counts = login_df['username'].value_counts()
    
    if len(username_counts) > 10:
        username_counts_top = username_counts.head(10)
        other_count = username_counts.sum() - username_counts_top.sum()
        username_counts_plot = pd.concat([username_counts_top, pd.Series([other_count], index=['Other'])])
        
        # Create color map with a distinct color for "Other"
        colors = plt.cm.tab20(range(10))  # Get first 10 colors from tab20 colormap
        colors = list(colors)  # Convert to list for manipulation
        colors.append((0.5, 0.5, 0.5, 1.0))  # Add gray color for "Other"
        
        plt.pie(username_counts_plot, labels=username_counts_plot.index, autopct='%1.1f%%', 
                startangle=90, shadow=True, colors=colors)
    else:
        username_counts_plot = username_counts
        plt.pie(username_counts_plot, labels=username_counts_plot.index, autopct='%1.1f%%', 
                startangle=90, shadow=True)
    
    plt.axis('equal')
    plt.title('Top Usernames in Login Attempts', fontsize=16)
    plt.savefig(f"{output_dir}/username_distribution.png", bbox_inches='tight')
    plt.close()

def login_success_chart():
    if login_df.empty or 'success' not in login_df.columns:
        print("No success data available")
        return
    
    plt.figure(figsize=(8, 6))
    success_counts = login_df['success'].value_counts()
    
    # Handle case where one category might be missing
    values = [success_counts.get(False, 0), success_counts.get(True, 0)]
    
    plt.bar(['Failed', 'Successful'], values, color=['#ff9999', '#66b3ff'])
    plt.title('Login Attempt Success Rate', fontsize=16)
    plt.ylabel('Number of Attempts', fontsize=14)
    
    for i, v in enumerate(values):
        plt.text(i, v + 5, str(v), ha='center', fontsize=12)
    
    plt.savefig(f"{output_dir}/login_success_rate.png", bbox_inches='tight')
    plt.close()

def country_chart():
    if geo_df.empty:
        print("No geo data available")
        return
    
    # Look for a country column (could have different names)
    country_col = None
    for col in geo_df.columns:
        if 'country' in col.lower():
            country_col = col
            break
    
    if not country_col:
        print("No country column found in geo data")
        return
    
    # Get country counts
    country_counts = geo_df[country_col].value_counts()
    
    # Create pie chart
    plt.figure(figsize=(10, 8))
    if len(country_counts) > 10:
        country_counts_top = country_counts.head(9)  # Get top 9
        other_count = country_counts.sum() - country_counts_top.sum()
        country_counts_plot = pd.concat([country_counts_top, pd.Series([other_count], index=['Other'])])
        
        # Create color map with a distinct color for "Other"
        colors = plt.cm.tab10(range(9))  # Get first 9 colors from tab10 colormap
        colors = list(colors)  # Convert to list for manipulation
        colors.append((0.5, 0.5, 0.5, 1.0))  # Add gray color for "Other"
        
        plt.pie(country_counts_plot, labels=country_counts_plot.index, autopct='%1.1f%%', 
                startangle=90, shadow=True, colors=colors)
    else:
        plt.pie(country_counts, labels=country_counts.index, autopct='%1.1f%%', 
                startangle=90, shadow=True)
    
    plt.axis('equal')
    plt.title('Country Distribution of Attack Sources', fontsize=16)
    plt.savefig(f"{output_dir}/country_pie.png", bbox_inches='tight')
    plt.close()
    
    # Create bar chart (existing functionality)
    plt.figure(figsize=(12, 8))
    if len(country_counts) > 10:
        country_counts = country_counts.head(10)
    
    sns.barplot(x=country_counts.index, y=country_counts.values)
    plt.title('Top 10 Countries of Origin', fontsize=16)
    plt.xlabel('Country', fontsize=14)
    plt.ylabel('Number of IPs', fontsize=14)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(f"{output_dir}/country_distribution.png", bbox_inches='tight')
    plt.close()

def ip_chart():
    # Try different tables for IP data
    ip_df = None
    ip_col = 'ip'
    
    if not login_df.empty and 'ip' in login_df.columns:
        ip_df = login_df
    elif not connection_df.empty and 'ip' in connection_df.columns:
        ip_df = connection_df
    elif not geo_df.empty:
        for col in geo_df.columns:
            if 'ip' in col.lower():
                ip_df = geo_df
                ip_col = col
                break
    
    if ip_df is None:
        print("No IP data available")
        return
    
    plt.figure(figsize=(14, 10))
    ip_counts = ip_df[ip_col].value_counts()
    
    if len(ip_counts) > 20:
        ip_counts = ip_counts.head(20)
    
    sns.barplot(x=ip_counts.values, y=ip_counts.index)
    plt.title('Top IP Addresses by Frequency', fontsize=16)
    plt.xlabel('Frequency', fontsize=14)
    plt.ylabel('IP Address', fontsize=14)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/ip_distribution.png", bbox_inches='tight')
    plt.close()

def subnet_chart():
    # Try different tables for IP data
    ip_df = None
    ip_col = 'ip'
    
    if not login_df.empty and 'ip' in login_df.columns:
        ip_df = login_df
    elif not connection_df.empty and 'ip' in connection_df.columns:
        ip_df = connection_df
    elif not geo_df.empty:
        for col in geo_df.columns:
            if 'ip' in col.lower():
                ip_df = geo_df
                ip_col = col
                break
    
    if ip_df is None:
        print("No IP data available for subnet analysis")
        return
    
    def extract_subnet(ip):
        try:
            if isinstance(ip, str) and '.' in ip:
                parts = ip.split('.')
                if len(parts) >= 2:
                    return f"{parts[0]}.{parts[1]}"
            return "Unknown"
        except:
            return "Unknown"
    
    ip_subnets = ip_df[ip_col].apply(extract_subnet)
    subnet_counts = ip_subnets.value_counts()
    
    if len(subnet_counts) > 15:
        subnet_counts = subnet_counts.head(15)
    
    plt.figure(figsize=(12, 8))
    sns.barplot(x=subnet_counts.index, y=subnet_counts.values)
    plt.title('Top IP Subnets', fontsize=16)
    plt.xlabel('Subnet (First Two Octets)', fontsize=14)
    plt.ylabel('Count', fontsize=14)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(f"{output_dir}/subnet_distribution.png", bbox_inches='tight')
    plt.close()

def connection_status_chart():
    if connection_df.empty or 'status' not in connection_df.columns:
        print("No connection status data available")
        return
    
    plt.figure(figsize=(8, 6))
    status_counts = connection_df['status'].value_counts()
    
    sns.barplot(x=status_counts.index, y=status_counts.values)
    plt.title('Connection Status Distribution', fontsize=16)
    plt.xlabel('Status', fontsize=14)
    plt.ylabel('Count', fontsize=14)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/connection_status.png", bbox_inches='tight')
    plt.close()

def command_count_chart():
    if command_df.empty or 'command' not in command_df.columns:
        print("No command data available")
        return
    
    plt.figure(figsize=(10, 8))
    command_counts = command_df['command'].value_counts().head(10)
    
    sns.barplot(x=command_counts.values, y=command_counts.index)
    plt.title('Top Commands Executed', fontsize=16)
    plt.xlabel('Count', fontsize=14)
    plt.ylabel('Command', fontsize=14)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/command_count.png", bbox_inches='tight')
    plt.close()

def connection_timeline():
    if connection_df.empty or 'start_time' not in connection_df.columns:
        print("No connection timeline data available")
        return
        
    try:
        valid_df = connection_df.dropna(subset=['start_time'])
        if valid_df.empty:
            print("No valid timestamp data for timeline")
            return
            
        # Group by date
        valid_df['date'] = pd.to_datetime(valid_df['start_time']).dt.date
        connections_by_date = valid_df.groupby('date').size()
        
        plt.figure(figsize=(14, 8))
        connections_by_date.plot(kind='line', marker='o')
        plt.title('Connections Over Time', fontsize=16)
        plt.xlabel('Date', fontsize=14)
        plt.ylabel('Number of Connections', fontsize=14)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(f"{output_dir}/connection_timeline.png", bbox_inches='tight')
        plt.close()
    except Exception as e:
        print(f"Error in connection timeline: {str(e)}")

# Create all visualizations
create_visualization(username_chart, "username distribution chart")
create_visualization(login_success_chart, "login success rate chart")
create_visualization(country_chart, "country distribution chart")
create_visualization(ip_chart, "IP distribution chart")
create_visualization(subnet_chart, "subnet distribution chart")
create_visualization(connection_status_chart, "connection status chart")
create_visualization(command_count_chart, "command count chart")
create_visualization(connection_timeline, "connection timeline chart")

print(f"\nAll visualizations have been saved to the '{output_dir}' directory")

# Generate a simple HTML report
html_report = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Honeypot Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #2c3e50; }}
        .container {{ display: flex; flex-wrap: wrap; }}
        .chart {{ margin: 10px; border: 1px solid #ddd; padding: 10px; }}
        img {{ max-width: 100%; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
    </style>
</head>
<body>
    <h1>Honeypot Analysis Report</h1>
    <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <h2>Data Summary</h2>
    <table>
        <tr>
            <th>Table</th>
            <th>Row Count</th>
        </tr>
"""

for table, df in data_dict.items():
    html_report += f"""
        <tr>
            <td>{table}</td>
            <td>{len(df)}</td>
        </tr>
    """

html_report += """
    </table>
    
    <h2>Visualizations</h2>
    <div class="container">
"""

# Add all generated charts to the report
for chart_file in os.listdir(output_dir):
    if chart_file.endswith('.png'):
        chart_name = chart_file.replace('_', ' ').replace('.png', '').title()
        html_report += f"""
        <div class="chart">
            <h3>{chart_name}</h3>
            <img src="{chart_file}" alt="{chart_name}">
        </div>
        """

html_report += """
    </div>
</body>
</html>
"""

# Write the HTML report
with open(f"{output_dir}/report.html", 'w') as f:
    f.write(html_report)

print(f"Generated HTML report: {output_dir}/report.html")