import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FileField
from wtforms.validators import DataRequired
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'static/videos'
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'webm', 'ogg'}
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///videos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), unique=True, nullable=False)
    title = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<Video {self.title}>'


# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


class RenameForm(FlaskForm):
    new_title = StringField('新标题', validators=[DataRequired()])
    submit = SubmitField('保存')


class SearchForm(FlaskForm):
    query = StringField('搜索视频')
    submit = SubmitField('搜索')


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']



@app.route('/', methods=['GET', 'POST'])
def index():
    search_form = SearchForm()
    if search_form.validate_on_submit():
        query = search_form.query.data.lower()
        videos = Video.query.filter(Video.title.ilike(f'%{query}%')).all()
    else:
        videos = Video.query.all()

    return render_template('index.html', videos=videos, search_form=search_form)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # 检查是否有文件被上传
        if 'file' not in request.files:
            flash('没有选择文件', 'error')
            return redirect(request.url)
        file = request.files['file']
        # 如果用户没有选择文件，浏览器可能会提交一个空文件
        if file.filename == '':
            flash('没有选择文件', 'error')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            # 使用文件名（不带扩展名）作为初始标题
            title = os.path.splitext(filename)[0]
            # 保存到数据库
            video = Video(filename=filename, title=title)
            db.session.add(video)
            db.session.commit()
            flash('视频上传成功!', 'success')
            return redirect(url_for('index'))
        else:
            flash('不允许的文件类型', 'error')
    return render_template('upload.html')


@app.route('/delete/<int:video_id>', methods=['POST'])
def delete(video_id):
    video = Video.query.get_or_404(video_id)

    # 删除文件
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], video.filename)
    if os.path.exists(filepath):
        os.remove(filepath)

    # 删除数据库记录
    db.session.delete(video)
    db.session.commit()

    flash('视频删除成功!', 'success')
    return redirect(url_for('index'))


@app.route('/rename/<int:video_id>', methods=['GET', 'POST'])
def rename(video_id):
    video = Video.query.get_or_404(video_id)
    form = RenameForm()

    if form.validate_on_submit():
        video.title = form.new_title.data
        db.session.commit()
        flash('视频标题更新成功!', 'success')
        return redirect(url_for('index'))

    # 预填充当前标题
    form.new_title.data = video.title

    return render_template('rename.html', form=form, video=video)


@app.route('/play/<int:video_id>')
def play(video_id):
    video = Video.query.get_or_404(video_id)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], video.filename)

    if not os.path.exists(filepath):
        flash('视频文件不存在!', 'error')
        return redirect(url_for('index'))

    return render_template('play.html',
                           video_title=video.title,
                           video_url=url_for('static', filename=f'videos/{video.filename}'))

# 在文件末尾添加
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)