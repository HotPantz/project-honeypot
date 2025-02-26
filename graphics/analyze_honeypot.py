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

    
    # Create a new Series with readable labels
    readable_status = pd.Series({status_labels[status]: count for status, count in status_counts.items()})
    
    sns.barplot(x=readable_status.index, y=readable_status.values)
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

def success_by_country():
    if login_df.empty or geo_df.empty or 'success' not in login_df.columns:
        print("Missing data for success by country analysis")
        return
    
    try:
        # Find IP column in geo data
        ip_col = None
        country_col = None
        for col in geo_df.columns:
            if 'ip' in col.lower():
                ip_col = col
            elif 'country' in col.lower():
                country_col = col
        
        if ip_col is None or country_col is None:
            print("Missing required columns in geo data")
            return
        
        # Create a mapping of IP to country
        ip_to_country = dict(zip(geo_df[ip_col], geo_df[country_col]))
        
        # Add country to login data
        login_df['country'] = login_df['ip'].map(ip_to_country)
        
        # Filter out rows with missing country
        valid_df = login_df.dropna(subset=['country'])
        
        if valid_df.empty:
            print("No valid country data for success rate analysis")
            return
        
        # Calculate success rate by country
        success_by_country = valid_df.groupby('country')['success'].agg(['mean', 'count'])
        success_by_country = success_by_country.sort_values('count', ascending=False).head(10)
        success_by_country['mean'] = success_by_country['mean'] * 100  # Convert to percentage
        
        plt.figure(figsize=(12, 8))
        ax = sns.barplot(x=success_by_country.index, y=success_by_country['mean'])
        
        # Add count annotations
        for i, (_, row) in enumerate(success_by_country.iterrows()):
            ax.text(i, row['mean'] + 1, f"n={row['count']}", ha='center')
        
        plt.title('Login Success Rate by Country (Top 10 by Attempt Count)', fontsize=16)
        plt.xlabel('Country', fontsize=14)
        plt.ylabel('Success Rate (%)', fontsize=14)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(f"{output_dir}/success_by_country.png", bbox_inches='tight')
        plt.close()
        print("Generated success by country chart")
    except Exception as e:
        print(f"Error generating success by country chart: {str(e)}")

def geo_map_folium():
    """Generate an interactive geographical map using Folium"""
    if geo_df.empty:
        print("No geo data available")
        return
    
    # Look for latitude/longitude columns
    lat_col = None
    lon_col = None
    country_col = None
    ip_col = None
    
    for col in geo_df.columns:
        if 'lat' in col.lower():
            lat_col = col
        elif 'lon' in col.lower() or 'lng' in col.lower():
            lon_col = col
        elif 'country' in col.lower():
            country_col = col
        elif 'ip' in col.lower():
            ip_col = col
    
    if lat_col is None or lon_col is None:
        print("Missing required geo coordinates")
        return
    
    try:
        import folium
        from folium.plugins import MarkerCluster
        
        # Convert lat/lon to float and filter out invalid values
        valid_geo = geo_df.copy()
        valid_geo[lat_col] = pd.to_numeric(valid_geo[lat_col], errors='coerce')
        valid_geo[lon_col] = pd.to_numeric(valid_geo[lon_col], errors='coerce')
        valid_geo = valid_geo.dropna(subset=[lat_col, lon_col])
        
        if valid_geo.empty:
            print("No valid geo coordinates found")
            return
        
        # Create map centered at average coordinates
        center_lat = valid_geo[lat_col].mean()
        center_lon = valid_geo[lon_col].mean()
        attack_map = folium.Map(location=[center_lat, center_lon], zoom_start=2)
        
        # Add marker cluster to improve performance with many points
        marker_cluster = MarkerCluster().add_to(attack_map)
        
        # Count occurrences of each country
        country_counts = valid_geo[country_col].value_counts() if country_col else {}
        
        # Add markers for each unique location
        locations_added = set()
        for _, row in valid_geo.iterrows():
            lat = row[lat_col]
            lon = row[lon_col]
            
            # Skip invalid coordinates
            if abs(lat) > 90 or abs(lon) > 180:
                continue
                
            # Create a unique location key to avoid too many overlapping points
            location_key = f"{lat:.2f},{lon:.2f}"
            if location_key in locations_added:
                continue
            locations_added.add(location_key)
            
            # Create popup content
            popup_content = []
            if country_col and row[country_col]:
                country = row[country_col]
                count = country_counts.get(country, 0)
                popup_content.append(f"Country: {country} ({count} IPs)")
            
            if ip_col and row[ip_col]:
                popup_content.append(f"Sample IP: {row[ip_col]}")
                
            popup_text = "<br>".join(popup_content) if popup_content else "Unknown location"
            
            # Add marker to cluster
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_text, max_width=300),
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(marker_cluster)
        
        # Save the map
        map_file = f"{output_dir}/attack_map.html"
        attack_map.save(map_file)
        print(f"Generated interactive map: {map_file}")
        
        # Generate a static screenshot for the report
        try:
            import selenium
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            import time
            
            print("Trying to create static image from interactive map...")
            
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_window_size(1000, 800)
            driver.get(f"file://{os.path.abspath(map_file)}")
            time.sleep(3)  # Wait for map to load
            
            # Take a screenshot
            static_map_file = f"{output_dir}/attack_map.png"
            driver.save_screenshot(static_map_file)
            driver.quit()
            
            print(f"Generated static map image: {static_map_file}")
        except Exception as e:
            print(f"Could not generate static map image: {str(e)}")
            print("The interactive HTML map is still available.")
        
    except ImportError:
        print("Folium library not available. Install with: pip install folium")
    except Exception as e:
        print(f"Error generating geo map: {str(e)}")

