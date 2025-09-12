from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
import models
import app_setup

teams_bp = Blueprint("teams", __name__)

@teams_bp.route('/teams', methods=['GET', 'POST'])
@login_required
def teams():
    teams = models.Team.query.all()
    joined_team = None
    membership = models.TeamMembership.query.filter_by(user_id=current_user.id).first()
    if membership:
        joined_team = models.Team.query.get(membership.team_id)
    return render_template('teams.html', teams=teams, joined_team=joined_team)

@teams_bp.route('/teams/join', methods=['POST'])
@login_required
def join():
    team_id = request.form.get('team_id')
    
    if not team_id:
        flash('No team selected.', 'danger')
        return redirect(url_for('teams.teams'))
    
    # Check if the user is already a member of any team
    existing_membership = models.TeamMembership.query.filter_by(user_id=current_user.id).first()
    if existing_membership:
        flash('You are already a member of a team.', 'info')
        return redirect(url_for('teams.teams'))
    
    # Create a new membership
    membership = models.TeamMembership(user_id=current_user.id, team_id=team_id)
    app_setup.db.session.add(membership)
    app_setup.db.session.commit()
    flash('You have joined the team!', 'success')
    return redirect(url_for('teams.teams'))

@teams_bp.route('/teams/leave', methods=['POST'])
@login_required
def leave():
    team_id = request.form.get('team_id')
    
    if not team_id:
        flash('No team selected.', 'danger')
        return redirect(url_for('teams.teams'))
    
    # Find the existing membership for the user
    membership = models.TeamMembership.query.filter_by(user_id=current_user.id, team_id=team_id).first()
    
    if not membership:
        flash('You are not a member of this team.', 'danger')
        return redirect(url_for('teams.teams'))

    # Delete the membership
    app_setup.db.session.delete(membership)
    app_setup.db.session.commit()
    flash('You have left the team!', 'success')
    return redirect(url_for('teams.teams'))

@teams_bp.route('/teams/create', methods=['POST'])
@login_required
def create():
    name = request.form.get('name')
    
    if not name:
        flash('Team name required.', 'danger')
        return redirect(url_for('teams.teams'))
    
    # Check if the team already exists
    if models.Team.query.filter_by(name=name).first():
        flash('Team already exists.', 'warning')
        return redirect(url_for('teams.teams'))
    
    # Create the new team
    team = models.Team(name=name)
    app_setup.db.session.add(team)
    app_setup.db.session.commit()
    flash('Team created successfully!', 'success')
    return redirect(url_for('teams.teams'))
