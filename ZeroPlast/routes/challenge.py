
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
import models
import app_setup

challenge_bp = Blueprint("challenge", __name__)

@challenge_bp.route('/challenges')
def challenges_page():
    challenges = models.Challenge.query.order_by(models.Challenge.start_date.desc()).all()
    return render_template('challenges.html', challenges=challenges)

@challenge_bp.route('/challenge/<int:challenge_id>', methods=['GET', 'POST'])
@login_required
def challenge_detail(challenge_id):
    challenge = models.Challenge.query.get_or_404(challenge_id)
    # Check if user has joined
    joined = models.ChallengeParticipation.query.filter_by(challenge_id=challenge.id, user_id=current_user.id).first() is not None
    # User leaderboard: sum of points for users in this challenge
    user_participants = models.ChallengeParticipation.query.filter_by(challenge_id=challenge.id).all()
    user_leaderboard = []
    for part in user_participants:
        points = sum(p.delta for p in models.PointsLog.query.filter_by(user_id=part.user_id).all())
        user_leaderboard.append({'user': models.User.query.get(part.user_id), 'points': points})
    user_leaderboard.sort(key=lambda x: x['points'], reverse=True)
    # Team leaderboard: sum of points for teams in this challenge
    team_points = {}
    for part in user_participants:
        memberships = models.TeamMembership.query.filter_by(user_id=part.user_id).all()
        for m in memberships:
            team_points.setdefault(m.team_id, 0)
            team_points[m.team_id] += sum(p.delta for p in models.PointsLog.query.filter_by(user_id=part.user_id).all())
    team_leaderboard = []
    for team_id, points in team_points.items():
        team = models.Team.query.get(team_id)
        if team:
            team_leaderboard.append({'team': team, 'points': points})
    team_leaderboard.sort(key=lambda x: x['points'], reverse=True)
    return render_template('challenge.html', challenge=challenge, joined=joined, user_leaderboard=user_leaderboard, team_leaderboard=team_leaderboard)

@challenge_bp.route('/challenge/<int:challenge_id>/join', methods=['POST'])
@login_required
def join(challenge_id):
    challenge = models.Challenge.query.get_or_404(challenge_id)
    already = models.ChallengeParticipation.query.filter_by(challenge_id=challenge.id, user_id=current_user.id).first()
    if already:
        flash('Already joined this challenge!', 'info')
        return redirect(url_for('challenge.challenge_detail', challenge_id=challenge.id))
    part = models.ChallengeParticipation(challenge_id=challenge.id, user_id=current_user.id)
    app_setup.db.session.add(part)
    app_setup.db.session.commit()
    flash('You have joined the challenge!', 'success')
    return redirect(url_for('challenge.challenge_detail', challenge_id=challenge.id))