def password_prefix_chart():
    if login_df.empty or 'password' not in login_df.columns:
        print("No password data available")
        return
    
    try:
        # Get the first 3 characters of each password
        login_df['prefix'] = login_df['password'].astype(str).str[:3]
        prefix_counts = login_df['prefix'].value_counts().head(15)
        
        plt.figure(figsize=(12, 8))
        sns.barplot(x=prefix_counts.index, y=prefix_counts.values)
        plt.title('Most Common Password Prefixes (First 3 Characters)', fontsize=16)
        plt.xlabel('Password Prefix', fontsize=14)
        plt.ylabel('Count', fontsize=14)
        plt.tight_layout()
        plt.savefig(f"{output_dir}/password_prefix.png", bbox_inches='tight')
        plt.close()
        print("Generated password prefix chart")
    except Exception as e:
        print(f"Error generating password prefix chart: {str(e)}")

def ip_diversity_chart():
    if login_df.empty or 'timestamp' not in login_df.columns or 'ip' not in login_df.columns:
        print("No IP diversity data available")
        return
    
    try:
        # Convert timestamps to datetime
        login_df['timestamp'] = pd.to_datetime(login_df['timestamp'], errors='coerce')
        valid_df = login_df.dropna(subset=['timestamp'])
        
        if valid_df.empty:
            print("No valid timestamp data for IP diversity")
            return
        
        # Group by date and count unique IPs
        valid_df['date'] = valid_df['timestamp'].dt.date
        ip_diversity = valid_df.groupby('date')['ip'].nunique()
        
        plt.figure(figsize=(12, 6))
        ip_diversity.plot(kind='line', marker='o', color='purple')
        plt.title('Unique IP Addresses per Day', fontsize=16)
        plt.xlabel('Date', fontsize=14)
        plt.ylabel('Number of Unique IPs', fontsize=14)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(f"{output_dir}/ip_diversity.png", bbox_inches='tight')
        plt.close()
        print("Generated IP diversity chart")
    except Exception as e:
        print(f"Error generating IP diversity chart: {str(e)}")

def credentials_heatmap():
    if login_df.empty or 'username' not in login_df.columns or 'password' not in login_df.columns:
        print("No credentials data available")
        return
    
    try:
        # Get top 10 usernames and passwords
        top_usernames = login_df['username'].value_counts().head(8).index
        top_passwords = login_df['password'].value_counts().head(8).index
        
        # Filter data to include only top credentials
        filtered_df = login_df[login_df['username'].isin(top_usernames) & login_df['password'].isin(top_passwords)]
        
        # Create cross-tabulation
        heatmap_data = pd.crosstab(filtered_df['username'], filtered_df['password'])
        
        plt.figure(figsize=(12, 10))
        sns.heatmap(heatmap_data, cmap="YlGnBu", annot=True, fmt="d", linewidths=.5)
        plt.title('Frequency of Username/Password Combinations', fontsize=16)
        plt.xlabel('Password', fontsize=14)
        plt.ylabel('Username', fontsize=14)
        plt.tight_layout()
        plt.savefig(f"{output_dir}/credentials_heatmap.png", bbox_inches='tight')
        plt.close()
        print("Generated credentials heatmap")
    except Exception as e:
        print(f"Error generating credentials heatmap: {str(e)}")

