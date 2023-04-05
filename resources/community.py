from flask import request
from flask_restful import Resource
from mysql.connector.errors import Error
from mysql_connection import get_connection
from flask_jwt_extended import jwt_required,get_jwt_identity
from utils import check_password, hash_password
from datetime import datetime
import boto3
from config import Config

class community(Resource) :
    @jwt_required()
    def post(self) : 
#     { form-data
#     "title":"반갑습니다.",
#     "content":"안녕하세요",
#     "imgUrl":"asdasd"
#     }
        userId = get_jwt_identity()
        title = request.form.get("title")
        content = request.form.get("content")

        try :
            if 'photo' in request.files :
                file = request.files['photo']
                current_time = datetime.now()
                file_name=current_time.isoformat().replace(':','_')+'_'+str(userId)+'.jpg'
            
                try :
                    client = boto3.client(
                        's3', 
                            aws_access_key_id = Config.AWS_ACCESS_KEY_ID,
                            aws_secret_access_key = Config.AWS_SECERT_ACCESS_KEY)
                    client.upload_fileobj(file,Config.S3_BUCKET,file_name,ExtraArgs={'ACL':'public-read', 'ContentType':file.content_type } )
                    imgUrl = Config.S3_LOCATION+file_name
                except Exception as es :
                    print(str(es))
                    return { "s3 error":"파일 업로드 실패. 이미지를 확인해주세요."},400
                query = '''insert into community(userId,title,content,imgUrl)
                            values(%s,%s,%s,%s);'''
                record = (userId,title,content,imgUrl)
            else :
                query = '''insert into community(userId,title,content)
                            values(%s,%s,%s);'''
                record = (userId,title,content)
            connection = get_connection()
                
            cursor = connection.cursor()
            cursor.execute(query,record)
            connection.commit()
            lastrowId = cursor.lastrowid
            cursor.close()
            connection.close()

            connection = get_connection()
            query ='''select cm.*,u.nickname,u.userEmail,u.profileImgUrl 
                    from community cm join user u
                    on cm.userId = u.id
                    where cm.communityId = ''' + str(lastrowId) +''';'''
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query)

            communityList = cursor.fetchall()
            i = 0
            for row in communityList :
                communityList[i]['createdAt'] = row['createdAt'].isoformat()
                communityList[i]['updatedAt'] = row['updatedAt'].isoformat()
                i+=1
            cursor.close()
            connection.close()
        except Error as e :
            print(str(e))
            cursor.close()
            connection.close()
            return {"error",str(e)},400 
        
        return {"result":"success","communityList":communityList},200
    
    @jwt_required(optional=True)
    def get(self) :

        userId = get_jwt_identity()

        page = request.args.get('page')
        pageCount = int(page) * 10

        keyword = request.args.get('keyword')
        if  request.args.get('keyword') is None :
            return {'error':'키워드 를 설정해주세요.'},400

        try :
            connection = get_connection()
            
            if userId is None :
                if keyword is None :
                    query = '''select cm.*,u.nickname,u.userEmail,u.profileImgUrl 
                    from community cm join user u
                    on cm.userId = u.id
                    order by cm.createdAt desc 
                    limit ''' + str(pageCount) +''', 10 ; '''
                else :
                    query = '''select cm.*,u.nickname,u.userEmail,u.profileImgUrl 
                    from community cm join user u
                    on cm.userId = u.id
                    where cm.title like "%'''+str(keyword)+'''%" or cm.content like "%'''+str(keyword)+'''%"
                    order by cm.createdAt desc 
                    limit ''' + str(pageCount) +''', 10 ; '''

            else :
                if keyword is None :
                    query='''select cm.*,u.nickname,u.userEmail,u.profileImgUrl 
                            from community cm join user u
                            on cm.userId = u.id
                            where cm.userId = '''+str(userId)+'''
                            order by cm.createdAt desc 
                            limit ''' + str(pageCount) +''', 10 ; '''
                else :
                    query='''select cm.*,u.nickname,u.userEmail,u.profileImgUrl 
                            from community cm join user u
                            on cm.userId = u.id
                            where cm.userId = '''+str(userId)+''' and 
                            (cm.title like "%'''+str(keyword)+'''%" or cm.content like "%'''+str(keyword)+'''%")
                            order by cm.createdAt desc 
                            limit ''' + str(pageCount) +''', 10 ; '''
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query)
            communityList = cursor.fetchall()

            i = 0
            for row in communityList :
                communityList[i]['createdAt'] = row['createdAt'].isoformat()
                communityList[i]['updatedAt'] = row['updatedAt'].isoformat()
                i+=1
            
            cursor.close()
            connection.close()

        except Error as e :
            cursor.close()
            connection.close()
            print(str(e))
            return {'error':str(e)},400

        return {'result':'success',
                'communityList' : communityList},200


