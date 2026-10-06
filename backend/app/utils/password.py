import bcrypt
def hash_password(password: str) -> str:
    # 1. 把明文密码变成字节串
    # 2. bcrypt.gensalt() 生成随机盐（也是字节串）
    # 3. hashpw 生成加密后的字节串，最后用 .decode("utf-8") 变成普通字符串存数据库
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
def verify_password(password: str, hashed_password: str) -> bool:
    # 直接把 明文密码 和 数据库里的乱码 一起扔进去比对
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
