from flask import Blueprint, session, make_response, request, jsonify, render_template, redirect, g,current_app
from utils.captcha.captcha import captcha
from utils.ytx_sdk import ytx_send
import random
from models import UserInfo, db, NewsCategory, NewsInfo
import functools
from utils import qiniu_upload
from datetime import datetime

user_blueprint = Blueprint('user', __name__, url_prefix='/user')


# url_for('user.image_code')
@user_blueprint.route('/image_code')
def image_code():
    # 生成图片验证码
    name, text, image = captcha.generate_captcha()
    # 构造响应对象
    response = make_response(image)
    # 设置返回数据的类型image/png
    response.mimetype = 'image/png'
    # 验证码的文本
    print(text)
    # 保存验证码文本
    session['image_code'] = text

    return response


@user_blueprint.route('/sms_code')
def sms_code():
    # 接收图片验证码，验证，通过后再发短信
    image_code_request = request.args.get('image_code')
    image_code_session = session.get('image_code')
    # 对比图形验证码
    if image_code_request != image_code_session:
        # 图形验证码错误则不进行短信发送
        return jsonify(result=1)

    # 手机号是用户填写的，需要获取
    mobile = request.args.get('mobile')

    # 生成随机的验证码
    code = random.randint(100000, 999999)

    # 保存，用于后续验证
    session['sms_code'] = code
    session['mobile'] = mobile
    print(code)

    # 调用云通讯的方法发送短信
    # ytx_send.sendTemplateSMS('手机号','信息[过期时间，验证码]','模板编号')
    # ytx_send.sendTemplateSMS(mobile, ['5', '%s' % code], 1)

    return jsonify(result=2)


@user_blueprint.route('/register', methods=['POST'])
def register():
    # 接收
    form = request.form
    mobile = form.get('mobile')  # '' None
    sms_code = form.get('sms_code')
    pwd = form.get('pwd')
    # 验证
    # 1.所有数据不为空
    if not all([mobile, sms_code, pwd]):  # 判断参数中是否有空值bool(x)
        return jsonify(result=1)  # 参数为空则返回1
    # 2.验证短信是否正确
    sms_code_session = str(session.get('sms_code'))
    if sms_code != sms_code_session:
        return jsonify(result=2)  # 短信验证码错误
    # 3.验证手机号是否存在
    mobile_exists = UserInfo.query.filter_by(mobile=mobile).count()
    if mobile_exists:
        return jsonify(result=3)  # 手机号存在
    # 4.验证当前手机号是否与接收短信的手机号一致
    mobile_session = session.get('mobile')
    if mobile != mobile_session:
        return jsonify(result=5)  # 两次手机号不一致

    # 处理：新建对象并保存
    user = UserInfo()
    user.nick_name = mobile
    user.mobile = mobile
    user.password = pwd
    # 添加
    db.session.add(user)
    # 保存到数据库
    db.session.commit()

    # 响应
    return jsonify(result=4)  # 注册成功


@user_blueprint.route('/login', methods=['POST'])
def login():
    # 接收
    mobile = request.form.get('mobile')
    pwd = request.form.get('pwd')
    # 验证
    if not all([mobile, pwd]):
        return jsonify(result=1)  # 数据不完整
    # 处理：判断手机号和密码是否正确
    # 1.根据手机号查询用户对象
    user = UserInfo.query.filter_by(mobile=mobile).first()
    if user:
        # 如果手机号存在则继续判断
        if user.check_pwd(pwd):
            # 密码正确，登录成功
            now=datetime.now()
            #修改用户的登录时间
            user.update_time=now
            db.session.commit()
            #统计登录数量08:15之前的，都算是08:15,19:15之后的，都算是19:15
            key=now.strftime('%Y-%m-%d')
            if now.hour<=7:
                current_app.redis_cli.hincrby(key,'08:00',1)
            elif now.hour>=19:
                current_app.redis_cli.hincrby(key,'19:00',1)
            else:
                current_app.redis_cli.hincrby(key,'%02d:00'%(now.hour+1),1)

            # 记录哪个用户登录成功
            session['user_id'] = user.id
            # 返回头像、昵称，用于展示
            return jsonify(result=3, nick_name=user.nick_name, avatar=user.avatar_url)
        else:
            # 密码错误
            return jsonify(result=4)
    else:
        # 如果用户不存在则说明手机号错误
        return jsonify(result=2)
        # 响应


