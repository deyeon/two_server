import json
from flask import request
from flask_restful import Resource
from mysql.connector import Error
from flask_jwt_extended import create_access_token, get_jwt, jwt_required
from mysql_connection import get_connection
from email_validator import validate_email, EmailNotValidError
from utils import check_password, hash_password
from flask_jwt_extended import jwt_required,get_jwt_identity

import boto3
from config import Config

class UserRegisterResource(Resource) :
    def post(self) :
#         {
#           "nickname" : "성태",
#            "userEmail" : "abc123@naver.com",
#            "password" : "1234",
#            "gender" : "1",
#            "age" :"28"
#            "name":""
#            "questionNum":"1"
#            "questionAnswer":"인천"                
#           }
#        폼데이터 profileImg 있음

         # 1. 클라이언트가 보낸 데이터를 받아준다.
        data = request.form.get("data")
        print(data)
        data = json.loads(data)

        
        if 'profileImg' not in request.files :
            return {'error' : '사진이 없습니다.'},400

        file = request.files['profileImg']
        
        new_file_name = data['userEmail']+"_profileImg.jpg"
        file.filename = new_file_name
        
        # 2. 이메일 주소형식이 올바른지 확인한다. 
        try : 
            validate_email( data["userEmail"] )
        except EmailNotValidError as e :
            print(str(e))
            return {'error' : '이메일 형식을 확인하세요'} , 400
        
        # 3. 비밀번호의 길이가 유효한지 체크한다.
        # 만약, 비번이 4자리 이상, 12자리 이하다라면,

        if len( data['password'] ) < 4 or len( data['password'] ) > 12 :
            return {'error' : '비밀번호 길이 확인'} , 400
        
         # 4. 비밀번호를 암호화 한다.
        hashed_password = hash_password( data['password']  )

        # 5. DB 에 회원정보를 저장한다.
        
        
        profileImgUrl = Config.S3_LOCATION+new_file_name

        try:
            connection = get_connection()
            query = '''insert into user(nickname,userEmail,password,gender,age,profileImgUrl,name,questionNum,questionAnswer)
                        values(%s,%s,%s,%s,%s,%s,%s,%s,%s);'''
            record = ( data["nickname"], data["userEmail"],hashed_password ,
                      data["gender"],data["age"] , profileImgUrl , data["name"],data["questionNum"],data["questionAnswer"])
            cursor = connection.cursor()
            cursor.execute(query,record)
            connection.commit()

            userId = cursor.lastrowid

            cursor.close()
            connection.close()
            client = boto3.client(
                   's3', 
                    aws_access_key_id = Config.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key = Config.AWS_SECERT_ACCESS_KEY)
            try :
                client.upload_fileobj(file,Config.S3_BUCKET,new_file_name,ExtraArgs={'ACL':'public-read', 'ContentType':file.content_type } )
            except Exception as e :
                return {'error' : str(e) },500
        except Error as e :
            print(e)
            cursor.close()
            connection.close()
            return {'error' : str(e)}, 500
        
        access_token = create_access_token(userId)
        return {'result' : 'success', 'access_token' : access_token}, 200
    
class UserLoginResource(Resource) :
    def post(self) :
#         {
#     "userEmail":"abc@naver.com",
#     "password" : "1234"}

        data = request.get_json()
        print(data)
        
         # 2. DB 로부터 해당 유저의 데이터를 가져온다.
        try :
            #커넥션은 연결해주는거
            connection = get_connection()
            query ='''select* 
                    from user
                    where userEmail= %s;'''
            record = ( data['userEmail'] ,  )

            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)
            #바로 보여지는 에러 확인
            print('쿼리 실행 ' + query)
            print(record)
            #select를 사용할때는 fetchall을 사용한다
            result_list = cursor.fetchall()
            print(result_list)
           # 저장되것이 없으면 0이면 리턴이 클라이언트에 보여준다
            if len(result_list) == 0 :
                return {'error' : '회원가입한 사람 아닙니다.'}, 400
            # 수많은 리스트중 하나씩 가져와서 반복문 돌릴수없으니 index를 0으로하고 +1더하는 형식으로 코드를 완성합니다
            index = 0
            for colrow in result_list :
                result_list[index]['createdAt'] = colrow['createdAt'].isoformat()
                index = index + 1 

            print(result_list[0]['createdAt'])
            cursor.close()
            connection.close()
        except Error as e:
            print(e)
            cursor.close()
            connection.close()
            return {"error" : str(e)}, 500
         
         # 비밀번호가 일치하지 않을때 코드
        check = check_password( data['password'], result_list[0]['password'] )

        if check == False :
            return {"error" : "비밀번호가 일치하지 않습니다"} , 400

        access_token = create_access_token( result_list[0]['id'] )

        return {"result" : "success", "access_token" : access_token}, 200

