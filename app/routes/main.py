from flask import Blueprint, render_template, request, g, jsonify, flash, Response
from app.services.search_service import search, get_filter_options
from app.services.auth_service import get_session
import datetime
import csv
import io

bp = Blueprint('main', __name__)

def get_current_tier():
    # Free Pivot: All users are premium now.
    return 'premium'

@bp.route('/', methods=['GET'])
def index():
    # Optimization: Serve skeleton page. filters loaded via AJAX.
    tier = get_current_tier()
    return render_template('index.html', tier=tier)

@bp.route('/search', methods=['GET'])
def search_route():
    course = request.args.get('course')
    # Use getlist for Multi-Select arguments
    # Note: AJAX might send them as repeated keys 'uni=A&uni=B' OR backend needs to split comma-separated if JS sends that.
    # We will assume getlist works for repeated keys, and we can also check for comma-split fallback if needed.
    institution = request.args.getlist('uni')
    cluster = request.args.getlist('cluster')
    points = request.args.get('points')
    reach = request.args.get('reach') == 'true'
    
    # Note: We rely on standard URL parameter handling (key=val&key=val2) for lists.
    # We are removing the .split(',') logic because our values (Clusters/Unis) CONTAIN commas,
    # so simple splitting is destructive.

    
    # Security Rule 1 Check (Frontend feedback)
    security_warning = False
    if not course and not institution and not cluster and not points:
        security_warning = True
    
    # Parse Cluster Map (JSON)
    cluster_map_json = request.args.get('cluster_map')
    cluster_map = {}
    if cluster_map_json:
        try:
            import json
            cluster_map = json.loads(cluster_map_json)
        except:
            pass # Fail silently, use defaults

    # Determine Tier
    tier = get_current_tier()
    
    # Perform Search
    # The service will return [] if security warning is true, effectively doing the same check
    results = search(
        course_name=course if course else None,
        institution=institution if institution else None,
        cluster=cluster if cluster else None,
        user_points=points,
        tier=tier,
        reach=reach,
        cluster_map=cluster_map
    )
    
    
    # AJAX Response
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('results_partial.html', results=results, tier=tier, security_warning=security_warning, user_points=points)
    
    # Full Page Fallback
    # Optimization: Don't load full options into HTML. Let JS fetch them.
    # We still pass empty lists or basic structure if needed, but for now we'll pass empty to prevent loop rendering.
    # Actually, we need to Change the Index Route to NOT pass heavy data.
    return render_template(
        'index.html', 
        results=results, 
        tier=tier,
        security_warning=security_warning
    )

@bp.route('/api/filters', methods=['GET'])
def api_filters():
    # Cache friendly endpoint for filter options
    options = get_filter_options()
    return jsonify(options)

@bp.route('/export', methods=['GET'])
def export_results():
    # Extract Args (Same as search)
    course = request.args.get('course')
    institution = request.args.getlist('uni')
    cluster = request.args.getlist('cluster')
    points = request.args.get('points')
    reach = request.args.get('reach') == 'true'
    
    # Handle JS "comma-separated" behavior
    if len(institution) == 1 and ',' in institution[0]:
        institution = institution[0].split(',')
    if len(cluster) == 1 and ',' in cluster[0]:
        cluster = cluster[0].split(',')

    # Check Tier (Implicitly handled by search_service returning hidden data for basic, 
    # but we can block export entirely for Basic if desired. 
    # Prompt said: "Alert: This is a Premium Feature." so backend should probably enforce it too.)
    user_tier = 'basic'
    if g.user and g.user['tier'] == 'premium':
        user_tier = 'premium' 
        
    # DEV OVERRIDE: Allow Basic Users to Export
    # if user_tier != 'premium':
    #     return Response("Premium Feature Only", status=403)

    # Fetch Results
    # Reuse Search Service (it now exposes full data)
    results = search(course, institution, cluster, points, tier='premium', reach=reach)

    # Generate CSV
    def generate():
        data = io.StringIO()
        w = csv.writer(data)
        
        # Header
        w.writerow(('Programme', 'Institution', 'Code', 'Cutoff'))
        yield data.getvalue()
        data.seek(0)
        data.truncate(0)

        for r in results:
            w.writerow((
                r['name'],
                r['institution'],
                r['code'],
                r['cutoff']
            ))
            yield data.getvalue()
            data.seek(0)
            data.truncate(0)

    # Streaming Response
    response = Response(generate(), mimetype='text/csv')
    response.headers.set("Content-Disposition", "attachment", filename="sar_shortlist.csv")
    return response
