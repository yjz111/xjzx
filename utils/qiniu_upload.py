from qiniu import Auth, put_data


def upload(f1):
    # f1表示要上传的文件对象
    access_key = 'UwFIEPkb2s3q-W7Hx9AP6pL5CgEyhfqNBUz-wD28'
    secret_key = 'rPeJZlrHQkBjnrKGHDY4SHIcqGi6P_2re61N1iAM'
    # 空间名称
    bucket_name = 'yjz0'
    # 构建鉴权对象
    q = Auth(access_key, secret_key)
    # 生成上传 Token
    token = q.upload_token(bucket_name)
    # f1.read()读取文件内容
    # 上传文件数据，ret是字典，键为hash、key，值为新文件名，info是response对象
    ret, info = put_data(token, None, f1.read())
    # 文件保存在七牛后，会对这个文件进行重命名
    # 需要获取七牛中保存的文件名称
    return ret.get('key')
