# uv run streamlit run cola_streamlit_app.py
import streamlit as st
import duckdb
import os
import json
import random
import pandas as pd
from dotenv import load_dotenv
import altair as alt

# Load environment variables from .env file
load_dotenv()

# MotherDuck database configuration
# Set your MotherDuck token as an environment variable: MOTHERDUCK_TOKEN
# Database format: md:<database_name> or md:<database_name>.<schema_name>
MOTHERDUCK_DATABASE = os.getenv('MOTHERDUCK_DATABASE', 'md:cola_data')  # Default database name
MOTHERDUCK_TOKEN = os.getenv('MOTHERDUCK_TOKEN')  # Required for authentication
HIGHLIGHT_COLOR = "#00ff99"  # Color for highlighted terms
IMAGE_INFO_HEADER_COLOR = "#00ff99"  # Color for image info headers
DETAIL_URL = "https://ttbonline.gov/colasonline/viewColaDetails.do?action=publicDisplaySearchAdvanced&ttbid="
IMAGES_URL = "https://ttbonline.gov/colasonline/viewColaDetails.do?action=publicFormDisplay&ttbid="

commodity_color_map = {
    'wine': "#DD35DD",
    'beer': "#ECA349", 
    'distilled_spirits': "#5DCB8B"
}
default_color = "#8D8D8D"

def get_motherduck_connection():
    """
    Create and return a MotherDuck connection with proper error handling.
    """
    if not MOTHERDUCK_TOKEN:
        st.error("MotherDuck token not found. Please set the MOTHERDUCK_TOKEN environment variable.")
        st.info("You can get your token from the MotherDuck console at https://app.motherduck.com/")
        st.stop()
    
    try:
        # Connect to MotherDuck with token authentication
        # Note: You can also use duckdb.connect() and then execute SET motherduck_token = 'token'
        con = duckdb.connect(f"{MOTHERDUCK_DATABASE}?motherduck_token={MOTHERDUCK_TOKEN}")
        
        # Test the connection by running a simple query
        con.execute("SELECT 1").fetchone()
        return con
        
    except Exception as e:
        error_msg = str(e)
        st.error(f"Failed to connect to MotherDuck database: {error_msg}")
        st.info(f"Trying to connect to: {MOTHERDUCK_DATABASE}")
        
        # Specific error handling for common issues
        if "database aliases are not yet supported" in error_msg.lower():
            st.error("🔍 **Database Alias Issue**: Your database uses aliases which aren't supported in MotherDuck workspace mode.")
            st.info("**Solutions:**")
            st.info("• Use the direct database name instead of an alias")
            st.info("• Ensure all tables are in the same database") 
            st.info("• Try a different MOTHERDUCK_DATABASE connection string")
            st.info("• Contact MotherDuck support about workspace mode limitations")
            
        elif "authentication" in error_msg.lower() or "token" in error_msg.lower():
            st.error("🔑 **Authentication Issue**: Please verify your MOTHERDUCK_TOKEN is correct and not expired.")
            
        elif "database" in error_msg.lower() and "not found" in error_msg.lower():
            st.error("🗄️ **Database Not Found**: The specified database doesn't exist or you don't have access.")
        
        st.info("**General troubleshooting:**")
        st.info("• Verify your MOTHERDUCK_TOKEN and MOTHERDUCK_DATABASE environment variables")
        st.info("• Run `uv run python test_motherduck.py` for detailed diagnostics")
        st.info("• Check the MotherDuck console for database availability")
        
        st.stop()

def get_commodity_icon(commodity):
    """
    Return an appropriate icon for the commodity type.
    
    Commodity types from cola_images.vw_colas.ct_commodity:
    - 'beer': Beer and malt beverages
    - 'wine': Wine, cider, mead, sake  
    - 'distilled_spirits': Distilled spirits and liqueurs
    - 'unknown': Unclassified or missing data
    """
    if not commodity:
        return "❓"  # Unknown
    
    commodity_lower = str(commodity).lower()
    if commodity_lower == 'beer':
        return "🍺"  # Beer mug
    elif commodity_lower == 'wine':
        return "🍷"  # Wine glass
    elif commodity_lower == 'distilled_spirits':
        return "🍸"  # Cocktail
    else:
        return "🍶"  # Default alcoholic beverage

