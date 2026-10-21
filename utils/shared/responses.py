from flask import jsonify


def error(message, status=400):
    return jsonify({"error": message}), status


def success(message, status=200, **payload):
    return jsonify({"message": message, **payload}), status
