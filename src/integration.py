from flask import Blueprint, jsonify, request
from database import get_connection
from auth import requer_auth

integration_bp = Blueprint("integration", __name__)
