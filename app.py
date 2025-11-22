import os
from flask import Flask, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import date
from diff_match_patch import diff_match_patch

# --- 1. 初始化应用和数据库 ---
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'laws.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_AS_ASCII'] = False

db = SQLAlchemy(app)


# --- 2. 数据库模型定义 ---
# 用于存储法律、版本和具体条文的结构
class Law(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    short_name = db.Column(db.String(50), unique=True, nullable=False)
    full_name_de = db.Column(db.String(255), nullable=False)
    full_name_zh = db.Column(db.String(255))

class LawVersion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    law_id = db.Column(db.Integer, db.ForeignKey('law.id'), nullable=False)
    version_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(512))
    law = db.relationship('Law', backref=db.backref('versions', lazy=True, order_by='LawVersion.version_date.desc()'))

class Paragraph(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    version_id = db.Column(db.Integer, db.ForeignKey('law_version.id'), nullable=False)
    paragraph_number = db.Column(db.String(20), nullable=False)
    content_de = db.Column(db.Text, nullable=False)
    content_zh = db.Column(db.Text)
    version = db.relationship('LawVersion', backref=db.backref('paragraphs', lazy=True))


# --- 3. 核心功能：差异对比 (Synopse) ---
def generate_synopsis_html(old_text, new_text):
    dmp = diff_match_patch()
    diffs = dmp.diff_main(old_text, new_text)
    dmp.diff_cleanupSemantic(diffs)

    old_html = ""
    new_html = ""
    for op, data in diffs:
        safe_data = data.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
        if op == dmp.DIFF_DELETE:
            old_html += f'<span class="diff-deleted">{safe_data}</span>'
        elif op == dmp.DIFF_INSERT:
            new_html += f'<span class="diff-inserted">{safe_data}</span>'
        elif op == dmp.DIFF_EQUAL:
            old_html += safe_data
            new_html += safe_data
            
    return {"old_version_html": old_html, "new_version_html": new_html}


# --- 4. API 接口 (数据接口) ---
@app.route('/api/synopsis/<law_short_name>/<v1_date_str>/<v2_date_str>/<path:paragraph_num>')
def get_synopsis_api(law_short_name, v1_date_str, v2_date_str, paragraph_num):
    paragraph_num_decoded = paragraph_num.replace('%20', ' ')
    try:
        v1_date = date.fromisoformat(v1_date_str)
        v2_date = date.fromisoformat(v2_date_str)
    except ValueError:
        return jsonify({"error": "日期格式无效，请使用 YYYY-MM-DD 格式。"}), 400

    p1 = db.session.query(Paragraph).join(LawVersion).join(Law).filter(Law.short_name == law_short_name, LawVersion.version_date == v1_date, Paragraph.paragraph_number == paragraph_num_decoded).first()
    p2 = db.session.query(Paragraph).join(LawVersion).join(Law).filter(Law.short_name == law_short_name, LawVersion.version_date == v2_date, Paragraph.paragraph_number == paragraph_num_decoded).first()

    if not p1 or not p2:
        return jsonify({"error": "未找到指定的法律条文版本。"}), 404

    # 同时生成德语和中文的差异对比
    synopsis_data_de = generate_synopsis_html(p1.content_de, p2.content_de)
    synopsis_data_zh = generate_synopsis_html(p1.content_zh or "", p2.content_zh or "") # 使用 or "" 避免内容为 None
    
    return jsonify({
        "law": law_short_name,
        "paragraph": paragraph_num_decoded,
        "version_1": {
            "date": v1_date.isoformat(), 
            "content_html_de": synopsis_data_de["old_version_html"],
            "content_html_zh": synopsis_data_zh["old_version_html"]
        },
        "version_2": {
            "date": v2_date.isoformat(), 
            "content_html_de": synopsis_data_de["new_version_html"],
            "content_html_zh": synopsis_data_zh["new_version_html"]
        }
    })

@app.route('/api/laws')
def get_laws():
    """获取所有法律的列表。"""
    laws = Law.query.all()
    return jsonify([{"short_name": law.short_name, "full_name_de": law.full_name_de} for law in laws])

@app.route('/api/law/<law_short_name>/details')
def get_law_details(law_short_name):
    """获取特定法律的所有版本和唯一的法条编号。"""
    law = Law.query.filter_by(short_name=law_short_name).first_or_404()
    
    # 获取所有版本
    versions = [{"date": v.version_date.isoformat(), "description": v.description} for v in law.versions]
    
    # 获取所有唯一的法条编号
    paragraphs = db.session.query(Paragraph.paragraph_number).distinct().join(LawVersion).filter(LawVersion.law_id == law.id).order_by(Paragraph.paragraph_number).all()
    paragraph_numbers = [p[0] for p in paragraphs]
    
    return jsonify({
        "versions": versions,
        "paragraph_numbers": paragraph_numbers
    })


# --- 5. 前端页面渲染 ---
@app.route('/')
def index():
    """渲染主前端页面。"""
    # Flask 会自动在 'templates' 文件夹中寻找 'index.html'
    return render_template('index.html')


if __name__ == '__main__':
    # 在第一次运行时，需要先运行 manage_data.py 来创建数据库
    if not os.path.exists(os.path.join(basedir, 'laws.db')):
        print("数据库 'laws.db' 不存在。请先运行 'python manage_data.py' 来创建和填充数据。")
    else:
        app.run(debug=True)
