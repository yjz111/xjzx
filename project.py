from flask_script import Manager
import config
import app

# 指定使用哪个配置，来创建flask对象
#flask_app=Flask()
flask_app = app.create(config.DevelopConfig)

# 添加扩展对象
manager = Manager(flask_app)

#添加管理员命令
from super_command import CreateSuperUserCommand,CreateTestUser,CreateTestLogin
manager.add_command('createuser',CreateSuperUserCommand())
manager.add_command('createtest',CreateTestUser())
manager.add_command('createlogin',CreateTestLogin())


#添加迁移命令
from models import db
from flask_migrate import Migrate,MigrateCommand
migrate=Migrate(flask_app,db)
manager.add_command('db',MigrateCommand)

if __name__ == '__main__':
    # print(flask_app.url_map)
    manager.run()