def login_time_heatmap():
    if login_df.empty or 'timestamp' not in login_df.columns:
        print("No timestamp data available for heatmap")
        return
    
    try:
        # Convert timestamps to datetime
        login_df['timestamp'] = pd.to_datetime(login_df['timestamp'], errors='coerce')
        valid_df = login_df.dropna(subset=['timestamp'])
        
        if valid_df.empty:
            print("No valid timestamp data for heatmap")
            return
        
        # Extract hour and day of week
        valid_df['hour'] = valid_df['timestamp'].dt.hour
        valid_df['day_of_week'] = valid_df['timestamp'].dt.day_name()
        
        # Order days of week properly
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        # Create pivot table
        heatmap_data = pd.crosstab(valid_df['day_of_week'], valid_df['hour'])
        heatmap_data = heatmap_data.reindex(day_order)
        
        plt.figure(figsize=(12, 8))
        sns.heatmap(heatmap_data, cmap="YlOrRd", annot=True, fmt="d", cbar_kws={'label': 'Number of Attempts'})
        plt.title('Login Attempts by Day of Week and Hour', fontsize=16)
        plt.xlabel('Hour of Day (24h)', fontsize=14)
        plt.ylabel('Day of Week', fontsize=14)
        plt.tight_layout()
        plt.savefig(f"{output_dir}/time_heatmap.png", bbox_inches='tight')
        plt.close()
        print("Generated time heatmap")
    except Exception as e:
        print(f"Error generating time heatmap: {str(e)}")

def password_pie_chart():
    """Generate a pie chart of the most commonly used passwords"""
    if login_df.empty or 'password' not in login_df.columns:
        print("No password data available")
        return
    
    plt.figure(figsize=(10, 8))
    password_counts = login_df['password'].value_counts()
    
    # Check if we have enough data
    if len(password_counts) == 0:
        print("No password data found")
        return
    
    # Limit to top passwords and group the rest as "Other"
    if len(password_counts) > 9:
        password_counts_top = password_counts.head(9)  # Get top 9
        other_count = password_counts.sum() - password_counts_top.sum()
        password_counts_plot = pd.concat([password_counts_top, pd.Series([other_count], index=['Other'])])
        
        # Create color map with a distinct color for "Other"
        colors = plt.cm.tab10(range(9))  # Get first 9 colors from tab10 colormap
        colors = list(colors)  # Convert to list for manipulation
        colors.append((0.5, 0.5, 0.5, 1.0))  # Add gray color for "Other"
        
        plt.pie(password_counts_plot, labels=password_counts_plot.index, autopct='%1.1f%%', 
                startangle=90, shadow=True, colors=colors)
    else:
        # If we have 9 or fewer passwords, just use all of them
        plt.pie(password_counts, labels=password_counts.index, autopct='%1.1f%%', 
                startangle=90, shadow=True)
    
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
    plt.title('Most Common Passwords', fontsize=16)
    plt.savefig(f"{output_dir}/password_distribution.png", bbox_inches='tight')
    plt.close()
    print("Generated password distribution pie chart")

def login_attempts_timeline():
    """Generate a timeline of login attempts over time"""
    if login_df.empty or 'timestamp' not in login_df.columns:
        print("No timestamp data available for login timeline")
        return
    
    try:
        print("Creating login attempts timeline chart...")
        
        # Convert timestamps to datetime objects
        login_df['timestamp'] = pd.to_datetime(login_df['timestamp'], errors='coerce')
        
        # Filter out invalid timestamps
        valid_df = login_df.dropna(subset=['timestamp'])
        
        if valid_df.empty:
            print("No valid timestamp data available")
            return
        
        # Group by day and count attempts
        valid_df['date'] = valid_df['timestamp'].dt.date
        attempts_by_date = valid_df.groupby('date').size()
        
        # Check if we have enough data points
        if len(attempts_by_date) <= 1:
            print("Not enough data points for a timeline (need at least 2 different dates)")
            return
        
        # Create the plot
        plt.figure(figsize=(14, 8))
        
        # Plot the data
        ax = attempts_by_date.plot(kind='line', marker='o', linewidth=2)
        
        # Format x-axis to show dates properly
        plt.gcf().autofmt_xdate()
        
        # Add grid lines for easier reading
        plt.grid(True, alpha=0.3)
        
        # Add labels and title
        plt.title('Login Attempts Over Time', fontsize=16)
        plt.xlabel('Date', fontsize=14)
        plt.ylabel('Number of Attempts', fontsize=14)
        
        # Add data point values
        for i, v in enumerate(attempts_by_date):
            ax.text(i, v + 0.5, str(v), ha='center')
        
        # Ensure y-axis starts at 0 for better visualization
        plt.ylim(bottom=0)
        
        # Make sure the layout looks good
        plt.tight_layout()
        
        # Save the figure
        plt.savefig(f"{output_dir}/login_attempts_timeline.png", bbox_inches='tight')
        plt.close()
        
        print("Successfully generated login attempts timeline chart")
    except Exception as e:
        print(f"Error generating login timeline: {str(e)}")
        import traceback
        traceback.print_exc()

