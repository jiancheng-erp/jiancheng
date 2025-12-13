import json
from flask import Blueprint, jsonify, request

from wechat_api.send_message_api import (
    delete_template,
    list_templates,
    send_configurable_message,
    send_massage_to_users,
    upsert_template,
    _render,  # internal helper is reused for preview
)

wechat_template_bp = Blueprint("wechat_template_bp", __name__)


@wechat_template_bp.route("/wechat/templates", methods=["GET"])
def get_templates():
    return jsonify(list_templates())


@wechat_template_bp.route("/wechat/templates/<template_key>", methods=["GET"])
def get_template(template_key):
    templates = list_templates()
    if template_key not in templates:
        return jsonify({"error": "template not found"}), 404
    return jsonify(templates[template_key])


@wechat_template_bp.route("/wechat/templates/<template_key>", methods=["PUT"])
def update_template(template_key):
    data = request.get_json() or {}
    content = data.get("content")
    users = data.get("users")
    description = data.get("description", "")
    if not content or not users:
        return jsonify({"error": "content and users are required"}), 400
    template = upsert_template(template_key, content, users, description)
    return jsonify(template)


@wechat_template_bp.route("/wechat/templates/<template_key>", methods=["DELETE"])
def remove_template(template_key):
    deleted = delete_template(template_key)
    if not deleted:
        return jsonify({"error": "template not found"}), 404
    return jsonify({"msg": "deleted"})


@wechat_template_bp.route("/wechat/templates/<template_key>/render", methods=["POST"])
def render_template(template_key):
    data = request.get_json() or {}
    context = data.get("context", {})
    templates = list_templates()
    template = templates.get(template_key)
    if not template:
        return jsonify({"error": "template not found"}), 404
    rendered = _render(template.get("content", ""), context)
    return jsonify({"rendered": rendered})


@wechat_template_bp.route("/wechat/templates/<template_key>/send-test", methods=["POST"])
def send_test_message(template_key):
    data = request.get_json() or {}
    touser = data.get("touser")
    context = data.get("context", {})
    templates = list_templates()
    template = templates.get(template_key)
    if not template:
        return jsonify({"error": "template not found"}), 404
    rendered = _render(template.get("content", ""), context)
    if touser:
        result = send_massage_to_users(rendered, touser)
    else:
        result = send_configurable_message(
            template_key,
            default_content=template.get("content", ""),
            default_users=template.get("users", ""),
            context=context,
        )
    return jsonify(result)
