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

def main():
    # Add logo at the top using st.logo()
    logo_path = os.path.join(os.path.dirname(__file__), 'resources/cola_search_logo.png')
    if os.path.exists(logo_path):
        st.logo(logo_path, size="large")
    st.title('TTB COLA Data Explorer')

    # Connect to MotherDuck database
    con = get_motherduck_connection()

    # Sidebar filters
    st.sidebar.header('Filters')
    search_term = st.sidebar.text_input('Search (ID, Brand, Analysis, etc.)')
    exclude_term = st.sidebar.text_input('Exclude phrase (optional)')
    has_analysis_only = st.sidebar.checkbox('Only COLAs with image analysis data', value=False)
    has_violations_only = st.sidebar.checkbox('Only COLAs with review warnings', value=False)

    # Date range filter for completed_date
    min_date = con.execute('SELECT MIN(completed_date) from cola_images.colas WHERE completed_date IS NOT NULL').fetchone()[0]
    max_date = con.execute('SELECT MAX(completed_date) from cola_images.colas WHERE completed_date IS NOT NULL').fetchone()[0]
    if min_date and max_date:
        min_date = min_date.strftime('%Y-%m-%d') if hasattr(min_date, 'strftime') else str(min_date)
        max_date = max_date.strftime('%Y-%m-%d') if hasattr(max_date, 'strftime') else str(max_date)
        
        # Default to one year before max date, but not earlier than min_date
        from datetime import datetime, timedelta
        max_date_obj = datetime.strptime(max_date, '%Y-%m-%d')
        min_date_obj = datetime.strptime(min_date, '%Y-%m-%d')
        default_start_obj = max_date_obj - timedelta(days=365)
        
        # Ensure default start is not before the minimum available date
        if default_start_obj < min_date_obj:
            default_start_obj = min_date_obj
            
        default_start = default_start_obj.strftime('%Y-%m-%d')
        
        date_range = st.sidebar.date_input('Completed Date Range', value=(default_start, max_date), min_value=min_date, max_value=max_date)
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
    
    selected_commodity_display = st.sidebar.multiselect('Commodity', commodity_display_options)
    selected_origin = st.sidebar.multiselect('Origin', origin_options)
    selected_class_type = st.sidebar.multiselect('Class Type', class_type_options)
    
    # Convert display selections back to actual values
    selected_commodity = [commodity_value_map[display] for display in selected_commodity_display]

    # Build optimized query based on filters
    # Start with base COLA query using vw_colas for better performance
    base_query = "SELECT * from cola_images.vw_colas c"
    where_clauses = []
    params = []
    
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
    if selected_start and selected_end:
        where_clauses.append('completed_date BETWEEN ? AND ?')
        params.extend([str(selected_start), str(selected_end)])
    
    # Image-related filters using pre-computed counts from cola_images.vw_colas
    if has_analysis_only:
        where_clauses.append('c.image_analysis_count > 0')
    if has_violations_only:
        where_clauses.append('c.cola_analysis_with_violations_count > 0')
    
    # Handle search terms efficiently
    if search_term or exclude_term:
        if search_term:
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
    
    # Fetch violations data separately if needed
    violations_data = {}
    if has_violations_only or search_term:
        if cola_ids:
            violations_query = """
                SELECT 
                    cola_id,
                    json_group_array(
                        json_object(
                            'violation_comment', violation_comment,
                            'violation_type', violation_type,
                            'violation_group', violation_group,
                            'violation_subgroup', violation_subgroup
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

    if len(filtered) > 100:
        st.write(f"Found {len(filtered):,} COLA records, limiting to 100 results displayed")
    else:
        st.write(f"Found {len(filtered):,} COLA records")
    
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
                    x_axis_title = 'Date'

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
                    chart = alt.Chart(chart_data_long).mark_bar(width={'band': 0.8}).encode(
                        x=alt.X('time_agg:T', title=x_axis_title, axis=alt.Axis(labelAngle=-45)),
                        y=alt.Y('count:Q', title='COLA Count'),
                        color=alt.Color('ct_commodity:N', 
                                        scale=alt.Scale(
                                            domain=final_order, 
                                            range=[commodity_color_map.get(c, default_color) for c in final_order]
                                        ),
                                        legend=None),
                        tooltip=['time_agg', 'ct_commodity', 'count']
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
        if c.get('downloaded_image_count', 0) > 0:
            summary_parts.append(f"📷 {c.get('downloaded_image_count')}")
        if c.get('cola_analysis_with_violations_count', 0) > 0:
            summary_parts.append(f"⚠️ {c.get('cola_analysis_with_violations_count')} review warnings")
        
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
            for violation in violations[:5]:  # Limit to first 5 violations
                violation_text = f"• **{violation.get('violation_type', 'Unknown')}** "
                if violation.get('violation_group'):
                    violation_text += f"({violation.get('violation_group')}) "
                if violation.get('violation_comment'):
                    violation_text += f": {highlight_term(violation.get('violation_comment'), search_term)}"
                violation_lines.append(violation_text)
            
            if len(violations) > 5:
                violation_lines.append(f"... and {len(violations) - 5} more review warnings")
            
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

    # Sidebar footer with logo and text
    st.sidebar.divider()
    # oa_logo_path = os.path.join(os.path.dirname(__file__), '../../resources/oa_wordmark1.png')
    # if os.path.exists(oa_logo_path):
    #     left_co, cent_co, last_co = st.columns(3, gap="large")
    #     with left_co:
    #         st.write('    ')
    #     with cent_co:
    #         st.sidebar.image(oa_logo_path, use_container_width=False, width=110)
    #     with last_co:
    #         st.write('    ')
    st.sidebar.markdown('<div style="font-size:0.95em; color:#444; text-align:center; margin-top:0.5em;">Prototype developed by the TTB Office of Analytics</div>', unsafe_allow_html=True)

if __name__ == '__main__':
    main()

# """
# Good examples:

# Bomb
# FD&C
# Pumpkin
# """