def login_attempts_timeline_alt():
    """Alternative implementation of login attempts timeline"""
    if login_df.empty:
        print("No login data available")
        return
    
    # Try to find a timestamp column (could have different names)
    timestamp_col = None
    for col in login_df.columns:
        if 'time' in col.lower() or 'date' in col.lower():
            timestamp_col = col
            break
    
    if timestamp_col is None:
        print("No timestamp column found")
        return
    
    try:
        # Convert to datetime and handle errors
        login_df['date_parsed'] = pd.to_datetime(login_df[timestamp_col], errors='coerce')
        valid_df = login_df.dropna(subset=['date_parsed'])
        
        if valid_df.empty:
            print("No valid dates found after parsing")
            return
        
        # Extract date part only
        valid_df['date_only'] = valid_df['date_parsed'].dt.date
        
        # Group and count
        counts = valid_df.groupby('date_only').size()
        
        # Create the plot directly with matplotlib
        plt.figure(figsize=(14, 8))
        
        dates = [pd.Timestamp(d) for d in counts.index]
        values = counts.values
        
        plt.plot(dates, values, 'o-', linewidth=2, markersize=8)
        
        # Format the plot
        plt.title("Login Attempts Over Time", fontsize=16)
        plt.xlabel("Date", fontsize=14)
        plt.ylabel("Number of Attempts", fontsize=14)
        plt.grid(True, alpha=0.3)
        
        # Format dates on x-axis
        plt.gcf().autofmt_xdate()
        
        # Add values above points
        for i, (date, value) in enumerate(zip(dates, values)):
            plt.annotate(str(value), (date, value), textcoords="offset points", 
                         xytext=(0,10), ha='center')
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/login_attempts_timeline_alt.png", bbox_inches='tight')
        plt.close()
        
        print("Successfully generated login attempts timeline (alternative method)")
    except Exception as e:
        print(f"Error in alternative timeline generation: {str(e)}")
        import traceback
        traceback.print_exc()