def get_flag_icon(origin, ct_source=None):
    """
    Return an appropriate flag icon for the origin/country.
    
    Uses ct_source from database view to prioritize domestic vs import classification,
    then maps specific origin values to their corresponding flag emojis.
    """
    # First check ct_source from database view - prioritize domestic
    if ct_source and str(ct_source).lower().strip() == 'domestic':
        return '🇺🇸'
    
    if not origin:
        # If we have ct_source but no specific origin, use generic import flag
        if ct_source and str(ct_source).lower().strip() == 'import':
            return '🌍'
        return ""
    
    origin_lower = str(origin).lower().strip()
    
    # Also check origin field for 'domestic' as fallback
    if 'domestic' in origin_lower:
        return '🇺🇸'
    
    # Map origins to flag emojis
    flag_map = {
        # US variations
        'united states': '🇺🇸',
        'usa': '🇺🇸',
        'us': '🇺🇸',
        'american': '🇺🇸',
        
        # Common countries
        'france': '🇫🇷',
        'french': '🇫🇷',
        'italy': '🇮🇹',
        'italian': '🇮🇹',
        'spain': '🇪🇸',
        'spanish': '🇪🇸',
        'germany': '🇩🇪',
        'german': '🇩🇪',
        'portugal': '🇵🇹',
        'portuguese': '🇵🇹',
        'chile': '🇨🇱',
        'chilean': '🇨🇱',
        'argentina': '🇦🇷',
        'argentine': '🇦🇷',
        'australia': '🇦🇺',
        'australian': '🇦🇺',
        'new zealand': '🇳🇿',
        'canada': '🇨🇦',
        'canadian': '🇨🇦',
        'mexico': '🇲🇽',
        'mexican': '🇲🇽',
        'japan': '🇯🇵',
        'japanese': '🇯🇵',
        'south africa': '🇿🇦',
        'austria': '🇦🇹',
        'austrian': '🇦🇹',
        'hungary': '🇭🇺',
        'hungarian': '🇭🇺',
        'greece': '🇬🇷',
        'greek': '🇬🇷',
        'turkey': '🇹🇷',
        'turkish': '🇹🇷',
        'israel': '🇮🇱',
        'lebanon': '🇱🇧',
        'india': '🇮🇳',
        'china': '🇨🇳',
        'chinese': '🇨🇳',
        'korea': '🇰🇷',
        'korean': '🇰🇷',
        'south korea': '🇰🇷',
        'brazil': '🇧🇷',
        'brazilian': '🇧🇷',
        'peru': '🇵🇪',
        'peruvian': '🇵🇪',
        'uruguay': '🇺🇾',
        'colombia': '🇨🇴',
        'colombian': '🇨🇴',
        'ecuador': '🇪🇨',
        'bolivia': '🇧🇴',
        'venezuela': '🇻🇪',
        'armenia': '🇦🇲',
        'armenian': '🇦🇲',
        'georgia': '🇬🇪',
        'georgian': '🇬🇪',
        'moldova': '🇲🇩',
        'ukraine': '🇺🇦',
        'ukrainian': '🇺🇦',
        'russia': '🇷🇺',
        'russian': '🇷🇺',
        'poland': '🇵🇱',
        'polish': '🇵🇱',
        'czech republic': '🇨🇿',
        'czech': '🇨🇿',
        'slovakia': '🇸🇰',
        'slovak': '🇸🇰',
        'slovenia': '🇸🇮',
        'croatia': '🇭🇷',
        'croatian': '🇭🇷',
        'serbia': '🇷🇸',
        'serbian': '🇷🇸',
        'bulgaria': '🇧🇬',
        'bulgarian': '🇧🇬',
        'romania': '🇷🇴',
        'romanian': '🇷🇴',
        'ireland': '🇮🇪',
        'irish': '🇮🇪',
        'scotland': '🏴',
        'scottish': '🏴',
        'england': '🏴',
        'english': '🏴',
        'wales': '🏴',
        'welsh': '🏴',
        'united kingdom': '🇬🇧',
        'uk': '🇬🇧',
        'britain': '🇬🇧',
        'british': '🇬🇧',
        'netherlands': '🇳🇱',
        'dutch': '🇳🇱',
        'belgium': '🇧🇪',
        'belgian': '🇧🇪',
        'switzerland': '🇨🇭',
        'swiss': '🇨🇭',
        'denmark': '🇩🇰',
        'danish': '🇩🇰',
        'sweden': '🇸🇪',
        'swedish': '🇸🇪',
        'norway': '🇳🇴',
        'norwegian': '🇳🇴',
        'finland': '🇫🇮',
        'finnish': '🇫🇮',
        'iceland': '🇮🇸',
        'icelandic': '🇮🇸',
        'luxembourg': '🇱🇺',
        'malta': '🇲🇹',
        'cyprus': '🇨🇾',
        'estonia': '🇪🇪',
        'latvia': '🇱🇻',
        'lithuania': '🇱🇹',
        'morocco': '🇲🇦',
        'moroccan': '🇲🇦',
        'tunisia': '🇹🇳',
        'algeria': '🇩🇿',
        'egypt': '🇪🇬',
        'egyptian': '🇪🇬',
        'ethiopia': '🇪🇹',
        'kenya': '🇰🇪',
        'madagascar': '🇲🇬',
        'thailand': '🇹🇭',
        'thai': '🇹🇭',
        'vietnam': '🇻🇳',
        'vietnamese': '🇻🇳',
        'cambodia': '🇰🇭',
        'laos': '🇱🇦',
        'myanmar': '🇲🇲',
        'philippines': '🇵🇭',
        'filipino': '🇵🇭',
        'indonesia': '🇮🇩',
        'indonesian': '🇮🇩',
        'malaysia': '🇲🇾',
        'singapore': '🇸🇬',
        'sri lanka': '🇱🇰',
        'bangladesh': '🇧🇩',
        'pakistan': '🇵🇰',
        'nepal': '🇳🇵',
        'bhutan': '🇧🇹',
        'mongolia': '🇲🇳',
        'taiwan': '🇹🇼',
        'hong kong': '🇭🇰',
        'macau': '🇲🇴'
    }
    
    # Check for exact match first
    if origin_lower in flag_map:
        return flag_map[origin_lower]
    
    # Check for partial matches (origin contains country name)
    for country, flag in flag_map.items():
        if country in origin_lower:
            return flag
    
    # Default: if we know it's an import from ct_source, show import flag
    # Only return empty string if origin is truly empty/unknown
    if ct_source and str(ct_source).lower().strip() == 'import':
        return '🌍'  # Globe icon for imports without specific country match
    elif origin_lower and origin_lower not in ['unknown', 'n/a', '', 'none']:
        return '🌍'  # Globe icon for generic imports
    
    return ""

def get_unique_values(cola_data, key):
    # Replace None or empty values with 'UNKNOWN' and ensure all are strings
    return sorted(set(str(c.get(key)) if c.get(key) not in [None, ''] else 'UNKNOWN' for c in cola_data))

def highlight_term(text, term):
    if not term or not isinstance(text, str):
        return text
    import re
    pattern = re.compile(re.escape(term), re.IGNORECASE)
    return pattern.sub(lambda m: f"<mark style='background: {HIGHLIGHT_COLOR}'>{m.group(0)}</mark>", text)