jwt_blacklist = set()

class UserLogoutResource(Resource) :
    @jwt_required()
    def post(self) :
        
        jti = get_jwt()['jti']
        print(jti)

        jwt_blacklist.add(jti)

        return {'result' : 'success'}, 200
    
class UserIspassword(Resource):
    def post(self) :
        # {
        #     "userEmail" : "abc123@naver.com"
        #     "questionNum":"1",
        #     "questionAnswer":"인천"
        # }

        # 1. 클라이언트 로부터 데이터를 받아온다.
        data = request.get_json()

        # 2. 받아온 데이터를 통해 서버 쿼리문을 실행한다.
        try : 
            connection = get_connection()
            query = '''select *
                    from user
                    where userEmail = %s and questionNum= %s and questionAnswer = %s ;'''
            record = ( data["userEmail"] , data['questionNum'] , data['questionAnswer'] )

            cursor = connection.cursor(dictionary=True)

            cursor.execute(query,record)

            result_list = cursor.fetchall()

            if len(result_list) == 0 :
                return {"error" : "회원이 아닙니다."},400
            
            cursor.close()
            connection.close()

        except Error as e :
            cursor.close()
            connection.close()
            return{"error",str(e)},500

        return {"result":"success","userEmail":result_list[0]["userEmail"]},200

class UserIsId(Resource) :
    def post(self) :
#         {
#     "name":"정웅",
#     "questionNum"="1",
#     "questionAnswer":"인천"
# }
        data = request.get_json()

        try :
            connection = get_connection()

            query = '''select userEmail 
                    from user
                    where name = %s and questionNum= %s and questionAnswer = %s ;'''
            record = (data['name'] , data['questionNum'] , data['questionAnswer'])

            cursor = connection.cursor(dictionary=True)

            cursor.execute(query,record)

            user_list = cursor.fetchall()

            cursor.close()
            connection.close()


        except Error as e :
            cursor.close()
            connection.close()
            return{"error",str(e)},500
        
        return user_list[0],200

class UserIsEmail(Resource) :
    def post(self) :
        data = request.get_json()

        try : 
            validate_email( data["userEmail"] )
        except EmailNotValidError as e :
            
            return {'error' : '이메일 형식을 확인하세요'} , 400

        try :
            connection = get_connection()
            query = '''select userEmail from user where userEmail = %s ;'''
            record = (data['userEmail'],)
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query,record)
            email_list = cursor.fetchall()

            cursor.close()
            connection.close()
        except Error as e :
            cursor.close()
            connection.close()
            return{"error",str(e)},500
        
        if email_list == [] :
            return {"result": "아이디로 사용이 가능 합니다.","result_code":"1" },200
        else :
            return {"result": "아이디로 사용이 불가능 합니다.","result_code":"0" },200

class UserIsNickname(Resource) :
    def post(self) :
        data = request.get_json()

        try :
            connection = get_connection()
            query = '''select * from user where nickname = %s ;'''
            record = (data['nickname'],)
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query,record)
            nickname_list = cursor.fetchall()

            cursor.close()
            connection.close()
        except Error as e :
            cursor.close()
            connection.close()
            return{"error",str(e)},500
        
        if nickname_list == [] :
            return {"result": "닉네임으로 사용이 가능 합니다.","result_code":"1" },200
        else :
            return {"result": "닉네임으로 사용이 불가능 합니다.","result_code":"0" },200

class UserPasswordChanged(Resource):
    def put(self) :
        # { userEmail : abc@naver.com 
        #   password : 1234 }

        data = request.get_json()

        password = hash_password(data["password"])
        try :
            connection = get_connection()

            query = '''update user
                        set password = %s
                        where userEmail = %s;'''
            record = (password , data["userEmail"])

            cursor = connection.cursor()
            cursor.execute(query,record)

            connection.commit()

            cursor.close()
            connection.close()
        except Error as e :
            cursor.close()
            connection.close()

        return {"result":"success"},200

class UserContentLike(Resource):
    @jwt_required()
    def get(self) :
        userId = get_jwt_identity()
        page = request.args.get('page')
        pageCount = int(page) * 10
        print(page)
        try :
            connection = get_connection()

            query = '''select cl.contentId,cl.contentLikeUserId,c.title,c.genre,c.content,c.imgUrl,c.contentRating,c.createdYear,c.tmdbcontentId 
                        from contentLike cl join content c 
                        on cl.contentId = c.Id 
                        where cl.contentLikeUserId = %s 
                        limit ''' + str(pageCount) +''', 10 ; ''' 
            
            record = (userId,)

            cursor = connection.cursor(dictionary=True)

            cursor.execute(query,record)

            contentLike_list = cursor.fetchall()

            i = 0
            
            for row in contentLike_list :
                contentLike_list[i]['createdYear'] = row['createdYear'].isoformat()
                i = i + 1

            cursor.close()

            connection.close()

        except Error as e :
            print(str(e))

            cursor.close()

            connection.close()

            return {"fail":str(e)},500

        return {"contentLike_list" : contentLike_list ,
                "pageNum":page,
                'contentSize':str(len(contentLike_list))},200

