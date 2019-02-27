from flask import Blueprint, render_template, session, g, request, jsonify, current_app
from models import NewsCategory, NewsInfo, UserInfo, db, NewsComment

news_blueprint = Blueprint('news', __name__)


@news_blueprint.route('/')
def index():
    # 分类信息
    category_list = NewsCategory.query.all()

    # 点击量排行
    click_list = NewsInfo.query.order_by(NewsInfo.click_count.desc())[0:6]

    # 用户登录状态
    if 'user_id' in session:
        g.user = UserInfo.query.get(session.get('user_id'))
    else:
        g.user = None

    return render_template(
        'news/index.html',
        category_list=category_list,
        click_list=click_list,
        # user=user
    )


@news_blueprint.route('/list/<int:category_id>')
def news_list(category_id):
    '''返回json格式的新闻数据'''
    # 接收新闻分类的编号category_id
    # 查询指定分类的所有新闻数据
    list1 = NewsInfo.query  # select * from newsinfo
    if category_id > 0:
        # 如果选择的是“最新”==0，表示所有分类的新闻
        list1 = list1.filter_by(category_id=category_id) # where ....
    # 排序：最新的显示在最前面
    list1 = list1.order_by(NewsInfo.id.desc())  # order by ....
    # 分页
    page = int(request.args.get('page', '1'))
    pagination = list1.paginate(page, 4, False)
    # 获取当前页的数据
    list2 = pagination.items  # [NewsInfo,....]
    # 获取总页数
    total_page = pagination.pages

    # 将python对象转换成js对象{id:1,....}
    list3 = []
    for news in list2:
        list3.append({
            'id': news.id,
            'pic_url': news.pic_url,
            'title': news.title,
            'summary': news.summary,
            'create_time': news.create_time.strftime('%Y-%m-%d'),  # 将日期转成字符串，并指定格式
            'avatar_url': news.user.avatar_url,
            'nick_name': news.user.nick_name,
        })

    return jsonify(list3=list3, total_page=total_page)


# 浏览器会自动请求一个地址，名称为'/favicon.ico'
# @news_blueprint.route('/favicon.ico')
# def ico():
#     # 到静态文件夹static中查找指定的静态文件
#     return news_blueprint.send_static_file('news/images/logo.png')


# 设计详细页路由地址为：/新闻的编号
@news_blueprint.route('/<int:news_id>')
def detail(news_id):
    # 根据编号查询新闻
    news = NewsInfo.query.get(news_id)
    # 将点击量+1
    news.click_count += 1
    db.session.commit()
    # 查询用户登录状态
    if 'user_id' in session:
        g.user = UserInfo.query.get(session.get('user_id'))
    else:
        g.user = None
    # 查询点击量排行
    click_list = NewsInfo.query.order_by(NewsInfo.click_count.desc())[0:6]

    # 响应
    return render_template(
        'news/detail.html',
        news=news,
        click_list=click_list,
        title='文章详情页'
    )


@news_blueprint.route('/comment_add', methods=['POST'])
def comment_add():
    # 接收
    msg = request.form.get('msg')
    news_id = request.form.get('news_id')
    # 如果进行评论则无此值，如果进行回复则有此值
    comment_id = request.form.get('comment_id', '0')
    # 验证
    # 判断用户是否登录
    if 'user_id' not in session:
        return jsonify(result=1)
    if not all([msg, news_id]):
        return jsonify(result=2)
    try:
        news_id = int(news_id)
    except:
        return jsonify(result=3)
    # 处理
    comment = NewsComment()
    comment.msg = msg
    comment.news_id = news_id
    comment.user_id = session.get('user_id')
    if comment_id != '0':
        # 回复，需要设置评论的编号
        comment.comment_id = int(comment_id)
    db.session.add(comment)
    # 让新闻的评论量+1
    news = NewsInfo.query.get(news_id)
    news.comment_count += 1
    try:
        db.session.commit()
    except Exception as e:
        # 写日志
        current_app.logger_xjzx.error('添加评论连接数据库出错')
        return jsonify(result=5)
    # 响应
    return jsonify(result=4)


@news_blueprint.route('/comment_list/<int:news_id>')
def comment_list(news_id):
    # 查询指定新闻的评论
    clist = NewsComment.query \
        .filter_by(news_id=news_id, comment_id=None) \
        .order_by(NewsComment.id.desc())
    # 将评论对象转成json对象
    clist2 = []
    count = 0
    for comment in clist:
        count += 1
        #点赞
        like=0
        # 获取评论的所有回复
        reply_list = []
        # user=UserInfo.query.get(comment.user_id)
        for reply in comment.comments:
            reply_list.append({
                'id': reply.id,
                'msg': reply.msg,
                'nick_name': reply.user.nick_name
            })
        # 构造评论对象
        clist2.append({
            'id': comment.id,
            'msg': comment.msg,
            'like_count': comment.like_count,
            'avatar_url': comment.user.avatar_url,
            'nick_name': comment.user.nick_name,
            'create_time': comment.create_time.strftime('%Y-%m-%d %H:%M:%S'),
            # 评论的所有回复
            'reply_list': reply_list,
            #当前登录的用户是否点赞
            'like':like
        })

    return jsonify(clist=clist2, count=count)


@news_blueprint.route('/collect', methods=['GET','POST'])
def collect():
    # 接收
    if request.method=='GET':
        news_id=request.args.get('news_id')
    else:
        news_id = request.form.get('news_id')
    flag = request.form.get('flag','1')
    # 验证
    # 必须传新闻编号
    if not news_id:
        return jsonify(result=1)
    # 用户必须登录
    if 'user_id' not in session:
        return jsonify(result=2)
    user_id = session.get('user_id')
    user = UserInfo.query.get(user_id)
    # 判断新闻编号是否对应着一条新闻数据
    news = NewsInfo.query.get(news_id)
    if not news:
        return jsonify(result=3)
    # 处理
    if request.method=='GET':
        #如果是GET请求，表示查询用户是否收藏了指定的新闻
        if news in user.news_collect:
            return jsonify(result=4)
        else:
            return jsonify(result=5)
    #如果是post请求，则进行收藏操作或取消收藏操作
    # 用户user_id收藏新闻news_id
    # 需要将数据添加到tb_news_collect表中
    # 关系属性news_collect，类型为列表，值为[NewsInfo,NewsInfo,....]
    # 如果flag=1表示收藏，flag=2表示取消收藏
    if flag == '1':
        # 如果新闻已经被用户收藏，则不再添加收藏
        if news not in user.news_collect:
            user.news_collect.append(news)
        else:
            return jsonify(result=5)
    else:
        # 取消收藏，从列表中删除数据
        if news in user.news_collect:
            user.news_collect.remove(news)
        else:
            return jsonify(result=5)
    # 提交
    db.session.commit()
    # 响应
    return jsonify(result=4)
#
#评论点赞
@news_blueprint.route('/comment_up', methods=['POST'])
def comment_up():
    dict1 = request.form

    comment_id = dict1.get('comment_id')
    up = dict1.get('up')
    comment_info = NewsComment.query.get(comment_id)

    if up == '1':
        comment_info.like_count += 1
    else:
        comment_info.like_count -= 1

    db.session.commit()

    return jsonify(result=1, count=comment_info.like_count)