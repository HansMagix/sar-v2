from app.db import get_programmes_db
import re

def get_filter_options():
    db = get_programmes_db()
    
    def fetch_col(col):
        # Fetch distinct non-empty values, exclude dirty data
        c = db.execute(f"SELECT DISTINCT {col} FROM programmes WHERE {col} IS NOT NULL AND {col} != '' AND {col} NOT IN ('#N/A', 'N/A') ORDER BY {col} ASC")
        return [r[0] for r in c.fetchall()]

    clusters = fetch_col('cluster')
    
    # Custom Sorter for Clusters (Integer Sort: "Cluster 2" < "Cluster 10")
    def cluster_sorter(val):
        try:
            # Extract first number found
            nums = re.findall(r'\d+', str(val))
            if nums:
                return int(nums[0])
            return 999
        except ValueError:
            return 999
            
    clusters.sort(key=cluster_sorter)

    return {
        'universities': fetch_col('institution'),
        'clusters': clusters,
        'courses': fetch_col('name')
    }

def search(course_name=None, institution=None, cluster=None, user_points=None, tier='basic', reach=False, cluster_map=None):
    # SECURITY RULE 1: The "Gatekeeper"
    has_course = bool(course_name and course_name != 'All')
    has_uni = bool(institution and institution != 'All' and len(institution) > 0)
    has_cluster = bool(cluster and cluster != 'All' and len(cluster) > 0)
    has_points = bool(user_points)

    if not has_course and not has_uni and not has_cluster and not has_points:
        return []

    db = get_programmes_db()
    
    # Base Query
    sql = "SELECT code, institution, name, cutoff_2024, cutoff_2023, cutoff_2022, cutoff_2021, cutoff_2020, cutoff_2019, cutoff_2018, cluster FROM programmes WHERE 1=1"
    params = []

    # Filtering
    if has_course:
        # Case-insensitive match, robust to spacing
        sql += " AND name LIKE ?"
        params.append(course_name)

    if has_uni:
        if isinstance(institution, list):
            placeholders = ','.join(['?'] * len(institution))
            sql += f" AND institution IN ({placeholders})"
            params.extend(institution)
        else:
            sql += " AND institution LIKE ?"
            params.append(institution)

    if has_cluster:
        if isinstance(cluster, list):
            placeholders = ','.join(['?'] * len(cluster))
            sql += f" AND cluster IN ({placeholders})"
            params.extend(cluster)
        else:
            sql += " AND cluster LIKE ?"
            params.append(cluster)

    # Points-Driven Discovery (Reach Logic) 
    # LEGACY MODE: If we only have global points, filter at SQL level for efficiency.
    # DYNAMIC MODE: If we have a cluster_map, we CANNOT filter effectively in SQL (would require complex ORs).
    # So we skip SQL filtering and let Python handle the "Safe/Risk" status.
    # Points-Driven Discovery (Reach Logic) 
    # LEGACY MODE: If we only have global points, filter at SQL level for efficiency.
    # DYNAMIC MODE: If we have a cluster_map, we CANNOT filter effectively in SQL (would require complex ORs).
    # So we skip SQL filtering and let Python handle the "Safe/Risk" status.
    # EXPLICIT MODE: If user searches for a specific course (has_course), DO NOT filter by points. Show it always.
    if user_points and not cluster_map and not has_course:
        try:
            pts = float(user_points)
            
            # Smart Ceiling (Reach)
            buffer_top = 2.0 if reach else 0.0
            ceiling = min(pts + buffer_top, 48.0)
            
            # Smart Floor (Relevance Window)
            # If > 40, show down to -10 (e.g. 44 -> 34)
            # Else, show down to -15 (e.g. 35 -> 20)
            buffer_bottom = 10.0 if pts > 40 else 15.0
            floor = max(pts - buffer_bottom, 0.0)
            
            sql += " AND (COALESCE(cutoff_2024, cutoff_2023, cutoff_2022, cutoff_2021, cutoff_2020, cutoff_2019, cutoff_2018, 0) BETWEEN ? AND ?)"
            params.extend([floor, ceiling])

        except ValueError:
            pass

    # Sorting
    sql += " ORDER BY COALESCE(cutoff_2024, cutoff_2023, cutoff_2022, cutoff_2021, cutoff_2020, cutoff_2019, cutoff_2018, 0) DESC"
    
    # Limit
    sql += " LIMIT 100"

    cursor = db.execute(sql, params)
    rows = cursor.fetchall()
    
    results = []
    for r in rows:
        item = dict(r)
        # Use latest available cutoff
        cutoff = item['cutoff_2024'] or item['cutoff_2023'] or item['cutoff_2022'] or item['cutoff_2021'] or item['cutoff_2020'] or item['cutoff_2019'] or item['cutoff_2018'] or 0.0
        course_cluster = item['cluster']
        
        # Determine Effective Points
        effective_points = user_points
        
        # Logic: If we have a map, try to find specific points.
        # Note: cluster_map keys come from frontend (TomSelect), values in DB 'course_cluster' match that format.
        if cluster_map and course_cluster and course_cluster in cluster_map:
            effective_points = cluster_map[course_cluster]

        if effective_points is not None and effective_points != '':
            try:
                pts = float(effective_points)
                
                # Dynamic Mode Filtering (Python Side)
                # If we are using a cluster map, we skipped the SQL filter. We must apply the Window here.
                if cluster_map:
                    buffer_top = 2.0 if reach else 0.0
                    ceiling = min(pts + buffer_top, 48.0)
                    buffer_bottom = 10.0 if pts > 40 else 15.0
                    floor = max(pts - buffer_bottom, 0.0)
                    
                    # Skip noise
                    if not (floor <= float(cutoff) <= ceiling):
                        continue

                if cutoff:
                    # Calculate Difference
                    diff = pts - cutoff
                    item['diff'] = round(diff, 3) 
                    
                    # Status Logic (All Users)
                    if pts >= cutoff:
                        item['status'] = 'Safe'
                    elif pts >= (cutoff - 2):
                            item['status'] = 'Tight' # Reach
                    else:
                            item['status'] = 'Risk'
                else:
                    item['status'] = 'Unknown'
            except ValueError:
                item['status'] = 'Unknown'
        else:
            item['status'] = 'Enter Points'

        # Force cutoff visibility
        item['cutoff'] = cutoff if cutoff > 0 else None
        
        # --- PREMIUM: Admissions Forecasting ---
        # --- FORECASTING: Available for All ---
        if True:
            # 1. Extract History (2018 -> 2024)
            # Create a list of tuples (Year, Cutoff) for available data
            raw_history = [
                (2018, item.get('cutoff_2018')),
                (2019, item.get('cutoff_2019')),
                (2020, item.get('cutoff_2020')),
                (2021, item.get('cutoff_2021')),
                (2022, item.get('cutoff_2022')),
                (2023, item.get('cutoff_2023')),
                (2024, item.get('cutoff_2024'))
            ]
            
            # Filter valid points
            valid_history = [val for year, val in raw_history if val and val > 0]
            item['history'] = valid_history # List of values e.g. [22.4, 23.5, ...]
            item['history_labels'] = [year for year, val in raw_history if val and val > 0]
            
            # 2. Trend Analysis
            trend = "Stable ⚖️"
            trend_color = "text-gray-500"
            
            if len(valid_history) >= 3:
                first = valid_history[0]
                last = valid_history[-1]
                
                diff = last - first
                
                if diff > 1.5:
                    trend = "Rising 🔥" # Harder
                    trend_color = "text-red-600"
                elif diff < -1.5:
                    trend = "Falling 📉" # Easier (Opp)
                    trend_color = "text-green-600"
                else:
                    # Check for volatility (Dip Detection)
                    # Simple check: max - min > 3 but start/end are close
                    if (max(valid_history) - min(valid_history)) > 3.0:
                         trend = "Volatile ⚡"
                         trend_color = "text-amber-600"
            
            item['trend'] = trend
            item['trend_color'] = trend_color
        # ---------------------------------------
            
        results.append(item)
        
    return results