class UserGenre(Resource) :
    @jwt_required()
    def post(self) :
        userId = get_jwt_identity()

        data = request.get_json()

        try :
            connection = get_connection()

            query = '''insert into userGenre(userId,tagId)
                        values(%s,%s);'''
            
            record = [ (userId , data['genre'][0]), 
                       (userId , data['genre'][1]),
                       (userId , data['genre'][2]) ]
            
            cursor = connection.cursor()

            cursor.executemany(query,record)

            connection.commit()

            cursor.close()

            connection.close()

        except Error as e :
            print(str(e))

            cursor.close()
            connection.close()

            return {'error':str(e)},500
        
        return {'result':'success'},200
    

class UserProfileChange(Resource) :
    @jwt_required()
    def put(self) :
        userId = get_jwt_identity()

        data = request.form.get("data")
        data = json.loads(data)

        hashed_password = hash_password( data['password']  )
        
        
        try :
            if 'profileImg' not in request.files :
                print('1')
                query = '''update user
                        set nickname=%s,password = %s
                        where id = %s ;'''
                record = (data['nickname'] , hashed_password , userId)
            else :
                file = request.files['profileImg']
                new_file_name = data['userEmail']+"_profileImg.jpg"
                file.filename = new_file_name
                
                client = boto3.client(
                    's3', 
                        aws_access_key_id = Config.AWS_ACCESS_KEY_ID,
                        aws_secret_access_key = Config.AWS_SECERT_ACCESS_KEY)
                try :
                    client.upload_fileobj(file,Config.S3_BUCKET,new_file_name,ExtraArgs={'ACL':'public-read', 'ContentType':file.content_type } )
                except Exception as e :
                    return {'error' : str(e) },500
            
                profileImgUrl = Config.S3_LOCATION+new_file_name

                query = '''update user
                        set nickname=%s,password = %s,profileImgUrl = %s
                        where id = %s ;'''
                record = (data['nickname'] , hashed_password ,profileImgUrl, userId)

         
            connection = get_connection()

            cursor = connection.cursor()
            
            cursor.execute(query,record)

            connection.commit()

            cursor.close()

            connection.close()

            jti = get_jwt()['jti']
            jwt_blacklist.add(jti)

        except Error as e :

            print(str(e))
            cursor.close()
            connection.close()

            return {'error':str(e)},500
        
        

        return {'result':'success','state':'logout'},200

    @jwt_required()
    def get(self) :
        userId = get_jwt_identity()
        try :
            connection = get_connection()

            query = '''select * from user
                        where id = %s ;'''
            record = (userId,)

            cursor = connection.cursor(dictionary=True)

            cursor.execute(query,record)

            user = cursor.fetchall()

            i = 0 
            for row in user :
                user[i]['createdAt'] = row['createdAt'].isoformat()
                i = i + 1
            cursor.close()

            connection.close()
           
        except Exception as e :
            print(str(e))
            cursor.close()
            connection.close()
            return {'error':str(e)},500
        
        return {'result':'success','user':user},200

    @jwt_required()
    def delete(self) :
        userId = get_jwt_identity()
         
        try :
            connection = get_connection()

            query = '''select userEmail from user
                        where id = %s ;'''
            record = (userId,)

            cursor = connection.cursor(dictionary=True)

            cursor.execute(query,record)

            email = cursor.fetchall()

            cursor.close()

            connection.close()
            print(email[0]['userEmail'])
            file_name = email[0]['userEmail'] + "_profileImg.jpg"

            client = boto3.client(
                    's3', 
                        aws_access_key_id = Config.AWS_ACCESS_KEY_ID,
                        aws_secret_access_key = Config.AWS_SECERT_ACCESS_KEY)
            
            client.delete_object(Bucket = Config.S3_BUCKET , Key= file_name )

            connection = get_connection()

            query = '''delete from user
                    where id = %s;'''
            record = (userId,)
            cursor = connection.cursor()
            cursor.execute(query,record)
            connection.commit()
            
            cursor.close()
            connection.close()


        except Exception as e :
            print(str(e))
            cursor.close()
            connection.close()
            return {'error':str(e)},500
        
        return {'result':'success'},200