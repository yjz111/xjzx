from flask_script.commands import Command
from models import UserInfo, db
from datetime import datetime
import random
from flask import current_app

class CreateSuperUserCommand(Command):
    def run(self):
        # 接收用户输入的账号、密码
        username = input('请输入管理员账号：')
        pwd = input('请输入密码：')
        # 创建对象
        user = UserInfo()
        user.mobile = username
        user.nick_name = username
        user.password = pwd
        user.isAdmin = True
        # 保存
        db.session.add(user)
        db.session.commit()
        # 响应
        print('创建管理员成功')

class CreateTestUser(Command):
    def run(self):
        user_list=[]
        for i in range(100):
            user=UserInfo()
            user.nick_name='%s'%i
            user.mobile='%s'%i
            user.password='%s'%i
            user.create_time=datetime(2018,random.randint(1,7),random.randint(1,16))
            user_list.append(user)
        #提交到数据库
        db.session.add_all(user_list)
        db.session.commit()
        #提示
        print('创建用户成功')

class CreateTestLogin(Command):
    def run(self):
        #将数据保存在Redis中
        #统计时间为：00:00---08:15-->19:15--23:59
        for i in range(8,20):
            current_app.redis_cli.hset('2018-07-16','%02d:00'%i,random.randint(100,999))
        print('登录数据完成')
