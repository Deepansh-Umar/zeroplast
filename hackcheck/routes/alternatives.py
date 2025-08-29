
from flask import Blueprint, render_template, request
from flask_login import login_required
from utils import alternative_for

alts_bp = Blueprint("alternatives", __name__)

@alts_bp.route('/alternatives', methods=['GET'])
@login_required
def show_alternatives():
    item_key = (request.args.get('item_key') or '').strip().lower()
    alternatives = None
    if item_key:
        alternatives = alternative_for(item_key)
    return render_template('alternatives.html', item_key=item_key, alternatives=alternatives)