class communityUD(Resource) :
    @jwt_required()
    def put(self,communityId) :
        userId = get_jwt_identity()
        title = request.form.get('title')
        content = request.form.get('content')
        try :
            if 'photo' in request.files :
                file = request.files['photo']
                current_time = datetime.now()
                file_name=current_time.isoformat().replace(':','_')+'_'+str(userId)+'.jpg'
                
                try :
                    client = boto3.client(
                        's3', 
                            aws_access_key_id = Config.AWS_ACCESS_KEY_ID,
                            aws_secret_access_key = Config.AWS_SECERT_ACCESS_KEY)
                    client.upload_fileobj(file,Config.S3_BUCKET,file_name,ExtraArgs={'ACL':'public-read', 'ContentType':file.content_type } )
                    imgUrl = Config.S3_LOCATION+file_name
                except Exception as es :
                    print(str(es))
                    return { "s3 error":"파일 업로드 실패. 이미지를 확인해주세요."},400

                query = '''update community
                        set title = %s , content = %s, imgUrl = %s
                        where userId = %s and communityId = %s;'''
                record = (title,content,imgUrl,userId,communityId)

            else :
                query = '''update community
                        set title = %s , content = %s
                        where userId = %s and communityId = %s;'''
                record = (title,content,userId,communityId)

            connection = get_connection()

            cursor = connection.cursor()
            cursor.execute(query,record)

            connection.commit()
            
            cursor.close()
            connection.close()
            connection = get_connection()
            query ='''select cm.*,u.nickname,u.userEmail,u.profileImgUrl 
                    from community cm join user u
                    on cm.userId = u.id
                    where cm.communityId = ''' + str(communityId) +''';'''
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query)

            communityList = cursor.fetchall()
            i = 0
            for row in communityList :
                communityList[i]['createdAt'] = row['createdAt'].isoformat()
                communityList[i]['updatedAt'] = row['updatedAt'].isoformat()
                i+=1
            cursor.close()
            connection.close()
        except Error as e :
            print(str(e))
            cursor.close()
            connection.close()
            return {"error",str(e)},400 
        
        return {"result":"success","communityList":communityList},200

    @jwt_required()
    def delete(self,communityId) :
        userId = get_jwt_identity()

        try :
            connection = get_connection()

            query = '''select title from community 
                    where userId = %s and communityId = %s;'''
            record = (userId,communityId)

            cursor = connection.cursor(dictionary=True)

            cursor.execute(query,record)

            titleList = cursor.fetchall()
            
            title = str(titleList[0])
            file_name=title+'_'+str(userId)+'.jpg'
            
            
            client = boto3.client(
                        's3', 
                            aws_access_key_id = Config.AWS_ACCESS_KEY_ID,
                            aws_secret_access_key = Config.AWS_SECERT_ACCESS_KEY)
            client.delete_object(Bucket = Config.S3_BUCKET , Key= file_name )
            
            cursor.close()
            connection.close()

            connection = get_connection()

            query = '''delete from community
                    where communityId = %s and userId = %s;'''
            record = (communityId,userId)
            cursor = connection.cursor()
            cursor.execute(query,record)
            connection.commit()
            cursor.close()
            connection.close()
        except Error as e :
            print(str(e))
            cursor.close()
            connection.close()
            return {"error",str(e)},400
        except Exception as es:
                return {"s3 error",'이미지 파일 삭제 에러'}     
        
        return {"result":"success"},200


class communityLike(Resource) :
    @jwt_required()
    def post(self,communityId) :
        userId = get_jwt_identity()
        try:
            connection = get_connection()
            query = '''insert into communityLike(communityId,userId)
                    values(%s,%s);'''
            record = (communityId,userId)
            cursor = connection.cursor()
            cursor.execute(query,record)
            connection.commit()
            cursor.close()
            connection.close()
        except Error as e :
            print(str(e))
            cursor.close()
            connection.close()
            return {'error':str(e)},400
        
        return {'result':'success'},200
    
    @jwt_required()
    def delete(self,communityId) :
        userId = get_jwt_identity()

        try :
            connection = get_connection()
            query = '''delete from communityLike
                    where communityId= %s and userId = %s ; '''
            record = (communityId,userId)
            cursor = connection.cursor()
            cursor.execute(query,record)
            connection.commit()
            cursor.close()
            connection.close()
        except Error as e :
            print(str(e))
            cursor.close()
            connection.close()
            return {'error':str(e)},400
    
        return {'result':'success'},200