def is_cola_id_list(search_term):
    """
    Check if the search term is a comma-separated list of 14-digit COLA IDs.
    Returns tuple (is_cola_list, cola_ids_list) where:
    - is_cola_list: True if the search term matches the pattern
    - cola_ids_list: List of valid COLA IDs if is_cola_list is True, empty list otherwise
    """
    if not search_term or not isinstance(search_term, str):
        return False, []
    
    # Split by comma and strip whitespace
    parts = [part.strip() for part in search_term.split(',')]
    
    # Check if all parts are exactly 14 digits
    cola_ids = []
    for part in parts:
        if len(part) == 14 and part.isdigit():
            cola_ids.append(part)
        else:
            # If any part is not a 14-digit number, this is not a COLA ID list
            return False, []
    
    # Must have at least one COLA ID
    if cola_ids:
        return True, cola_ids
    else:
        return False, []

def main():
    # Add logo at the top using st.logo()
    logo_path = os.path.join(os.path.dirname(__file__), 'resources/cola_search_logo.png')
    if os.path.exists(logo_path):
        st.logo(logo_path, size="large")
    st.title('TTB COLA Data Explorer')

    # Connect to MotherDuck database
    con = get_motherduck_connection()

    # Load filters from URL parameters
    query_params = st.query_params
    
    # Helper function to parse comma-separated values from URL
    def parse_url_list(param_value):
        if param_value:
            return [item.strip() for item in param_value.split(',') if item.strip()]
        return []

    # Sidebar filters
    st.sidebar.header('Filters')
    search_term = st.sidebar.text_input('Search (ID, Brand, Analysis, etc.)', value=query_params.get('search', ''))
    exclude_term = st.sidebar.text_input('Exclude phrase (optional)', value=query_params.get('exclude', ''))

    # Date range filter for completed_date
    min_date = con.execute('SELECT MIN(completed_date) from cola_images.colas WHERE completed_date IS NOT NULL').fetchone()[0]
    max_date = con.execute('SELECT MAX(completed_date) from cola_images.colas WHERE completed_date IS NOT NULL').fetchone()[0]
    if min_date and max_date:
        min_date = min_date.strftime('%Y-%m-%d') if hasattr(min_date, 'strftime') else str(min_date)
        max_date = max_date.strftime('%Y-%m-%d') if hasattr(max_date, 'strftime') else str(max_date)
        
        # Check for URL parameters for date range
        url_start_date = query_params.get('start_date')
        url_end_date = query_params.get('end_date')
        
        # Default to defined # of days before max date, but not earlier than min_date
        from datetime import datetime, timedelta
        max_date_obj = datetime.strptime(max_date, '%Y-%m-%d')
        min_date_obj = datetime.strptime(min_date, '%Y-%m-%d')
        default_start_obj = max_date_obj - timedelta(days=14)
        
        # Ensure default start is not before the minimum available date
        if default_start_obj < min_date_obj:
            default_start_obj = min_date_obj
            
        default_start = default_start_obj.strftime('%Y-%m-%d')
        
        # Use URL parameters if available, otherwise use defaults
        if url_start_date and url_end_date:
            try:
                # Validate the URL date parameters
                datetime.strptime(url_start_date, '%Y-%m-%d')
                datetime.strptime(url_end_date, '%Y-%m-%d')
                default_date_range = (url_start_date, url_end_date)
            except ValueError:
                default_date_range = (default_start, max_date)
        else:
            default_date_range = (default_start, max_date)
        
        date_range = st.sidebar.date_input('Completed Date Range', value=default_date_range, min_value=min_date, max_value=max_date)
        if isinstance(date_range, tuple) and len(date_range) == 2:
            selected_start, selected_end = date_range
        else:
            selected_start, selected_end = default_start, max_date
    else:
        selected_start, selected_end = None, None

    # Query DuckDB for unique origin and class type options
    origin_options = [row[0] if row[0] else 'UNKNOWN' for row in con.execute("SELECT DISTINCT COALESCE(origin, 'UNKNOWN') from cola_images.colas").fetchall()]
    origin_options = sorted(set(str(o) for o in origin_options))
    class_type_options = [row[0] if row[0] else 'UNKNOWN' for row in con.execute("SELECT DISTINCT COALESCE(class_type, 'UNKNOWN') from cola_images.colas").fetchall()]
    class_type_options = sorted(set(str(c) for c in class_type_options))
    
    # Query for brand options
    brand_options = [row[0] if row[0] else 'UNKNOWN' for row in con.execute("SELECT DISTINCT COALESCE(brand_name, 'UNKNOWN') from cola_images.colas WHERE brand_name IS NOT NULL AND TRIM(brand_name) != ''").fetchall()]
    brand_options = sorted(set(str(b) for b in brand_options))
    
    # Query for violation group options from violations
    violation_group_options = [row[0] for row in con.execute("SELECT DISTINCT violation_group FROM cola_images.vw_cola_violations_list WHERE violation_group IS NOT NULL AND TRIM(violation_group) != '' ORDER BY violation_group").fetchall()]
    violation_group_options = sorted(set(str(c) for c in violation_group_options))
    
    # Query for commodity options from cola_images.vw_colas with custom ordering
    commodity_data = con.execute("SELECT DISTINCT ct_commodity from cola_images.vw_colas WHERE ct_commodity IS NOT NULL").fetchall()
    commodity_options_raw = [row[0] for row in commodity_data]
    
    # Custom order: Wine, Beer, Distilled Spirits, then others
    commodity_order = ['wine', 'beer', 'distilled_spirits']
    commodity_options = []
    
    # Add commodities in preferred order
    for commodity in commodity_order:
        if commodity in commodity_options_raw:
            commodity_options.append(commodity)
    
    # Add any remaining commodities not in the preferred order
    for commodity in sorted(commodity_options_raw):
        if commodity not in commodity_options:
            commodity_options.append(commodity)
    
    # Create commodity display options with icons
    commodity_display_options = []
    commodity_value_map = {}
    for commodity in commodity_options:
        icon = get_commodity_icon(commodity)
        display_name = f"{icon} {commodity.replace('_', ' ').title()}"
        commodity_display_options.append(display_name)
        commodity_value_map[display_name] = commodity
    
    selected_commodity_display = st.sidebar.multiselect('Commodity', commodity_display_options, default=[display for display in commodity_display_options if commodity_value_map[display] in parse_url_list(query_params.get('commodity', ''))])
    selected_origin = st.sidebar.multiselect('Origin', origin_options, default=parse_url_list(query_params.get('origin', '')))
    selected_class_type = st.sidebar.multiselect('Class Type', class_type_options, default=parse_url_list(query_params.get('class_type', '')))
    selected_brand = st.sidebar.multiselect('Brand Name', brand_options, default=parse_url_list(query_params.get('brand', '')))
    selected_violation_group = st.sidebar.multiselect('Violation Group (from review warnings)', violation_group_options, default=parse_url_list(query_params.get('violation_group', '')))
    
    # Convert display selections back to actual values
    selected_commodity = [commodity_value_map[display] for display in selected_commodity_display]

    # Update URL parameters to reflect current filter state
    new_query_params = {}
    
    if search_term:
        new_query_params['search'] = search_term
    if exclude_term:
        new_query_params['exclude'] = exclude_term
    if selected_start and selected_end:
        new_query_params['start_date'] = str(selected_start)
        new_query_params['end_date'] = str(selected_end)
    if selected_commodity:
        new_query_params['commodity'] = ','.join(selected_commodity)
    if selected_origin:
        new_query_params['origin'] = ','.join(selected_origin)
    if selected_class_type:
        new_query_params['class_type'] = ','.join(selected_class_type)
    if selected_brand:
        new_query_params['brand'] = ','.join(selected_brand)
    if selected_violation_group:
        new_query_params['violation_group'] = ','.join(selected_violation_group)
    
    # Update query parameters (this creates a shareable URL)
    st.query_params.update(new_query_params)

    # Check if any non-date filters are active to show "Show All Available Dates" button
    has_other_filters = bool(
        search_term or 
        exclude_term or 
        selected_commodity or 
        selected_origin or 
        selected_class_type or 
        selected_brand or 
        selected_violation_group
    )
    
    # Add button to expand to full date range only if other filters are active
    if has_other_filters and min_date and max_date:
        if st.sidebar.button("📅 Show All Available Dates", help="Expand date range to include all COLA records"):
            # Update query parameters to include full date range
            st.query_params.update({
                'start_date': min_date,
                'end_date': max_date
            })
            st.rerun()

    # Build optimized query based on filters
    # Start with base COLA query using vw_colas for better performance
    base_query = "SELECT * from cola_images.vw_colas c"
    where_clauses = []
    params = []
    
    # Check if search term is a comma-separated list of 14-digit COLA IDs
    is_cola_list = False
    cola_ids = []
    if search_term:
        is_cola_list, cola_ids = is_cola_id_list(search_term)
    
    if is_cola_list:
        # When searching for specific COLA IDs, ignore all other filters
        where_clauses.append('c.cola_id IN (' + ','.join(['?' for _ in cola_ids]) + ')')
        params.extend(cola_ids)
    else:
        # Apply all filters only when NOT searching for specific COLA IDs
        
        # Apply basic filters
        if selected_origin:
            where_clauses.append('COALESCE(c.origin, \'UNKNOWN\') IN (' + ','.join(['?' for _ in selected_origin]) + ')')
            params.extend(selected_origin)
        if selected_class_type:
            where_clauses.append('COALESCE(c.class_type, \'UNKNOWN\') IN (' + ','.join(['?' for _ in selected_class_type]) + ')')
            params.extend(selected_class_type)
        if selected_commodity:
            where_clauses.append('c.ct_commodity IN (' + ','.join(['?' for _ in selected_commodity]) + ')')
            params.extend(selected_commodity)
        if selected_brand:
            where_clauses.append('COALESCE(c.brand_name, \'UNKNOWN\') IN (' + ','.join(['?' for _ in selected_brand]) + ')')
            params.extend(selected_brand)
        if selected_violation_group:
            # Filter COLAs that have violations with the selected violation groups
            where_clauses.append('''
                EXISTS (
                    SELECT 1 FROM cola_images.vw_cola_violations_list v 
                    WHERE v.cola_id = c.cola_id 
                    AND v.violation_group IN (''' + ','.join(['?' for _ in selected_violation_group]) + ''')
                )
            ''')
            params.extend(selected_violation_group)
        if selected_start and selected_end:
            where_clauses.append('completed_date BETWEEN ? AND ?')
            params.extend([str(selected_start), str(selected_end)])
        
        # Handle search terms efficiently
        if search_term or exclude_term:
            if search_term:
                # Regular text search across multiple fields
                term = f"%{search_term.lower()}%"
                search_conditions = [
                    'LOWER(CAST(c.cola_id AS VARCHAR)) LIKE ?',
                    'LOWER(COALESCE(c.brand_name, \'\')) LIKE ?',
                    'LOWER(COALESCE(c.fanciful_name, \'\')) LIKE ?',
                    'LOWER(COALESCE(c.permit_num, \'\')) LIKE ?',
                    'LOWER(COALESCE(c.serial_num, \'\')) LIKE ?'
                ]
                
                # Add image analysis search if needed
                search_conditions.append("""
                    EXISTS (
                        SELECT 1 from cola_images.image_analysis_items iai 
                        WHERE iai.cola_id = c.cola_id 
                        AND LOWER(COALESCE(iai.text, '')) LIKE ?
                    )
                """)
                
                # Add violation search if needed
                search_conditions.append("""
                    EXISTS (
                        SELECT 1 from cola_images.cola_analysis ca
                        WHERE ca.cola_id = c.cola_id
                        AND (
                            LOWER(CAST(ca.response AS VARCHAR)) LIKE ?
                            OR LOWER(CAST(ca.metadata AS VARCHAR)) LIKE ?
                        )
                    )
                """)
                
                where_clauses.append('(' + ' OR '.join(search_conditions) + ')')
                params.extend([term] * 8)  # 5 basic fields + 1 image analysis + 2 violation fields
            
            if exclude_term:
                ex_term = f"%{exclude_term.lower()}%"
                exclude_conditions = [
                    'LOWER(CAST(c.cola_id AS VARCHAR)) LIKE ?',
                    'LOWER(COALESCE(c.brand_name, \'\')) LIKE ?',
                    'LOWER(COALESCE(c.fanciful_name, \'\')) LIKE ?',
                    'LOWER(COALESCE(c.permit_num, \'\')) LIKE ?',
                    'LOWER(COALESCE(c.serial_num, \'\')) LIKE ?'
                ]
                
                exclude_conditions.append("""
                    EXISTS (
                        SELECT 1 from cola_images.image_analysis_items iai 
                        WHERE iai.cola_id = c.cola_id 
                        AND LOWER(COALESCE(iai.text, '')) LIKE ?
                    )
                """)
                
                exclude_conditions.append("""
                    EXISTS (
                        SELECT 1 from cola_images.cola_analysis ca
                        WHERE ca.cola_id = c.cola_id
                        AND (
                            LOWER(CAST(ca.response AS VARCHAR)) LIKE ?
                            OR LOWER(CAST(ca.metadata AS VARCHAR)) LIKE ?
                        )
                    )
                """)
                
                where_clauses.append('NOT (' + ' OR '.join(exclude_conditions) + ')')
                params.extend([ex_term] * 8)
    
    # Build final WHERE clause
    where_sql = ('WHERE ' + ' AND '.join(where_clauses)) if where_clauses else ''
    
    # Execute main query
    main_query = f"{base_query} {where_sql} ORDER BY completed_date DESC"
    df = con.execute(main_query, params).fetchdf()
    
    # Get the cola_ids for additional data fetching
    cola_ids = df['cola_id'].tolist()
    
    # Fetch images data separately for better performance
    images_data = {}
    if cola_ids:
        images_query = """
            SELECT 
                ci.cola_id,
                json_group_array(
                    json_object(
                        'public_url', ci.public_url,
                        'img_type', ci.img_type,
                        'file_name', ci.file_name,
                        'dimensions_txt', ci.dimensions_txt,
                        'analysis_items', COALESCE(
                            (
                                SELECT json_group_array(json_object(
                                    'analysis_item_type', iai.analysis_item_type,
                                    'text', iai.text,
                                    'model_confidence', iai.model_confidence,
                                    'bounding_box', iai.bounding_box
                                ))
                                from cola_images.image_analysis_items iai
                                WHERE iai.cola_id = ci.cola_id AND iai.file_name = ci.file_name
                            ), 
                            '[]'
                        )
                    )
                ) AS images_json
            from cola_images.vw_cola_images ci
            WHERE ci.cola_id IN (""" + ','.join(['?' for _ in cola_ids]) + """)
            AND ci.public_url IS NOT NULL
            GROUP BY ci.cola_id
        """
        
        images_df = con.execute(images_query, cola_ids).fetchdf()
        for _, row in images_df.iterrows():
            try:
                images_data[row['cola_id']] = json.loads(row['images_json'])
            except Exception:
                images_data[row['cola_id']] = []
    
    # Fetch violations data separately - always fetch when we have COLAs to ensure violations display properly
    violations_data = {}
    if cola_ids:
        violations_query = """
            SELECT 
                cola_id,
                json_group_array(
                    json_object(
                        'violation_comment', violation_comment,
                        'violation_type', violation_type,
                        'violation_group', violation_group,
                        'violation_subgroup', violation_subgroup,
                        'cfr_ref', cfr_ref
                    )
                ) AS violations_json
            FROM cola_images.vw_cola_violations_list
            WHERE cola_id IN (""" + ','.join(['?' for _ in cola_ids]) + """)
            GROUP BY cola_id
        """
        
        violations_df = con.execute(violations_query, cola_ids).fetchdf()
        for _, row in violations_df.iterrows():
            try:
                violations_data[row['cola_id']] = json.loads(row['violations_json'])
            except Exception:
                violations_data[row['cola_id']] = []
    
    # Combine data
    filtered = df.to_dict(orient='records')
    for rec in filtered:
        cola_id = rec['cola_id']
        rec['images'] = images_data.get(cola_id, [])
        rec['violations'] = violations_data.get(cola_id, [])
    
    # Shuffle for variety
    random.shuffle(filtered)

    # Add search explanation showing active filters
    filter_explanations = []
    
    # Date range explanation
    if selected_start and selected_end:
        from datetime import datetime
        if isinstance(selected_start, str):
            start_date = datetime.strptime(selected_start, '%Y-%m-%d').strftime('%B %d, %Y')
        else:
            start_date = selected_start.strftime('%B %d, %Y')
        
        if isinstance(selected_end, str):
            end_date = datetime.strptime(selected_end, '%Y-%m-%d').strftime('%B %d, %Y')
        else:
            end_date = selected_end.strftime('%B %d, %Y')
        
        filter_explanations.append(f"with completion date from {start_date} through {end_date}")
    
    # Commodity filter explanation
    if selected_commodity:
        if len(selected_commodity) == 1:
            commodity_text = selected_commodity[0].replace('_', ' ').title()
            filter_explanations.append(f"limited to {commodity_text} COLAs only")
        else:
            commodity_list = [c.replace('_', ' ').title() for c in selected_commodity]
            if len(commodity_list) == 2:
                commodity_text = ' and '.join(commodity_list)
            else:
                commodity_text = ', '.join(commodity_list[:-1]) + ', and ' + commodity_list[-1]
            filter_explanations.append(f"limited to {commodity_text} COLAs")
    
    # Brand filter explanation
    if selected_brand:
        if len(selected_brand) == 1:
            filter_explanations.append(f"for brand {selected_brand[0]}")
        else:
            if len(selected_brand) == 2:
                brand_text = ' and '.join(selected_brand)
            else:
                brand_text = ', '.join(selected_brand[:-1]) + ', and ' + selected_brand[-1]
            filter_explanations.append(f"for brands {brand_text}")
    
    # Origin filter explanation
    if selected_origin:
        if len(selected_origin) == 1:
            filter_explanations.append(f"of origin {selected_origin[0]}")
        else:
            if len(selected_origin) == 2:
                origin_text = ' and '.join(selected_origin)
            else:
                origin_text = ', '.join(selected_origin[:-1]) + ', and ' + selected_origin[-1]
            filter_explanations.append(f"of origins {origin_text}")
    
    # Class Type filter explanation
    if selected_class_type:
        if len(selected_class_type) == 1:
            filter_explanations.append(f"with Class Type = {selected_class_type[0]}")
        else:
            class_type_list = ', '.join(selected_class_type)
            filter_explanations.append(f"with Class Type = [{class_type_list}]")
    
    # Violation Group filter explanation
    if selected_violation_group:
        if len(selected_violation_group) == 1:
            filter_explanations.append(f"with {selected_violation_group[0]} violations")
        else:
            if len(selected_violation_group) == 2:
                violation_text = ' and '.join(selected_violation_group)
            else:
                violation_text = ', '.join(selected_violation_group[:-1]) + ', and ' + selected_violation_group[-1]
            filter_explanations.append(f"with {violation_text} violations")
    
    # Search term explanation
    if search_term and not is_cola_list:
        filter_explanations.append(f"matching search term '{search_term}'")
    elif is_cola_list:
        if len(cola_ids) == 1:
            filter_explanations.append(f"for COLA ID {cola_ids[0]}")
        else:
            filter_explanations.append(f"for {len(cola_ids)} specific COLA IDs")
    
    # Exclude term explanation
    if exclude_term:
        filter_explanations.append(f"excluding '{exclude_term}'")
    
    # Build the results message with inline filter explanation
    results_message = f"Found {len(filtered):,} COLA records"
    
    # Add filter explanation inline if any filters are active
    if filter_explanations:
        explanation_text = ', '.join(filter_explanations)
        results_message += f" {explanation_text}"
    
    # Add limiting note if applicable
    if len(filtered) > 100:
        results_message += ", limiting to 100 results displayed"
    
    st.write(results_message)
    
    # Show commodity distribution summary
    if filtered:
        commodity_counts = {}
        for record in filtered:
            commodity = record.get('ct_commodity', 'unknown')
            commodity_counts[commodity] = commodity_counts.get(commodity, 0) + 1
        
        if len(commodity_counts) > 1:  # Only show if there are multiple commodities
            commodity_summary = []
            
            # Custom order for summary: Wine, Beer, Distilled Spirits, then others
            summary_order = ['wine', 'beer', 'distilled_spirits']
            
            # Add commodities in preferred order first
            for commodity in summary_order:
                if commodity in commodity_counts:
                    count = commodity_counts[commodity]
                    icon = get_commodity_icon(commodity)
                    color = commodity_color_map.get(commodity, default_color)
                    commodity_summary.append(f"{icon} <span style='color:{color}'>■</span> {count:,}")
            
            # Add any remaining commodities not in the preferred order
            for commodity in sorted(commodity_counts.keys()):
                if commodity not in summary_order:
                    count = commodity_counts[commodity]
                    icon = get_commodity_icon(commodity)
                    color = commodity_color_map.get(commodity, default_color)
                    commodity_summary.append(f"{icon} <span style='color:{color}'>■</span> {count:,}")
            
            st.markdown(f"**Commodity Distribution:** {' | '.join(commodity_summary)}", unsafe_allow_html=True)

    if filtered:
        try:
            chart_df = pd.DataFrame(filtered)
            if 'completed_date' in chart_df.columns and not chart_df['completed_date'].isnull().all():
                chart_df['completed_date'] = pd.to_datetime(chart_df['completed_date'])
                
                # Determine granularity based on the selected date range
                from datetime import date, datetime
                if isinstance(selected_start, date):
                    start_date_obj = selected_start
                else:
                    start_date_obj = datetime.strptime(str(selected_start), '%Y-%m-%d').date()
                
                if isinstance(selected_end, date):
                    end_date_obj = selected_end
                else:
                    end_date_obj = datetime.strptime(str(selected_end), '%Y-%m-%d').date()

                date_diff_days = (end_date_obj - start_date_obj).days
                
                # Determine granularity based on the selected date range
                if date_diff_days > 365:  # More than a year -> Monthly
                    chart_df['time_agg'] = chart_df['completed_date'].dt.to_period('M').apply(lambda p: p.start_time).dt.date
                    x_axis_title = 'Month'
                elif date_diff_days > 60:  # 2 to 12 months -> Weekly
                    chart_df['time_agg'] = chart_df['completed_date'].dt.to_period('W').apply(lambda p: p.start_time).dt.date
                    x_axis_title = 'Week'
                else:  # Up to 2 months -> Daily
                    chart_df['time_agg'] = chart_df['completed_date'].dt.date
                    x_axis_title = 'Completed Date'

                cola_counts = chart_df.groupby(['time_agg', 'ct_commodity']).size().unstack(fill_value=0)

                if not cola_counts.empty:
                    # Reorder columns to match commodity summary order for consistent colors
                    commodity_order = ['wine', 'beer', 'distilled_spirits']
                    present_commodities = [c for c in commodity_order if c in cola_counts.columns]
                    other_commodities = sorted([c for c in cola_counts.columns if c not in commodity_order])
                    final_order = present_commodities + other_commodities
                    
                    cola_counts = cola_counts[final_order]

                    # Convert data to long format for Altair/Vega-Lite
                    chart_data_long = cola_counts.reset_index().melt(
                        id_vars='time_agg',
                        value_vars=final_order,
                        var_name='ct_commodity',
                        value_name='count'
                    )
                    
                    # Create Altair chart
                    base_chart = alt.Chart(chart_data_long)
                    
                    # Bar chart layer
                    bars = base_chart.mark_bar(width={'band': 0.8}).encode(
                        x=alt.X('time_agg:T', title=x_axis_title, axis=alt.Axis(labelAngle=-45)),
                        y=alt.Y('count:Q', title='COLA Count'),
                        color=alt.Color('ct_commodity:N', 
                                        scale=alt.Scale(
                                            domain=final_order, 
                                            range=[commodity_color_map.get(c, default_color) for c in final_order]
                                        ),
                                        legend=None),
                        tooltip=['time_agg', 'ct_commodity', 'count']
                    )
                    
                    # Calculate totals for each time period
                    totals_data = chart_data_long.groupby('time_agg')['count'].sum().reset_index()
                    totals_data.columns = ['time_agg', 'total_count']
                    
                    # Text labels layer for totals
                    text_labels = alt.Chart(totals_data).mark_text(
                        align='center',
                        baseline='bottom',
                        dy=-5,  # Offset above the bar
                        fontSize=10,
                        fontWeight='bold'
                    ).encode(
                        x=alt.X('time_agg:T'),
                        y=alt.Y('total_count:Q'),
                        text=alt.Text('total_count:Q', format=',d'),
                        color=alt.value('var(--text-color)')  # Use CSS variable for theme adaptation
                    )
                    
                    # Combine layers
                    chart = (bars + text_labels).resolve_scale(
                        y='shared'
                    ).properties(
                        height=200
                    ).configure_view(
                        strokeWidth=0
                    ).configure_axis(
                        grid=False
                    )

                    st.altair_chart(chart, use_container_width=True)
        except Exception:
            # Don't crash the app if chart fails
            st.write("")

    # Add visual separator between summary/chart and search results
    if filtered:
        st.divider()

    # Display results
    for c in filtered[:100]:  # Limit to 100 results for performance
        # Get commodity icon
        commodity_icon = get_commodity_icon(c.get('ct_commodity'))
        
        # Condensed COLA header: COLA ID, Brand, Origin, Class Type, Date, and link in one line
        header_parts = [
            f"<b>{highlight_term(str(c.get('cola_id')), search_term)}</b>",
            f"{highlight_term(str(c.get('permit_num', 'N/A')), search_term)}"
        ]
        
        # Only add fanciful name if it exists and is not empty
        if c.get('fanciful_name') and c.get('fanciful_name').strip():
            header_parts.append(highlight_term(c.get('fanciful_name'), search_term))
        
        # Add brand name
        header_parts.append(highlight_term(c.get('brand_name', ''), search_term))
        
        # Add origin with flag icon
        origin = c.get('origin', '')
        ct_source = c.get('ct_source', '')
        flag_icon = get_flag_icon(origin, ct_source)
        if flag_icon:
            origin_display = f"{flag_icon} {highlight_term(origin, search_term)}"
        else:
            origin_display = highlight_term(origin, search_term)
        header_parts.append(origin_display)
        
        header_parts.extend([
            f"{commodity_icon} {highlight_term(c.get('class_type', ''), search_term)}",
            f"☑️ {c.get('completed_date').strftime('%m/%d/%Y') if c.get('completed_date') else 'N/A'}"
        ])
        
        # Add summary counts 
        summary_parts = []
        if c.get('cola_analysis_with_violations_count', 0) > 0:
            summary_parts.append(f"🤖 {c.get('cola_analysis_with_violations_count')}")
        # Add indicator for COLA-level analysis completion (only if no violations to avoid redundancy)
        elif c.get('cola_analysis_count', 0) > 0:
            summary_parts.append("🤖 0")
        else:
            summary_parts.append("⏳ Pending Review")
        
        if summary_parts:
            header_parts.append(' | '.join(summary_parts))
        
        # Add links to TTB detail and images pages using database view URLs with icons
        cola_id = str(c.get('cola_id'))
        links = []
        
        # Use URLs from database view with appropriate icons (no text labels)
        if c.get('cola_details_url'):
            links.append(f"<a href='{c['cola_details_url']}' target='_blank' style='color:{HIGHLIGHT_COLOR}; text-decoration:none;' title='Public COLA Registry Details'>ℹ️</a>")
        if c.get('cola_form_url'):
            links.append(f"<a href='{c['cola_form_url']}' target='_blank' style='color:{HIGHLIGHT_COLOR}; text-decoration:none;' title='Public COLA Registry Form'>📄</a>")
        if c.get('cola_internal_url'):
            links.append(f"<a href='{c['cola_internal_url']}' target='_blank' style='color:{HIGHLIGHT_COLOR}; text-decoration:none;' title='TTB Internal COLAs Online'>🔗</a>")
        
        if links:
            header_parts.append(' '.join(links))
        
        st.markdown('<span style="font-size:1.1em;line-height:1.1">' + ' | '.join(header_parts) + '</span>', unsafe_allow_html=True)
        
        # Show violations if present
        violations = c.get('violations', [])
        if violations:
            violation_lines = []
            for violation in violations:
                if violation.get('violation_comment'):
                    # Build prefix with available violation metadata
                    prefix_parts = []
                    if violation.get('cfr_ref'):
                        prefix_parts.append(f"CFR {violation.get('cfr_ref')}")
                    if violation.get('violation_type'):
                        prefix_parts.append(violation.get('violation_type'))
                    if violation.get('violation_group'):
                        prefix_parts.append(violation.get('violation_group'))
                    
                    # Create the violation text with prefix if available
                    if prefix_parts:
                        prefix = f"[{' | '.join(prefix_parts)}] "
                        violation_text = f"• {prefix}{highlight_term(violation.get('violation_comment'), search_term)}"
                    else:
                        violation_text = f"• {highlight_term(violation.get('violation_comment'), search_term)}"
                    
                    violation_lines.append(violation_text)
            
            if len(violations) > 5:
                violation_lines.append(f"... and {len(violations) - 5} more review warnings")
            
            if violation_lines:  # Only show if there are actual comments to display
                violations_html = "<br>".join(violation_lines)
                st.markdown(f"<div style='color:#d63384;font-size:0.85em;line-height:1.1;margin:0.2em 0;'><strong>Review Warnings:</strong><br>{violations_html}</div>", unsafe_allow_html=True)
        # Show images if present
        images = c.get('images', [])
        if images:
            for img_idx, img in enumerate(images):
                cols = st.columns([1, 2])
                with cols[0]:
                    public_url = img.get('public_url')

                    if public_url:
                        # Use public_url if available
                        try:
                            st.image(public_url, caption=None, use_container_width='always', output_format='auto')
                        except Exception:
                            st.write('(Image could not be loaded from URL)')
                            st.caption(public_url)
                    else:
                        st.write("(Image not available)")

                with cols[1]:
                    img_type = img.get('img_type', 'N/A')
                    if isinstance(img_type, str) and img_type.startswith('Label Image: '):
                        img_type = img_type[len('Label Image: '):]
                    details = [
                        f"<span style='font-weight:600;color:{IMAGE_INFO_HEADER_COLOR}'>File:</span> {highlight_term(str(img.get('file_name', 'N/A')), search_term)}",
                        f"<span style='font-weight:600;color:{IMAGE_INFO_HEADER_COLOR}'>Type:</span> {highlight_term(img_type, search_term)}",
                        f"<span style='font-weight:600;color:{IMAGE_INFO_HEADER_COLOR}'>Dim:</span> {highlight_term(str(img.get('dimensions_txt', 'N/A')), search_term)}"
                    ]
                    
                    # Use analysis_items from cola_images.image_analysis_items
                    analysis_items = img.get('analysis_items')
                    if analysis_items and analysis_items != '[]':
                        try:
                            if isinstance(analysis_items, str):
                                analysis_items = json.loads(analysis_items)
                            if analysis_items:  # Check if list is not empty
                                # Group by type
                                captions = [item for item in analysis_items if item.get('analysis_item_type') == 'dense_caption']
                                tags = [item for item in analysis_items if item.get('analysis_item_type') == 'tag']
                                objects = [item for item in analysis_items if item.get('analysis_item_type') == 'object']
                                text_blocks = [item for item in analysis_items if item.get('analysis_item_type') == 'text_block']
                                
                                if captions:
                                    caption_texts = [
                                        f"{highlight_term(cap.get('text', ''), search_term)} <span style='font-size:0.85em;color:#888'>({int(round(float(cap.get('model_confidence', 0))*100))}%)</span>" if cap.get('model_confidence') is not None else highlight_term(cap.get('text', ''), search_term)
                                        for cap in captions
                                    ]
                                    details.append(f"<span style='font-weight:600;color:{IMAGE_INFO_HEADER_COLOR}'>Captions:</span> {'; '.join(caption_texts)}")
                                
                                if tags:
                                    tag_texts = [
                                        f"{highlight_term(tag.get('text', ''), search_term)} <span style='font-size:0.85em;color:#888'>({int(round(float(tag.get('model_confidence', 0))*100))}%)</span>" if tag.get('model_confidence') is not None else highlight_term(tag.get('text', ''), search_term)
                                        for tag in tags
                                    ]
                                    details.append(f"<span style='font-weight:600;color:{IMAGE_INFO_HEADER_COLOR}'>Tags:</span> {'; '.join(tag_texts)}")
                                
                                if objects:
                                    obj_texts = [
                                        f"{highlight_term(obj.get('text', ''), search_term)} <span style='font-size:0.85em;color:#888'>({int(round(float(obj.get('model_confidence', 0))*100))}%)</span>" if obj.get('model_confidence') is not None else highlight_term(obj.get('text', ''), search_term)
                                        for obj in objects
                                    ]
                                    details.append(f"<span style='font-weight:600;color:{IMAGE_INFO_HEADER_COLOR}'>Objects:</span> {'; '.join(obj_texts)}")
                                
                                if text_blocks:
                                    tb_texts = [
                                        f"{highlight_term(tb.get('text', ''), search_term)} <span style='font-size:0.85em;color:#888'>({int(round(float(tb.get('model_confidence', 0))*100))}%)</span>" if tb.get('model_confidence') is not None else highlight_term(tb.get('text', ''), search_term)
                                        for tb in text_blocks
                                    ]
                                    details.append(f"<span style='font-weight:600;color:{IMAGE_INFO_HEADER_COLOR}'>Text Blocks:</span> {'; '.join(tb_texts)}")
                        except Exception as e:
                            details.append(f"<span style='color:#c00'>(Error parsing analysis_items: {e})</span>")
                    else:
                        details.append("<span style='color:#888'><i>No image analysis data found</i></span>")
                    
                    st.markdown('<div style="font-size:0.9em;line-height:1.1;margin:0.1em 0;">' + ' | '.join(details) + '</div>', unsafe_allow_html=True)
        # Remove the old version of TTB Details and TTB Images links at the end of each COLA record
        # Only keep the divider here
        st.divider()

if __name__ == '__main__':
    main()