def ip_reconnection_frequency():
    """Analyze how frequently each IP attempts to reconnect within an hour"""
    # Vérification de disponibilité des données
    ip_data_available = False
    timestamp_data_available = False
    
    # Vérifier si l'une des tables contient les données IP et timestamp nécessaires
    tables_to_check = [login_df, connection_df]
    
    for df in tables_to_check:
        if df.empty:
            continue
            
        # Recherche de colonnes d'IP
        ip_col = None
        for col in df.columns:
            if 'ip' in col.lower():
                ip_col = col
                ip_data_available = True
                break
                
        # Recherche de colonnes de timestamp
        timestamp_col = None
        for col in df.columns:
            if 'time' in col.lower() or 'date' in col.lower() or 'stamp' in col.lower():
                timestamp_col = col
                timestamp_data_available = True
                break
                
        # Si on a trouvé les deux colonnes dans cette table, on l'utilise
        if ip_data_available and timestamp_data_available:
            analysis_df = df
            break
    
    if not ip_data_available or not timestamp_data_available:
        print(f"No IP or timestamp data available for reconnection analysis (IP available: {ip_data_available}, Timestamp available: {timestamp_data_available})")
        return
    
    try:
        print(f"Using columns: {ip_col} and {timestamp_col} for reconnection analysis")
        
        # Convert timestamps to datetime
        analysis_df[timestamp_col] = pd.to_datetime(analysis_df[timestamp_col], errors='coerce')
        valid_df = analysis_df.dropna(subset=[timestamp_col, ip_col])
        
        if valid_df.empty:
            print("No valid timestamp and IP data available after conversion")
            return
            
        # Sort by IP and timestamp
        sorted_df = valid_df.sort_values([ip_col, timestamp_col])
        
        # Initialize dictionary to store reconnection counts
        ip_reconnection_counts = {}
        
        # Process each IP separately
        for ip, group in sorted_df.groupby(ip_col):
            # Skip IPs with only one attempt
            if len(group) <= 1:
                continue
                
            # Convert timestamps to a list
            timestamps = group[timestamp_col].tolist()
            
            # Count reconnections within different time intervals (in minutes)
            intervals = {
                '< 1 min': 0,
                '1-5 mins': 0,
                '5-15 mins': 0,
                '15-30 mins': 0,
                '30-60 mins': 0,
                '> 60 mins': 0
            }
            
            # Calculate time differences between consecutive attempts
            for i in range(1, len(timestamps)):
                time_diff = (timestamps[i] - timestamps[i-1]).total_seconds() / 60  # Convert to minutes
                
                if time_diff < 1:
                    intervals['< 1 min'] += 1
                elif time_diff < 5:
                    intervals['1-5 mins'] += 1
                elif time_diff < 15:
                    intervals['5-15 mins'] += 1
                elif time_diff < 30:
                    intervals['15-30 mins'] += 1
                elif time_diff < 60:
                    intervals['30-60 mins'] += 1
                else:
                    intervals['> 60 mins'] += 1
            
            # Store the counts for this IP
            ip_reconnection_counts[ip] = intervals
        
        # Check if we have any reconnection data
        if not ip_reconnection_counts:
            print("No reconnection patterns found in the data")
            return
            
        print(f"Found reconnection patterns for {len(ip_reconnection_counts)} IP addresses")
        
        # Create DataFrame from the counts
        columns = ['< 1 min', '1-5 mins', '5-15 mins', '15-30 mins', '30-60 mins', '> 60 mins']
        reconnection_data = pd.DataFrame.from_dict(ip_reconnection_counts, orient='index', columns=columns)
        
        # Calculate total reconnections for each IP
        reconnection_data['total'] = reconnection_data.sum(axis=1)
        
        # Sort by total reconnections and get top 15 (or less if we have fewer IPs)
        top_count = min(15, len(reconnection_data))
        top_ips = reconnection_data.sort_values('total', ascending=False).head(top_count)
        
        # Remove the total column for plotting
        top_ips = top_ips.drop(columns=['total'])
        
        # Plot the stacked bar chart
        plt.figure(figsize=(14, 10))
        
        # Create a stacked bar chart
        top_ips.plot(kind='barh', stacked=True, figsize=(14, 10), 
                     colormap='viridis', width=0.8)
        
        plt.title(f'Reconnection Frequency Analysis by IP Address (Top {top_count})', fontsize=16)
        plt.xlabel('Number of Reconnection Attempts', fontsize=14)
        plt.ylabel('IP Address', fontsize=14)
        plt.legend(title='Time Interval Between Attempts')
        plt.grid(axis='x', alpha=0.3)
        plt.tight_layout()
        
        plt.savefig(f"{output_dir}/ip_reconnection_frequency.png", bbox_inches='tight')
        plt.close()
        
        # Create a second visualization: distribution of reconnection intervals
        interval_totals = top_ips.sum()
        
        plt.figure(figsize=(12, 7))
        interval_totals.plot(kind='bar', color=plt.cm.viridis(np.linspace(0, 1, len(interval_totals))))
        
        plt.title('Distribution of Time Intervals Between Reconnection Attempts', fontsize=16)
        plt.xlabel('Time Interval', fontsize=14)
        plt.ylabel('Number of Reconnection Attempts', fontsize=14)
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        
        plt.savefig(f"{output_dir}/reconnection_interval_distribution.png", bbox_inches='tight')
        plt.close()
        
        print("Generated IP reconnection frequency analysis")
    except Exception as e:
        print(f"Error analyzing IP reconnection frequency: {str(e)}")
        import traceback
        traceback.print_exc()

# Create all visualizations
create_visualization(username_chart, "username distribution chart")
create_visualization(login_success_chart, "login success rate chart")
create_visualization(country_chart, "country distribution chart")
create_visualization(ip_chart, "IP distribution chart")
create_visualization(subnet_chart, "subnet distribution chart")
create_visualization(command_count_chart, "command count chart")
create_visualization(connection_timeline, "connection timeline chart")


# Ajoutez ces lignes pour les nouveaux graphiques
create_visualization(login_time_heatmap, "login time heatmap")
create_visualization(credentials_heatmap, "credentials heatmap")
create_visualization(ip_diversity_chart, "IP diversity chart")
create_visualization(password_prefix_chart, "password prefix chart")
create_visualization(success_by_country, "success by country chart")
# Ajoutez geo_map_chart uniquement si vous avez installé Basemap
create_visualization(geo_map_folium, "geographical map")
create_visualization(password_pie_chart, "password distribution pie chart")
create_visualization(login_attempts_timeline, "login attempts timeline") 
create_visualization(login_attempts_timeline_alt, "login attempts timeline alt")
create_visualization(ip_reconnection_frequency, "IP reconnection frequency analysis")

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