@user_blueprint.route('/logout', methods=['POST'])
def logout():
    # 将session中的用户编号删除，则完成退出功能
    session.pop('user_id')
    return jsonify(result=1)


# 用户登录验证：装饰器
def required_login(view_fun):
    @functools.wraps(view_fun)
    def fun1(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/')
        # 每个视图，都需要使用user对象，则查询
        g.user = UserInfo.query.get(session.get('user_id'))
        # 视图函数会返回响应对象，此时，必须调用return，否则客户端无法接收响应
        return view_fun(*args, **kwargs)

    return fun1


@user_blueprint.route('/')  # /==>函数
@required_login
def index():
    # # 判断用户是否登录
    # if 'user_id' not in session:
    #     return redirect('/')
    # 获取当前登录的用户编号，根据编号查询用户对象的数据
    # user = UserInfo.query.get(session.get('user_id'))
    # 设置变量
    title = '用户中心'
    # 将用户对象传递到模板中，可以访问头像、昵称信息
    return render_template('news/user.html', title=title)


@user_blueprint.route('/base', methods=['GET', 'POST'])
@required_login
def base():
    # 查询用户对象
    # user = UserInfo.query.get(session['user_id'])
    user = g.user
    if request.method == 'GET':
        # GET请求展示页面
        return render_template('news/user_base_info.html', user=user)
    # POST请求用于修改数据
    signature = request.form.get('signature')
    nick_name = request.form.get('nick_name')
    gender = bool(int(request.form.get('gender')))  # '1' '0'
    # 修改对象的属性
    user.signature = signature
    user.nick_name = nick_name
    user.gender = gender
    # 保存到数据库
    db.session.commit()
    # 响应
    return jsonify(result=1)


@user_blueprint.route('/pic', methods=["GET", 'POST'])
@required_login
def pic():
    if request.method == 'GET':
        return render_template('news/user_pic_info.html')
    # post请求接收文件，保存到七牛，修改对象的属性
    avatar = request.files.get('avatar')
    # 验证
    if not avatar:
        # return '请选择要上传的头像'
        return jsonify(result=1)
    # 保存到七牛云
    avatar_name = qiniu_upload.upload(avatar)
    # 修改对象的头像属性
    user = g.user
    user.avatar = avatar_name
    db.session.commit()
    # 响应
    # return 'ok'
    # 需要返回头像的url值，用于显示
    return jsonify(result=2, avatar=user.avatar_url)


@user_blueprint.route('/follow')
@required_login
def follow():
    '''
    我的关注：当前用户关注的作者信息
    '''
    # user = UserInfo.query.get(session.get('user_id'))
    # 获取关注的作者
    author_list = g.user.authors
    # 参数：页码
    page = int(request.args.get('page', '1'))
    # 对数据进行分页
    pagination = author_list.paginate(page, 4, False)
    # 获取当前页的数据
    author_items = pagination.items
    # 获取总页数
    total_page = pagination.pages

    return render_template(
        'news/user_follow.html',
        author_items=author_items,
        total_page=total_page,
        page=page
    )


@user_blueprint.route('/pass', methods=["GET", "POST"])
@required_login
def pwd():
    if request.method == 'GET':
        return render_template('news/user_pass_info.html', msg='')
    # post请求接收数据，验证，保存
    pwd1 = request.form.get('pwd1')
    pwd2 = request.form.get('pwd2')
    pwd3 = request.form.get('pwd3')
    # 判断是否有空值
    if not all([pwd1, pwd2, pwd3]):
        return render_template('news/user_pass_info.html', msg='数据不能为空')
    # 判断密码长度
    if len(pwd1) < 6:
        return render_template('news/user_pass_info.html', msg='旧密码错误')
    if len(pwd2) < 6:
        return render_template('news/user_pass_info.html', msg='新密码不能少于6位')
    # 判断两个新密码是否相同
    if pwd2 != pwd3:
        return render_template('news/user_pass_info.html', msg='两个新密码不一致')
    # 旧密码是否确
    user = g.user
    if user.check_pwd(pwd1):
        user.password = pwd2
        db.session.commit()
        return render_template('news/user_pass_info.html', msg='修改成功')
    else:
        return render_template('news/user_pass_info.html', msg='旧密码错误')


@user_blueprint.route('/collection')
@required_login
def collection():
    # user=UserInfo.query.get(session.get('user_id'))
    # 获取此用户收藏的新闻
    news_list = g.user.news_collect
    # 参数：页码
    page = int(request.args.get('page', '1'))
    # 对数据进行分页
    pagination = news_list.paginate(page, 6, False)
    # 获取当前页的数据
    news_items = pagination.items
    # 获取总页数
    total_page = pagination.pages

    return render_template(
        'news/user_collection.html',
        news_items=news_items,
        total_page=total_page,
        page=page
    )


@user_blueprint.route('/release', methods=["GET", 'POST'])
@required_login
def release():
    if request.method == 'GET':
        category_list = NewsCategory.query.all()
        return render_template(
            'news/user_news_release.html',
            category_list=category_list
        )
    # 添加新闻数据
    title = request.form.get('title')
    category = request.form.get('category')
    summary = request.form.get('summary')
    content = request.form.get('content')
    # 接收图片
    pic = request.files.get('pic')
    # 验证
    if not all([title, category, summary, content, pic]):
        return '请填写完整数据'
    # 保存图片到七牛
    pic_name = qiniu_upload.upload(pic)
    # 保存数据
    news = NewsInfo()
    news.title = title
    news.category_id = int(category)
    news.summary = summary
    news.context = content
    news.pic = pic_name
    news.user_id = session.get('user_id')
    db.session.add(news)
    #修改作者的发布量
    # user=g.user
    # user.public_count+=1
    #提交到数据库
    db.session.commit()
    # 响应
    return redirect('/user/list')


@user_blueprint.route('/edit/<int:news_id>', methods=['GET', 'POST'])
@required_login
def edit(news_id):
    news = NewsInfo.query.get(news_id)
    if request.method == 'GET':
        category_list = NewsCategory.query.all()
        return render_template(
            'news/user_news_edit.html',
            category_list=category_list,
            news=news
        )
    # post请求进行修改
    title = request.form.get('title')
    category = request.form.get('category')
    summary = request.form.get('summary')
    content = request.form.get('content')
    # 接收图片
    pic = request.files.get('pic')
    # 验证
    if not all([title, category, summary, content]):
        return '请填写完整数据'
    # 保存图片到七牛
    if pic:
        pic_name = qiniu_upload.upload(pic)
        news.pic = pic_name
    # 保存数据
    news.title = title
    news.category_id = int(category)
    news.summary = summary
    news.context = content
    #修改状态为待审核
    news.status=1

    db.session.commit()
    # 响应
    return redirect('/user/list')


@user_blueprint.route('/list')
@required_login
def news_list():
    # 获取当前页的页码，默认为1
    page = int(request.args.get('page', 1))
    # 获取当前用户的所有新闻，并进行分页
    pagination = g.user.news.order_by(NewsInfo.id.desc()).paginate(page, 6, False)
    # 获取当前页的数据
    news_list1 = pagination.items
    # 获取总页数
    total_page = pagination.pages

    return render_template(
        'news/user_news_list.html',
        news_list1=news_list1,
        total_page=total_page,
        page=page
    )

#关注作者
@user_blueprint.route('/follow', methods=['POST'])
def follow_handle():
    user_id = session.get('user_id')
    user = UserInfo.query.get(user_id)

    dict1 = request.form
    follow_user_id = int(dict1.get('follow_user_id'))
    action = dict1.get('action')

    follow_user = UserInfo.query.get(follow_user_id)

    if action == '1':
        if follow_user not in user.follow_user:
            user.follow_user.append(follow_user)
        follow_user.follow_count += 1
    elif action == '2':
        if follow_user in user.follow_user:
            user.follow_user.remove(follow_user)
            follow_user.follow_count -= 1

    # db.session.add(user)
    db.session.commit()

    return jsonify(result=1)